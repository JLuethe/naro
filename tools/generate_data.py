#!/usr/bin/env python3
"""Generate Rust data from pinned GPL nano inventories. No runtime source dependency.
Reference: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.
"""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def q(s):
    return json.dumps(s,ensure_ascii=False).replace('\\u0000','\\0')
flags='DONTUSE ZERO NO_HELP CONSTANT_SHOW LINE_NUMBERS WHITESPACE_DISPLAY NO_SYNTAX SOFTWRAP BREAK_LONG_LINES TABS_TO_SPACES AUTOINDENT SMART_HOME CUT_FROM_CURSOR USE_MOUSE CASE_SENSITIVE USE_REGEXP BACKWARDS_SEARCH COLON_PARSING NOREAD_MODE LOCKING RESTRICTED VIEW_MODE USE_MAGIC NEW_BUFFER NO_CONVERT NO_NEWLINES HISTORYLOG POSITIONLOG MAKE_BACKUP INSECURE_BACKUP SAVE_ON_EXIT MAKE_IT_UNIX PRESERVE REBIND_DELETE RAW_SEQUENCES MODERN_BINDINGS LET_THEM_ZAP AFTER_ENDS WORD_BOUNDS AT_BLANKS TRIM_BLANKS BOOKSTYLE NO_WRAP JUMPY_SCROLLING SOLO_SIDESCROLL QUICK_BLANK SHOW_CURSOR BOLD_TEXT EMPTY_LINE INDICATOR STATEFLAGS MINIBAR'.split()
f=['// Generated from pinned GNU nano data; GPL-3.0-or-later.','// Reference: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.','#![allow(dead_code)]']
for i,s in enumerate(flags):f.append(f'pub const {s}: usize = {i};')
menus='MAIN SEARCH REPLACE REPLACEWITH GOTO WRITE INSERT EXEC HELP SPELL BROWSER BSEARCH BGOTO YESNO LINTER HSEARCH'.split()
for i,s in enumerate(menus):f.append(f'pub const {s}: u32 = {1<<i};')
f+=['#[derive(Clone, Debug)]','pub struct Binding {pub key:i32,pub menus:u32,pub func:String,pub tag:String,pub toggle:usize,pub expansion:Option<String>}', '#[derive(Clone, Debug)]','pub struct Function {pub func:String,pub menus:u32,pub tag:String,pub phrase:String,pub blank:bool}']
f.append('pub fn keymap(profile: &str) -> (Vec<Binding>,Vec<Function>) {match profile {')
for p in sorted((ROOT/'spec/evidence/tables').glob('*.json')):
 d=json.loads(p.read_text());f.append('#[cfg('+('feature = \"tiny\"' if p.stem.startswith('tiny-') else 'not(feature = \"tiny\")')+')]');f.append(q(p.stem)+' => (vec![')
 for k in d['keys']:
  f.append('Binding{key:%d,menus:%d,func:%s.into(),tag:%s.into(),toggle:%d,expansion:None},'%(k['keycode'],k['menus_mask'],q(k['func']),q(k['keystr']),k.get('toggle',0)))
 f.append('], vec![')
 for x in d['funcs']:
  f.append('Function{func:%s.into(),menus:%d,tag:%s.into(),phrase:%s.into(),blank:%s},'%(q(x['func']),x['menus_mask'],q(x['tag']),q(x.get('phrase','')),str(x.get('blank_after',False)).lower()))
 f.append(']),')
f.append('_ => keymap(if cfg!(feature="tiny") {"tiny-utf8"} else {"default-utf8"}),}}')
f.append('pub const RC_OPTIONS: &[(&str,usize)] = &[')
for r in csv.DictReader((ROOT/'spec/data/nanorc-options.csv').open()):
 if r['flag'] in flags:f.append('(%s,%s),'%(q(r['option']),r['flag']))
f.append('];')
f.append('pub const RC_FUNCTIONS: &[(&str,&str)] = &[')
for r in csv.DictReader((ROOT/'spec/data/keybindings.csv').open()):
 for name in r['rc_function_names'].split():
  if name and not r['toggle_flag']:f.append('(%s,%s),'%(q(name),q(r['function_c'])))
f.append('];')
f.append('pub const TOGGLES: &[(&str,usize,&str)] = &[')
for r in csv.DictReader((ROOT/'spec/data/toggles.csv').open()):f.append('(%s,%s,%s),'%(q(r['rc_function']),r['flag'],q(r['description'])))
f.append('];')
(ROOT/'src/generated.rs').write_text('\n'.join(f)+'\n')
rows=list(csv.DictReader((ROOT/'spec/data/cli-options.csv').open()))
options=[]
for r in sorted(rows,key=lambda r:int(r['long_source'].rsplit(':',1)[-1]) if r['long_source'] else 0):
 for name in [r['long']]+r['deprecated_aliases'].split():
  if not name.startswith('--'):continue
  name=name[2:];code=ord(r['short'][1:]) if r['short'].startswith('-') else 0x700
  entry='{%s,%d,NULL,%d},'%(q(name),int(r['argument']!='none'),code)
  options.append(entry if chr(code) in 'DKRUVcdhptvx/' else '#ifndef NARO_TINY\n'+entry+'\n#endif')
(ROOT/'native/options.inc').write_text('// Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c\nstatic const struct option options[] = {\n'+'\n'.join(options)+'\n{NULL,0,NULL,0}};\n')
# Exact help text is reference data, not an executable dependency.
probes=json.loads((ROOT/'spec/evidence/cli/cli-probes.json').read_text())['results']
for ident,name in [('CLI-P-001','help.txt'),('CLI-P-003','help-restricted.txt'),('CLI-P-007','help-tiny.txt')]:
 (ROOT/'assets'/name).write_text(next(p['stdout'] for p in probes if p['id']==ident))
