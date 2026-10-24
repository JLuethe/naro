#!/usr/bin/env python3
"""Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.
Compare nanoharness result trees. See 16-test-plan.md for the contract.
"""
import argparse
import base64
import copy
import ctypes
import json
import os
from pathlib import Path
import re
import sys

COMMIT = '6ed285c3ec7a1d228def4d4e7021c6ba269f620c'
DYNAMIC = re.compile(r'nano\.\d+\.save(?=\W|$)|nano\.[A-Za-z0-9]{6}(?=\W|$)')
LIBC = ctypes.CDLL(None)
LIBC.setlocale(0, b'C.UTF-8')
LIBC.wcwidth.argtypes = [ctypes.c_wchar]


def norm_text(text, root=None):
    if root:
        text = text.replace(root, '<FX>')
        # Numbered backup names contain the absolute path with ! separators.
        text = text.replace(root.replace('/', '!'), '<FX!>')
    def replace(m):
        return 'nano.<PID>.save' if m.group().endswith('.save') else 'nano.XXXXXX'
    text = DYNAMIC.sub(replace, text)
    return re.sub(r"(Pane is dead \((?:status|signal) [^,]+), [^\n)]*\)", r"\1, <TIME>)", text)


def fixture_root(run):
    # HOME may be deliberately overridden by a scenario. cwd is authoritative.
    cwd = run.get('cwd', '')
    marker = '/fx'
    i = cwd.rfind(marker)
    return cwd[:i + len(marker)] if i >= 0 else None


def norm_lock(raw):
    """Mask only variable identity fields in a recognizable nano lock."""
    if len(raw) != 1024 or raw[:2] != b'b0':
        return raw
    raw = bytearray(raw)
    for a, b in ((24, 28), (28, 44), (68, 100)):
        raw[a:b] = b'\0' * (b - a)
    return bytes(raw)


def norm_row(row, width, root=None):
    # attrs are CELL offsets, while text is Unicode with no wide placeholders.
    attrs = [{} for _ in range(width)]
    for run in row['attrs']:
        value = dict(part.split('=', 1) for part in run['attr'].split(',') if '=' in part)
        for col in range(max(0, run['start']), min(width, run['end'])):
            attrs[col] = value.copy()
    glyphs, col = [], 0
    for ch in row['text']:
        w = max(0, LIBC.wcwidth(ch))
        if not w and glyphs:
            glyphs[-1][0] += ch
            continue
        w = max(1, w)
        a = attrs[col] if col < width else {}
        if ch == ' ':
            # Reverse swaps the foreground into the visible background.
            a = {k: v for k, v in a.items() if k in ('bg', 'reverse', 'underline', 'strike', 'hidden')
                 or k == 'fg' and 'reverse' in a}
        glyphs.append([ch, w, tuple(sorted(a.items()))])
        col += w
    # Normalize volatile text without conflating codepoint and cell indexes.
    text = ''.join(g[0] for g in glyphs)
    return norm_text(text, root), [(g[1], g[2]) for g in glyphs]


def norm_screen(screen, root=None, dead=False):
    if screen is None:
        return None
    cursor = dict(screen['cursor'])
    if dead:
        cursor.pop('visible', None)
    # Grid width comes from mode-independent geometry, not Python len(text).
    width = screen.get('width') or max((sum(max(0, LIBC.wcwidth(c)) for c in r['text'])
                                           for r in screen['rows']), default=0)
    rows = [norm_row(r, width, root) for r in screen['rows']]
    if dead:
        rows = [(re.sub(r'^(Pane is dead \((?:status|signal) [0-9]+), .*$', r'\1, <TIME>', t), a) for t, a in rows]
    return {'rows': rows,
            'cursor': cursor, 'modes': screen.get('modes', {})}


def norm_manifest(fixture, root=None, include_nlink=True, run=None):
    out = {}
    for path, entry in fixture.items():
        name = norm_text(path, root)
        if name in out:
            raise ValueError('normalization collides at ' + name)
        item = {k: entry.get(k) for k in ('type', 'mode', 'nlink') if k in entry}
        if not include_nlink:
            item.pop('nlink', None)
        if entry['type'] == 'file':
            if 'b64' in entry:
                raw = base64.b64decode(entry['b64'], validate=True)
                if os.path.basename(path).startswith('.') and path.endswith('.swp'):
                    raw = norm_lock(raw)
                # Only these fixture-owned tool argument logs contain mkstemps output.
                aux = {'TEST-FEAT-005': 'home/spell-args', 'TEST-FEAT-007': 'home/fmt-args'}
                if run and aux.get(run.get('scenario')) == path:
                    tempdir = (run.get('env') or {}).get('TMPDIR') or '/tmp'
                    value = raw.decode('utf-8', 'surrogateescape')
                    value = re.sub(re.escape(tempdir.rstrip('/')) + r'/nano\.[A-Za-z0-9]{6}(?=\W|$)', '<TMP>/nano.XXXXXX', value)
                    raw = value.encode('utf-8', 'surrogateescape')
                # Ordinary file bytes are exact: never mask text that resembles a temp name.
                # Paths in history/tool log files are normalized only when the scenario opts in.
                item['data'] = raw.hex()
            else:
                item.update(size=entry['size'], sha256=entry['sha256'])
        elif entry['type'] == 'link':
            item['target'] = norm_text(entry['target'], root)
        out[name] = item
    # Compare hardlink relationships, not process-specific inode numbers.
    groups = {}
    for path, entry in fixture.items():
        if entry['type'] == 'file':
            groups.setdefault(entry.get('ino', path), []).append(norm_text(path, root))
    links = sorted(sorted(g) for g in groups.values() if len(g) > 1)
    return {'entries': out, 'hardlinks': links}


