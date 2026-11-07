"""Reference-derived Q-IDENTITY-001 classification; raw compare stays strict."""
import copy
import hashlib
import gettext
import json
import re
import tomllib
from compare_runs import compare, fixture_root
from candidate_expectations import ROOT, POLICY, candidate_title, expected_cli_output, case_sha256, display_width, display_slice, display_pad, title_row, DEFAULT_STATES

WELCOME = 'Welcome to nano.  For basic help, type Ctrl+G.'
HELP_TITLE = 'Main nano help text'


def policy_identity():
    names = ['spec/tools/identity_review.py', 'spec/tools/candidate_expectations.py',
             'tests/naro/identity-overrides.json', 'tests/naro/legacy-deviations.json', 'tests/naro/identity-title-contexts.json', 'docs/NARO_IDENTITY_POLICY.md']
    payload = b''.join(n.encode() + bytes([0]) + (ROOT / n).read_bytes() + bytes([0]) for n in names)
    return {'id': POLICY, 'schema': 'naro-identity-review-v1',
            'version': tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version'],
            'sha256': hashlib.sha256(payload).hexdigest()}


def _message_row(width, message):
    message = message[:width]
    start = (width - len(message)) // 2
    if start > 1:
        return (' ' * (start - 2) + '[ ' + message + ' ]').ljust(width)[:width]
    return (' ' * start + message).ljust(width)[:width]


