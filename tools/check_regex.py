#!/usr/bin/env python3
"""Validate Naro's actual Rust/native regex wrapper through harness fixtures.
Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.
"""
import argparse,hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--binary',default=str(ROOT/'target/debug/naro'));args=p.parse_args();args.binary=str(pathlib.Path(args.binary).resolve())
out=ROOT/'spec/evidence/naro-regex';out.mkdir(parents=True,exist_ok=True)
cases=(ROOT/'spec/evidence/regex/cases.tsv').read_text()
scenarios=[]
for locale in ('C','en_US.UTF-8'):
 scenarios.append(dict(id='TEST-NARO-REGEX-'+('001'if locale=='C'else'002'),lang=locale,env={'NARO_REGEX_PROBE':'1'},stdin=cases,stdout_redirect=True,hold_tty=True,steps=[{'wait_exit':5}],expect={'exit_status':0}))
path=out/'scenarios.json';path.write_text(json.dumps(scenarios,indent=1)+'\n')
r=subprocess.run([sys.executable,str(ROOT/'spec/tools/nanoharness.py'),str(path),'--binary',args.binary,'--out',str(out)])
failed=r.returncode;report=[]
for s in scenarios:
 result=json.loads((out/s['id']/'result.json').read_text());actual=[json.loads(l)for l in result['stdout'].splitlines()];expected=[json.loads(l)for l in (ROOT/'spec/evidence/regex'/('results-'+s['lang']+'.jsonl')).read_text().splitlines()]
 diffs=[]
 if len(actual)!=len(expected):diffs.append(dict(count=[len(expected),len(actual)]))
 for i,(a,b)in enumerate(zip(expected,actual)):
  # regcomp numeric error codes are platform details; compare success/error text.
  a['compile']=bool(a['compile']);b['compile']=bool(b['compile'])
  if a!=b:diffs.append(dict(case=i+1,expected=a,actual=b))
 report.append(dict(locale=s['lang'],cases=len(actual),differences=diffs));failed|=bool(diffs)
 print(s['lang'],len(actual),'cases,',len(diffs),'differences')
(out/'report.json').write_text(json.dumps({'reference_commit':'6ed285c3ec7a1d228def4d4e7021c6ba269f620c','binary_sha256':hashlib.sha256(pathlib.Path(args.binary).read_bytes()).hexdigest(),'locales':report},indent=2)+'\n')
raise SystemExit(failed)