def norm_captured(captured):
    out = {}
    for path, values in captured.items():
        converted = []
        for value in values:
            if value.startswith('ERROR: '):
                converted.append(norm_text(value))
            else:
                raw = base64.b64decode(value, validate=True)
                if os.path.basename(path).startswith('.') and path.endswith('.swp'):
                    raw = norm_lock(raw)
                converted.append(raw.hex())
        out[norm_text(path)] = converted
    return out


def compare(ref, cand, files_only=False):
    diffs = []
    def check(name, a, b):
        if a != b:
            diffs.append({'field': name, 'reference': a, 'candidate': b})
    if ref.get('reference_commit') != COMMIT:
        diffs.append({'field': 'reference_commit', 'reference': COMMIT, 'candidate': ref.get('reference_commit')})
    check('scenario', ref['scenario'], cand['scenario'])
    for k in ('exit_status', 'exit_signal'):
        check(k, ref.get(k), cand.get(k))
    roots = fixture_root(ref), fixture_root(cand)
    for k in ('fixture', 'initial_fixture'):
        if k == 'initial_fixture' and k not in ref:
            continue  # Early reference schema did not record initial metadata.
        rf, cf = ref.get(k, {}), cand.get(k, {})
        links = all('nlink' in e for e in rf.values())
        check(k, norm_manifest(rf, roots[0], links, ref), norm_manifest(cf, roots[1], links, cand))
    check('captured_files', norm_captured(ref.get('captured_files', {})), norm_captured(cand.get('captured_files', {})))
    if files_only:
        return diffs
    for k in ('stderr', 'stdout'):
        check(k, norm_text(ref.get(k) or '', roots[0]), norm_text(cand.get(k) or '', roots[1]))
    # Compare exact input order/bytes but not elapsed timestamps or executable paths.
    check('inputs', [i['hex'] for i in ref['inputs']], [i['hex'] for i in cand['inputs']])
    for name in sorted(set(ref['snapshots']) | set(cand['snapshots'])):
        a, b = ref['snapshots'].get(name), cand['snapshots'].get(name)
        if a is None or b is None:
            check('snapshot.' + name, a, b)
            continue
        a, b = norm_screen(a, roots[0]), norm_screen(b, roots[1])
        for k in ('cursor', 'modes'):
            check('snapshot.%s.%s' % (name, k), a[k], b[k])
        check('snapshot.%s.height' % name, len(a['rows']), len(b['rows']))
        for n, (ar, br) in enumerate(zip(a['rows'], b['rows'])):
            check('snapshot.%s.row%d.text' % (name, n), ar[0], br[0])
            check('snapshot.%s.row%d.attributes' % (name, n), ar[1], br[1])
    check('after_exit_screen', norm_screen(ref.get('after_exit_screen'), roots[0], True),
          norm_screen(cand.get('after_exit_screen'), roots[1], True))
    check('trace_final_modes', ref.get('trace_final_modes'), cand.get('trace_final_modes'))
    # Timeouts invalidate a comparison even if both happen to time out.
    for side, run in (('reference', ref), ('candidate', cand)):
        if run.get('steps_ok') is False:
            diffs.append({'field': side + '.failed_steps', 'reference': True, 'candidate': False})
        for note in run.get('notes', []):
            if 'timed out' in note:
                diffs.append({'field': side + '.timeout', 'reference': None, 'candidate': note})
    return diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('reference', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--json', type=Path, help='write full machine-readable differences')
    ap.add_argument('--files-only', action='store_true', help='diagnostic subset; does not establish conformance')
    args = ap.parse_args()
    refids = {p.name for p in args.reference.glob('TEST-*') if p.is_dir()}
    candids = {p.name for p in args.candidate.glob('TEST-*') if p.is_dir()}
    ids = sorted(set(args.ids) if args.ids else refids | candids)
    if not ids:
        ap.error('no tests selected')
    report = {}
    for tid in ids:
        try:
            with (args.reference / tid / 'result.json').open() as f:
                ref = json.load(f)
            with (args.candidate / tid / 'result.json').open() as f:
                cand = json.load(f)
            diffs = compare(ref, cand, args.files_only)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            diffs = [{'field': 'invalid or missing evidence', 'reference': None, 'candidate': str(exc)}]
        report[tid] = diffs
        print(tid, 'DIFF' if diffs else 'MATCH')
        for d in diffs[:12]:
            detail = repr(d['reference']) + ' != ' + repr(d['candidate'])
            print('   ', d['field'] + ':', detail[:260])
    bad = sum(bool(v) for v in report.values())
    print('%d compared, %d differ%s' % (len(report), bad, ' (files-only subset)' if args.files_only else ''))
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=True, indent=2) + '\n')
    return int(bool(bad))


if __name__ == '__main__':
    sys.exit(main())
