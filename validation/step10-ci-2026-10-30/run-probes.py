from pathlib import Path
import subprocess,os,json,sys
root=Path(sys.argv[1]);base=Path(sys.argv[2]);name=sys.argv[3];binary=sys.argv[4];reports=[]
for mode in ('original','synchronized'):
 out=base/(name+'-'+mode+'-attempt02');out.mkdir(exist_ok=False)
 with (out/'harness.log').open('w')as log:
  r=subprocess.run([sys.executable,str(root/'spec/tools/nanoharness.py'),str(base/(mode+'-delayed.json')),'--binary',binary,'--out',str(out),'--keep'],env={**os.environ,'NANOSPEC_WORK':'/tmp/naro-step10-'+name+'-'+mode},stdout=log,stderr=log)
 results=[]
 for p in sorted(out.glob('TEST-*/result.json')):
  v=json.loads(p.read_text());results.append({'id':v['scenario'],'steps_ok':v['steps_ok'],'failed':[c for c in v['checks']if not c['pass']],'saved_cursor':v['snapshots']['saved']['cursor'],'saved_status':v['snapshots']['saved']['rows'][21]['text'],'stderr':v['stderr'],'binary_sha256':v['binary_sha256'],'raw_output_sha256':v['raw_output_sha256']})
 reports.append({'mode':mode,'exit':r.returncode,'results':results})
(base/(name+'-probe-summary.json')).write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
