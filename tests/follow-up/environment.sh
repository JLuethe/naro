#!/bin/bash
# Run as an ordinary uid inside the private rootless Ubuntu container.
# GNU nano intentionally ignores HOME for uid 0; tests require fixture HOME.
set -euo pipefail
export HOME=/work/build-home
export CARGO_HOME=/work/build-home/.cargo
export XDG_CONFIG_HOME=/work/build-home/.config
mkdir -p "$HOME" "$XDG_CONFIG_HOME"
mkdir -p /work/naro /work/ref-source /work/ref-build /opt/nano-locales
tar -C /project --exclude=./target --exclude='./spec/evidence/naro*' --exclude=./spec/evidence/follow-up-runs -cf - . | tar -C /work/naro -xf -
cp -a /reference-source/. /work/ref-source/
# Bootstrap exports contain host automake symlinks; use container auxiliaries.
python3 - <<'PY_AUX'
from pathlib import Path
import shutil
aux=next(Path("/usr/share").glob("automake-*/compile")).parent
for name in ["compile","config.guess","config.sub","depcomp","install-sh","missing"]:
 target=Path("/work/ref-source")/name
 if target.is_symlink():target.unlink()
 shutil.copy2(aux/name,target)
PY_AUX
for entry in de_DE:UTF-8:de_DE.UTF-8 ja_JP:UTF-8:ja_JP.UTF-8 de_DE:ISO-8859-1:de_DE.ISO-8859-1 en_US:ISO-8859-1:en_US.ISO-8859-1; do
  IFS=: read -r input encoding name <<< "$entry"
  localedef --no-archive -c -i "$input" -f "$encoding" "/opt/nano-locales/$name" || test -f "/opt/nano-locales/$name/LC_CTYPE"
done
if test -d /reference-built; then
 cp -a /reference-built /work/reference
else
cd /work/ref-build
/work/ref-source/configure --prefix=/work/reference > /out/reference-configure.log 2>&1
make -C lib -j4 > /out/reference-build.log 2>&1
make -C src -j4 >> /out/reference-build.log 2>&1
make -C po -j4 >> /out/reference-build.log 2>&1
make -C src install > /out/reference-install.log 2>&1
make -C po install >> /out/reference-install.log 2>&1
fi
cd /work/naro
cargo build --release --offline > /out/candidate-build.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,hashlib
source=Path('/reference-pinned/src'); export=Path('/work/ref-source/src')
assert all(hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((export/p.name).read_bytes()).digest()for p in source.glob('*.c'))
for folder in ['spec/evidence/scenarios','tests/follow-up/scenarios']:
 for path in Path(folder).glob('*.json'):
  cases=json.loads(path.read_text())
  for case in cases:
   if 'locpath'in case:case['locpath']='/opt/nano-locales'
  path.write_text(json.dumps(cases,indent=1)+'\n')
cases=[]
for path in sorted(Path('spec/evidence/scenarios').glob('*.json')):
 for case in json.loads(path.read_text()):
  if case.get('profile')=='tiny'or any(a.startswith('/')for a in case.get('args',[]))or case['id']=='TEST-BROWSE-003':continue
  cases.append(case)
Path('/out/reference-cases.json').write_text(json.dumps(cases,indent=1)+'\n')
PY
python3 tools/replay_reference.py --scenarios /out/reference-cases.json --binary /work/reference/bin/nano --out /out/reference > /out/reference-replay.log 2>&1
NARO_REFERENCE_RUNS=/out/reference python3 tools/validate_parallel.py --binary target/release/naro --out /out/candidate --jobs 4 > /out/candidate-replay.log 2>&1
python3 tools/check_follow_up.py --suite tools --binary target/release/naro --reference /work/reference/bin/nano --out /out/tools > /out/tools-replay.log 2>&1
python3 tools/check_follow_up.py --suite edges --binary target/release/naro --reference /work/reference/bin/nano --out /out/edges > /out/edges-replay.log 2>&1
for suite in environments supplement backup fifo-eof signal-SIGTERM signal-SIGHUP; do
 python3 tools/check_follow_up.py --suite "$suite" --binary target/release/naro --reference /work/reference/bin/nano --out "/out/$suite" > "/out/$suite-replay.log" 2>&1
done
python3 - <<'PY'
import json,sys
sys.path.insert(0,'tools');from environment import snapshot
json.dump(snapshot(),open('/out/environment.json','w'),indent=2)
PY
python3 tools/package.py --binary target/release/naro --out /out/package > /out/package.log 2>&1
cp target/release/naro /out/naro
cp -a tests/follow-up/scenarios /out/scenario-revisions
printf '%s\n' completed > /out/complete
