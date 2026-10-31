"""Explicit NARO identity expectations; never normalize recorded terminal output.

Reference scenarios/oracles stay untouched. Overrides bind to exact case content
and package version, so a source scenario edit or version bump requires review.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import tomllib
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
OVERLAYS = ROOT / 'tests/naro/identity-overrides.json'
POLICY = 'Q-IDENTITY-001'


def case_sha256(case):
    return hashlib.sha256(json.dumps(case, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def candidate_case(case, overlays=None):
    selected = copy.deepcopy(case)
    if 'candidate_expect' in selected:
        selected['expect'] = copy.deepcopy(selected['candidate_expect'])
    data = json.loads(OVERLAYS.read_text()) if overlays is None else overlays
    version = tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version']
    if data['policy'] != POLICY or data['package_version'] != version:
        raise ValueError('candidate identity policy/version needs review')
    override = data['cases'].get(case['id'])
    if override:
        if override['reference_case_sha256'] != case_sha256(case):
            raise ValueError('stale candidate identity override: ' + case['id'])
        selected['expect'] = copy.deepcopy(override['expect'])
        if 'steps' in override:
            selected['steps'] = copy.deepcopy(override['steps'])
    return selected


def expected_cli_output(reference, profile='default'):
    """Project only exact known CLI identity surfaces in an expected oracle.

    This function never receives or rewrites actual candidate output.
    """
    version = tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version']
    if reference.startswith(' GNU nano, version ') and not reference.startswith(' GNU nano, version 9.3\n'):
        raise ValueError('unsupported GNU nano version oracle')
    if reference.startswith(' GNU nano, version 9.3\n'):
        old = (' GNU nano, version 9.3\n'
               + ('' if profile == 'tiny' else ' (C) 2026 the Free Software Foundation and various contributors\n')
               + ' Compiled options: ' + ('--enable-tiny ' if profile == 'tiny' else '') + '--enable-utf8\n')
        if reference != old:
            raise ValueError('unrecognized nano version oracle; review before projection')
        return (f' NARO, version {version}\n'
                ' Independent Rust port of GNU nano; reference version 9.3\n'
                ' License: GPL-3.0-or-later\n'
                f' Compiled profile: {profile}; UTF-8 enabled\n')
    if reference.startswith('Usage: nano '):
        return reference.replace('Usage: nano ', 'Usage: naro ', 1).replace(', nano reads data', ', naro reads data').replace('configuring nano', 'configuring NARO')
    return reference


def display_width(text):
    """Reviewed terminal widths: controls forbidden, combining zero, W/F two."""
    if any(ord(c)<32 or 0x7f<=ord(c)<0xa0 for c in text):
        raise ValueError('control in display text')
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in text)


def display_slice(text, start=0, stop=None):
    """Slice whole glyphs by display cells; refuse cuts through wide glyphs."""
    result=[];column=0;previous_selected=False
    for char in text:
        span=display_width(char)
        if span==0:
            if previous_selected:result.append(char)
            continue
        if (column<start<column+span) or (stop is not None and column<stop<column+span):
            raise ValueError('display slice crosses a wide glyph')
        previous_selected=column>=start and (stop is None or column<stop)
        if previous_selected:result.append(char)
        column+=span
    return ''.join(result)


def display_pad(text, width):
    cells=display_width(text)
    if cells>width:raise ValueError('display text exceeds width')
    return text+' '*(width-cells)


def title_row(cols, filename, state='', label='NARO 0.1.1', reserved=9):
    """Independent GNU C titlebar algorithm; ASCII names, reviewed Unicode states."""
    if (not filename.isascii() and filename != 'New·Buffer') or not filename or any(ord(c)<32 for c in filename):
        raise ValueError('title oracle needs a printable ASCII filename')
    row=[' ']*cols
    def put(start,text):
        column=start;previous=None
        for char in text:
            span=display_width(char)
            if column+span>cols:break
            if span==0:
                if previous is not None:row[previous]+=char
                continue
            if column>=0:
                row[column]=char;previous=column
                for tail in range(1,span):row[column+tail]=''
            column+=span
    plug=0 if state else reserved
    ver=display_width(label)+3
    path=display_width(filename)+bool(state)
    # This historical ISO trace has an extra decoder replacement cell; its
    # original gettext state still occupies nine terminal columns.
    stat=(9 if state=='�Ver�ndert' else display_width(state))+2
    if ver+path+plug+stat<=cols:put(2,label)
    else:
        ver=2
        if ver+path+plug+stat>cols:plug=0
        if ver+path+plug+stat>cols:ver=0;stat=max(0,stat-2)
    offset=ver+max(0,cols-ver-plug-stat-path)//2 if ver else 0
    if path+plug+stat<=cols:put(offset,filename)
    elif 5+stat<=cols:
        put(offset,'...')
        start=max(0,3+path+stat-cols)
        put(offset+3,display_slice(filename,start,start+max(0,cols-stat-3)))
    put(max(0,cols-stat),state)
    return ''.join(row).rstrip()


DEFAULT_STATES=('Modified','View','Restricted','Verändert','�Ver�ndert')


def candidate_title(reference, cols=80, version='0.1.1', reserved=9, states=DEFAULT_STATES):
    prefix='  GNU nano 9.3'
    if not reference.startswith(prefix):raise ValueError('not a full nano title assertion')
    rest=reference[len(prefix):]
    names='|'.join(re.escape(state) for state in sorted(states,key=len,reverse=True))
    match=re.fullmatch(r' +(.*?)(?: {2,}('+names+r'))?',rest)
    if not match:raise ValueError('unrecognized nano title assertion')
    filename,state=match.group(1),match.group(2)or''
    if title_row(cols,filename,state,'GNU nano 9.3',reserved)!=reference:
        raise ValueError('reference title does not match independent layout oracle: '+repr(reference))
    return title_row(cols,filename,state,'NARO '+version,reserved)