def _help_caption(width, caption):
    if len(caption) + 5 > width:
        raise ValueError('unreviewed clipped help caption')
    return (' ' * (3 + (width - 5 - len(caption)) // 2) + caption).ljust(width)


def _context_geometry(rows,width,context,app_width=None):
    """Bound contexts authorize one physical grid and one effective app width."""
    if (type(width)is not int or width!=context['width']
        or len(rows)!=context['height'] or not rows
        or display_width(rows[0])!=width
        or (app_width is not None and (type(app_width)is not int or app_width!=context['width']))):
        raise ValueError('reviewed title context geometry changed')


def project_identity_rows(reference_rows, width, *, allow_help=False, status_rows=(),
                          reference_root=None, candidate_root=None, language='C', stateflags=False, title_context=None):
    """Return (expected rows,evidence), using only reference text and frozen context."""
    expected, evidence = list(reference_rows), []
    if title_context is not None:
        _context_geometry(reference_rows,width,title_context)
    if not reference_rows or width < 1:
        return expected, evidence
    if display_width(reference_rows[0]) != width:
        if 'GNU nano' in reference_rows[0]:raise ValueError('unreviewed identity title width')
        return expected,evidence
    version = policy_identity()['version']
    def change(index, text, kind):
        if text != reference_rows[index]:
            expected[index] = text
            evidence.append({'row': index, 'kind': kind, 'reference': reference_rows[index], 'expected': text})
    first = reference_rows[0]
    if first.startswith('  GNU nano') and not first.startswith('  GNU nano '):
        raise ValueError('unsupported identity title')
    if title_context is not None:
        fields={k:title_context[k]for k in ('filename','state')}
        if display_pad(title_row(width,label='GNU nano 9.3',**fields),width)!=first:
            raise ValueError('unbranded reference title failed independent oracle')
        change(0,display_pad(title_row(width,label='NARO '+version,**fields),width),'editing-title')
    elif first.startswith('  GNU nano '):
        if not first.startswith('  GNU nano 9.3'):
            raise ValueError('unsupported reference title version')
        if language.lower().startswith('de_de.iso') and first[-3:] == ' t ':
            # ISO-8859-1 terminal trace leaves the final translated-state cell.
            # Preserve that cell; independently validate all clean-title cells.
            clean=first[:-2]+'  '
            new=_reference_title(clean,width,version,language)[:-2]+'t '
        else:
            new = _stateflags_title(first, width, version) if stateflags else _reference_title(first,width,version,language)
        change(0, new, 'editing-title')
    if allow_help:
        heading, title, pairs = _help_rows(width, language)
        if first == _help_caption(width, heading):
            change(0, _help_caption(width, title), 'main-help-title')
            for index, row in enumerate(reference_rows[1:], 1):
                if row in pairs:
                    change(index, pairs[row], 'main-help-intro')
    for index in status_rows:
        if 0 <= index < len(reference_rows) and reference_rows[index] == _message_row(width, WELCOME):
            change(index, _message_row(width, WELCOME.replace('nano', 'NARO', 1)), 'welcome-status')
    return expected, evidence


def _help_snapshots(case):
    active, result = False, {}
    for step in (case or {}).get('steps', []):
        for key in step.get('keys', []):
            if key in ('^G', 'F1') or (key == '^H' and '--modernbindings' in (case or {}).get('args', [])):
                active = True
            elif active and key == '^X':
                active = False
        if step.get('text') == 'g' and any(x.get('hex') == '1b' for x in (case or {}).get('steps', [])):
            active=True
        if 'snapshot' in step:
            result[step['snapshot']] = active
    return result


def _status_rows(run, height):
    args = run.get('argv', [])[1:]
    nohelp = '--nohelp' in args or '-x' in args
    zero = '--zero' in args or '-0' in args
    mini = '--minibar' in args or '-_' in args
    minimum = 3 if zero else 4 if mini else 5
    return (height - (1 if nohelp or height < minimum else 3),)


def _attrs(row, width):
    values = [{} for _ in range(width)]
    for item in row.get('attrs', []):
        attr = dict(part.split('=', 1) for part in item['attr'].split(',') if '=' in part)
        for index in range(max(0, item['start']), min(width, item['end'])):
            values[index] = attr
    return values


def project_screen(reference, *, allow_help=False, status_rows=(), reference_root=None, candidate_root=None,
                   app_width=None, language='C', stateflags=False, boldtext=False, title_context=None):
    projected = copy.deepcopy(reference)
    rows = reference.get('rows', [])
    width = reference.get('width') or (display_width(rows[0]['text']) if rows else 0)
    if title_context is not None and 'width'in reference:width=reference['width']
    app_width = width if app_width is None else app_width
    if title_context is not None:
        _context_geometry([row['text']for row in rows],width,title_context,app_width)
        height=reference.get('height',len(rows))
        if type(height)is not int or height!=title_context['height']:
            raise ValueError('reviewed title context physical height changed')
    if app_width < 1 or app_width > width:
        raise ValueError('unsupported application width')
    texts, evidence = project_identity_rows([display_slice(row['text'],0,app_width) for row in rows], app_width,
        allow_help=allow_help, status_rows=status_rows, reference_root=reference_root,
        candidate_root=candidate_root, language=language, stateflags=stateflags, title_context=title_context)
    for change in evidence:
        index = change['row']
        projected['rows'][index]['text'] = texts[index] + display_slice(rows[index]['text'],app_width)
        if boldtext and index == 0:
            old_end = display_width(rows[index]['text'].rstrip())
            attrs = [{'start': 0, 'end': old_end, 'attr': 'bold=True'}]
            if rows[index].get('attrs') == attrs:
                projected['rows'][index]['attrs'] = [{'start': 0, 'end': display_width(projected['rows'][index]['text'].rstrip()), 'attr': 'bold=True'}]
    return projected, evidence


def classify(reference, candidate, case_id=None, case=None):
    """Recompute raw and projected comparisons, ignoring all saved verdicts."""
    tid = case_id or reference.get('scenario')
    raw = compare(reference, candidate)
    projected, evidence, attr_errors = copy.deepcopy(reference), [], []
    projection_errors = []
    args = reference.get('argv', [])[1:]
    env = reference.get('env', {})
    help_modes = _help_snapshots(case)
    for name, screen in reference.get('snapshots', {}).items():
        height = int(env.get('LINES', len(screen.get('rows', []))))
        try:
            expected, changes = project_screen(screen, allow_help=help_modes.get(name, False),
                status_rows=_status_rows(reference, height),
                app_width=int(env['COLUMNS']) if 'COLUMNS' in env else None,
                language=env.get('LANGUAGE') or env.get('LC_ALL') or env.get('LANG', 'C'),
                stateflags='-%' in args or '--stateflags' in args,
                boldtext='-D' in args or '--boldtext' in args,
                title_context=_title_context(case,name),
                reference_root=fixture_root(reference), candidate_root=fixture_root(candidate))
        except ValueError as exc:
            projection_errors.append({'field': f'snapshot.{name}.identity_projection', 'reference': str(exc), 'candidate': 'unreviewed'})
            continue
        projected['snapshots'][name] = expected
        for change in changes:
            evidence.append({'snapshot': name, **change})
            actual = candidate.get('snapshots', {}).get(name)
            width = screen.get('width') or display_width(screen['rows'][change['row']]['text'])
            if not actual or len(actual.get('rows', [])) <= change['row']:
                continue
            if _attrs(expected['rows'][change['row']], width) != _attrs(actual['rows'][change['row']], width):
                attr_errors.append({'field': f'snapshot.{name}.row{change["row"]}.raw_attributes',
                                    'reference': 'original identity-row attributes', 'candidate': 'changed'})
    args = reference.get('argv', [])[1:]
    if any(x in ('--help', '-h', '--version', '-V') for x in args):
        profile = 'tiny' if (case or {}).get('profile') == 'tiny' else 'default'
        try:
            stdout = expected_cli_output(reference.get('stdout', ''), profile)
            if stdout != reference.get('stdout', ''):
                projected['stdout'] = stdout
                evidence.append({'field': 'stdout', 'kind': 'cli-identity'})
        except ValueError as exc:
            projection_errors.append({'field':'stdout.identity_projection','reference':str(exc),'candidate':'unreviewed'})
    if tid and tid.startswith('TEST-NEXT-RECOVER-002-'):
        old = reference.get('stderr', '')
        if old.startswith('Sorry! Nano crashed!'):
            projected['stderr'] = old.replace('Sorry! Nano crashed!', 'Sorry! NARO crashed!', 1)
            evidence.append({'field': 'stderr', 'kind': 'panic-identity'})
    if tid == 'TEST-KEY-004':
        known = "No key is bound to function 'Exit' in menu 'main'.  Exiting.\n\nIf needed, use nano with the -I option to adjust your nanorc settings.\n"
        if reference.get('stderr') == known:
            projected['stderr'] = known.replace('use nano with', 'use naro with', 1)
            evidence.append({'field': 'stderr', 'kind': 'unbound-key-identity'})
    if tid in ('TEST-FEAT-016', 'TEST-SIG-007'):
        screen = reference.get('after_exit_screen') or {}
        rows = screen.get('rows', [])
        if len(rows) > 1:
            width = screen.get('width') or len(rows[1]['text'])
            known = 'Use "fg" to return to nano.'
            if rows[1]['text'] == known.ljust(width):
                projected['after_exit_screen']['rows'][1]['text'] = known.replace('nano', 'NARO').ljust(width)
                evidence.append({'field': 'after_exit_screen.row1.text', 'kind': 'suspend-identity'})
    reference_inputs=[x.get('hex') for x in reference.get('inputs',[])]
    candidate_inputs=[x.get('hex') for x in candidate.get('inputs',[])]
    if reference_inputs!=candidate_inputs:
        projection_errors.append({'field':'inputs.hex','reference':reference_inputs,'candidate':candidate_inputs})
    residual = compare(projected, candidate) + attr_errors + projection_errors
    issue = legacy_deviation(tid, reference, candidate, residual) if residual else None
    issue = issue or _corpus_deviation(tid, reference, candidate, residual)
    accepted = not residual or bool(issue)
    reviewed = accepted and bool(evidence)
    kind = 'unexpected' if not accepted else 'declared_deviation' if issue else 'identity_reviewed' if reviewed else 'raw_exact'
    return {'raw_exact': not raw, 'identity_reviewed': reviewed and not issue,
            'declared_deviation': bool(issue), 'deviation_id': issue, 'accepted': accepted,
            'classification': kind, 'differences': raw, 'identity_fields': evidence,
            'unexpected_differences': [] if accepted else residual,
            'identity_policy': POLICY, 'policy_sha256': policy_identity()['sha256']}


def _corpus_deviation(tid, reference, candidate, residual):
    return legacy_deviation(tid,reference,candidate,residual)


def summary_counts(results):
    values = list(results.values())
    return {'recorded': len(values), 'raw_matches': sum(v['raw_exact'] for v in values),
            'identity_reviewed': sum(v['identity_reviewed'] for v in values),
            'declared_deviations': sum(v['declared_deviation'] for v in values),
            'unexpected': sum(not v['accepted'] for v in values),
            'accepted': sum(v['accepted'] for v in values)}


def legacy_deviation(tid, reference, candidate, differences):
    """Accept only the complete residual recorded in the reviewed old baseline."""
    policy=json.loads((ROOT/'tests/naro/legacy-deviations.json').read_text())
    entry=policy['cases'].get(tid)
    if not entry or not differences:return None
    if tid == 'TEST-ROOT-HOME-002-NO-HOME-TILDE':
        ns=reference.get('root_namespace')or{}
        if ns.get('euid')!=0 or ns.get('passwd_home')is not None or ns.get('HOME')is not None:return None
    expected=copy.deepcopy(entry['differences'])
    current_version=policy_identity()['version']
    if current_version!=policy['version']:
        # The two original 0.1.1 residuals include an exact branded title.
        # Project only that seven-cell label for the reviewed 0.1.3 candidate;
        # retain every other recorded field and the historical policy itself.
        if (policy['version'],current_version)!=('0.1.1','0.1.3'):return None
        for difference in expected:
            if difference['field'] in ('snapshot.start.row0.text','snapshot.opened.row0.text'):
                old=difference['candidate']
                if not isinstance(old,str) or old.count('NARO 0.1.1')!=1:return None
                difference['candidate']=old.replace('NARO 0.1.1','NARO 0.1.3',1)
    canonical=lambda rows:json.dumps(sorted(rows,key=lambda x:x['field']),sort_keys=True)
    return entry['deviation_id'] if canonical(differences)==canonical(expected) else None


def _stateflags_title(row, width, version):
    flags = row[width-7:width-2]
    if len(flags) != 5 or any(c not in (' ', want) for c, want in zip(flags, 'IMLRS')):
        raise ValueError('unsupported state flags')
    tail = row[len('  GNU nano 9.3'):width-7].strip()
    modified = tail.endswith(' *')
    filename = tail[:-2] if modified else tail
    if not filename.isascii() or not filename or '*' in filename:
        raise ValueError('unsupported stateflags filename')
    def paint(label):
        cells = [' '] * width
        ver, path, stat = len(label)+3, len(filename)+1, 9
        if ver + path + stat > width:
            raise ValueError('unsupported clipped stateflags title')
        start = ver + (width-ver-path-stat)//2
        for at, text in [(2,label),(start,filename),(width-7,flags)]:
            for i,c in enumerate(text): cells[at+i]=c
        if modified:cells[start+len(filename):start+len(filename)+2]=list(' *')
        return ''.join(cells)
    if paint('GNU nano 9.3') != row:
        raise ValueError('stateflags title failed independent oracle')
    return paint('NARO '+version)


def _help_rows(width, language):
    lang = 'de' if language.lower().startswith('de') else 'C'
    source = (ROOT/'src/help_data.rs').read_text()
    block = re.search(r'\(\s*MAIN,\s*&\[(.*?)\]', source, re.S).group(1)
    parts = [json.loads(x) for x in re.findall(r'"(?:\\.|[^"\\])*"', block)]
    if lang == 'de':
        with (ROOT/'assets/locale/de/LC_MESSAGES/nano.mo').open('rb') as f: tr=gettext.GNUTranslations(f)
        parts = [tr.gettext(x) for x in parts]
    intro=''.join(parts)
    heading,body=intro.split('\n',1);body=body.removeprefix('\n')
    branded=re.sub(r'\b(?:nano|Nano|NANO)\b','NARO',body)
    def wrap(text):
        lines=[]
        span=max(40,min(width,74))
        for paragraph in text.split('\n'):
            rest=paragraph;first=True
            while len(rest)>span:
                cut=rest[:span].rfind(' ')
                if cut<=0:cut=span
                lines.append(((''if first else' ')+rest[:cut]).ljust(width)[:width])
                rest=rest[cut:].removeprefix(' ');first=False
            lines.append(((''if first else' ')+rest).ljust(width)[:width])
        return lines
    original,new=wrap(body),wrap(branded)
    if len(original)!=len(new):raise ValueError('unreviewed help reflow')
    title=re.sub(r'\b(?:nano|Nano|NANO)\b','NARO',heading)
    return heading,title,dict(zip(original,new))



def _reviewed_states(language):
    states=set(DEFAULT_STATES);reserves={9}
    # LANGUAGE is a request, not evidence of a successful message locale. Each
    # requested catalog and C is only a possibility until the complete original
    # row round-trips. Candidate output and the collector's locale are unused.
    for part in language.split(':'):
        lang=part.split('_')[0].split('.')[0]
        path=ROOT/'assets/locale'/lang/'LC_MESSAGES/nano.mo'
        if path.exists():
            with path.open('rb') as stream:translation=gettext.GNUTranslations(stream)
            values=[translation.gettext(word)for word in ('Modified','View','Restricted')]
            states.update(values);reserves.add(display_width(values[0])+1)
    if language.lower().startswith('de_de.iso'):
        states.add('Ver�ndert')
    return states,reserves


def _unique_projection(projections):
    choices=set(projections)
    if len(choices)!=1:raise ValueError('reference title projection absent or ambiguous')
    return choices.pop()


def _reference_title(reference,width,version,language):
    states,reserves=_reviewed_states(language);projections=[]
    for reserved in reserves:
        try:
            expected=candidate_title(reference.rstrip(),width,version,reserved=reserved,states=states)
            projections.append(display_pad(expected,width))
        except ValueError:continue
    return _unique_projection(projections)


def _title_context(case,snapshot):
    if not case:return None
    data=json.loads((ROOT/'tests/naro/identity-title-contexts.json').read_text())
    if data.get('schema')!='naro-identity-title-context-v1':
        raise ValueError('unknown reviewed title context schema')
    entry=data['cases'].get(case.get('id'))
    if not entry or snapshot not in entry['snapshots']:return None
    if (data['policy']!=POLICY or data['package_version']!=policy_identity()['version']
        or entry['reference_case_sha256']!=case_sha256(case)):
        raise ValueError('stale reviewed title context')
    return entry['snapshots'][snapshot]
