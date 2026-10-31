#!/usr/bin/env bash
# Private-workspace Ubuntu qualification entrypoint, invoked by run_closure_ubuntu.py.
set -euo pipefail
export PATH=/opt/rust/bin:/usr/local/bin:/usr/bin:/bin
export HOME=/work/build-home
export CARGO_HOME=/work/build-home/.cargo
export XDG_CONFIG_HOME=/work/build-home/.config
export CARGO_TARGET_DIR=/work/naro-target/checks
export RUSTC=/opt/rust/bin/rustc
export RUSTDOC=/opt/rust/bin/rustdoc
export CARGO_BUILD_JOBS=1
export CARGO_NET_OFFLINE=true
export PYTHONDONTWRITEBYTECODE=1
export NANOSPEC_WORK=/work/nanospec-work
export LOCPATH=/opt/nano-locales
export TMUX_TMPDIR=/work/tmux-sockets
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$NANOSPEC_WORK" /work/naro /work/reference /work/package-source
mkdir -p "$TMUX_TMPDIR"; chmod 700 "$TMUX_TMPDIR"
cleanup_tmux_owned() {
  local original_status=$? socket_dir="$TMUX_TMPDIR/tmux-$(id -u)" status=0 socket
  mkdir -p /out
  : > /out/tmux-cleanup.log
  if [[ -d "$socket_dir" && ! -L "$socket_dir" ]]; then
    for socket in "$socket_dir"/*; do
      [[ -S "$socket" ]] || continue
      tmux -S "$socket" kill-server >> /out/tmux-cleanup.log 2>&1 || status=1
    done
    sleep 0.1
    for socket in "$socket_dir"/*; do [[ ! -S "$socket" ]] || status=1; done
  fi
  echo "$status" > /out/tmux-cleanup.status
  trap - EXIT
  [[ "$status" == 0 ]] || exit 125
  exit "$original_status"
}
trap cleanup_tmux_owned EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cp -a /project/. /work/naro/
cp -a /project/. /work/package-source/
cp -a /reference-built/. /work/reference/
mkdir -p /work/naro/target/release
cp /frozen/naro /work/naro/target/release/naro
cp /root-reference.bin /out/root-reference.bin

for entry in de_DE:UTF-8:de_DE.UTF-8 ja_JP:UTF-8:ja_JP.UTF-8 de_DE:ISO-8859-1:de_DE.ISO-8859-1 en_US:ISO-8859-1:en_US.ISO-8859-1; do
  IFS=: read -r input encoding name <<< "$entry"
  localedef --no-archive -c -i "$input" -f "$encoding" "/opt/nano-locales/$name" || test -f "/opt/nano-locales/$name/LC_CTYPE"
done

cd /work/naro
python3 - <<'PY_SETUP'
import hashlib,json,os,subprocess,sys
from pathlib import Path
source=Path('/project')
copy=Path('/work/naro')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=copy,text=True).strip()
status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=copy,text=True)
assert not status,status
assert commit==os.environ['NARO_SOURCE_COMMIT'],commit
sys.path.insert(0,str(copy/'tools'))
from check_wrap_undo import source_fingerprint,verification_fingerprint
candidate=Path('/work/naro/target/release/naro')
candidate_info=json.loads(subprocess.check_output([str(candidate)],env={**os.environ,'NARO_BUILD_INFO':'1'},text=True))
assert candidate_info['version']==os.environ['NARO_EXPECTED_VERSION'],candidate_info
assert candidate_info['revision']==commit,candidate_info
assert candidate_info['source_sha256']==os.environ['NARO_SOURCE_FINGERPRINT']==source_fingerprint(copy),candidate_info
assert candidate_info['reference_commit']==os.environ['NARO_NANO_REFERENCE_COMMIT'],candidate_info
assert candidate_info['features']=='',candidate_info
adaptations=[]
file_hashes=[]
for folder in ('spec/evidence/scenarios','tests/follow-up/scenarios'):
 for path in sorted(Path(folder).glob('*.json')):
  raw=path.read_bytes(); cases=json.loads(raw); changes=0
  for case in cases:
   if case.get('locpath') and case['locpath']!='/opt/nano-locales':
    before=case['locpath'];case['locpath']='/opt/nano-locales';changes+=1
    adaptations.append({'file':path.as_posix(),'id':case.get('id'),'from':before,'to':'/opt/nano-locales'})
  if changes:
   path.write_text(json.dumps(cases,indent=1)+'\n')
   file_hashes.append({'file':path.as_posix(),'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'changed_cases':changes})
Path('/out/source-adaptations.json').write_text(json.dumps({'source_commit':commit,'changes':adaptations,'file_hashes':file_hashes},indent=2)+'\n')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
record={'source_commit':commit,'source_status_before_adaptation':status,'source_fingerprint':source_fingerprint(copy),'verification_fingerprint':verification_fingerprint(),'candidate_build_info':candidate_info,'candidate_sha256':sha('/work/naro/target/release/naro'),'reference_sha256':sha('/work/reference/bin/nano'),'root_reference_sha256':sha('/root-reference.bin'),'reference_version':subprocess.check_output(['/work/reference/bin/nano','--version'],text=True),'locale_inventory':subprocess.check_output(['locale','-a'],text=True),'locpath':os.environ.get('LOCPATH')}
Path('/out/runtime-inputs.json').write_text(json.dumps(record,indent=2)+'\n')
cases=[]
for path in sorted(Path('spec/evidence/scenarios').glob('*.json')):
 for case in json.loads(path.read_text()):
  if case.get('profile')=='tiny' or any(str(arg).startswith('/') for arg in case.get('args',[])) or case['id']=='TEST-BROWSE-003':continue
  cases.append(case)
Path('/out/reference-cases.json').write_text(json.dumps(cases,indent=1)+'\n')
PY_SETUP

run() {
  local name=$1; shift
  echo "COMMAND $name: $*" >> /out/commands.log
  set +e
  "$@" > "/out/$name.log" 2>&1
  local status=$?
  set -e
  echo "$status" > "/out/$name.status"
  echo "$name status=$status"
  [[ "$status" == 0 ]]
}

run reference-replay python3 tools/replay_reference.py --scenarios /out/reference-cases.json --binary /work/reference/bin/nano --out /out/reference
run terminal env NARO_REFERENCE_RUNS=/out/reference python3 tools/validate_parallel.py --binary /work/naro/target/release/naro --out /out/candidate --jobs 4
for suite in tools edges environments supplement backup fifo-eof signal-SIGTERM signal-SIGHUP; do
  run "followup-$suite" python3 tools/check_follow_up.py --suite "$suite" --binary /work/naro/target/release/naro --reference /work/reference/bin/nano --out "/out/$suite"
done
for suite in $(python3 -c 'import sys;sys.path.insert(0,"tools");from check_closure_regressions import SUITES;print(" ".join(SUITES))'); do
  run "closure-$suite" python3 tools/check_follow_up.py --suite "$suite" --binary /work/naro/target/release/naro --reference /work/reference/bin/nano --out "/out/$suite"
done
run closure-regressions python3 tools/check_closure_regressions.py --base /out --binary /work/naro/target/release/naro --reference /work/reference/bin/nano
run vt-ioctl python3 tools/check_follow_up.py --suite vt-ioctl --binary /work/naro/target/release/naro --reference /work/reference/bin/nano --out /out/vt-ioctl
run extras python3 tools/check_environment_extras.py --binary /work/naro/target/release/naro --reference /work/reference/bin/nano --out /out/extras
run cli python3 tools/check_cli.py --binary /work/naro/target/release/naro --out /out/cli
run large python3 tools/check_large_files.py --binary /work/naro/target/release/naro --out /out/large
run panic-hooks-build env CARGO_TARGET_DIR=/work/naro-target/hooks cargo build --features test-hooks --offline --locked
run panic python3 spec/tools/nanoharness.py tests/follow-up/scenarios/panic.json --candidate-expectations --binary /work/naro-target/hooks/debug/naro --out /out/panic
run credits-build env CARGO_TARGET_DIR=/work/naro-target/credits cargo build --release --features credits --offline --locked
python3 - <<'PY_VARIANTS'
import hashlib,json,os,subprocess
from pathlib import Path
variants={}
for name,path,features in [('hooks',Path('/work/naro-target/hooks/debug/naro'),'test-hooks'),('credits',Path('/work/naro-target/credits/release/naro'),'credits')]:
 info=json.loads(subprocess.check_output([str(path)],env={**os.environ,'NARO_BUILD_INFO':'1'},text=True))
 assert info['features']==features and info['version']==os.environ['NARO_EXPECTED_VERSION'],info
 assert info['revision']==os.environ['NARO_SOURCE_COMMIT'] and info['source_sha256']==os.environ['NARO_SOURCE_FINGERPRINT'],info
 variants[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'features':info['features'],'build_info':info,'target_directory':str(path.parents[1])}
Path('/out/variant-builds.json').write_text(json.dumps(variants,indent=2)+'\n')
PY_VARIANTS
run extensions python3 tools/check_extensions.py --default /work/naro/target/release/naro --credits /work/naro-target/credits/release/naro --panic-runs /out/panic --out /out/extensions
cd /work/package-source
run package python3 tools/package.py --binary /work/naro/target/release/naro --out /out/package
version=$(python3 -c 'import tomllib;print(tomllib.load(open("Cargo.toml","rb"))["package"]["version"])')
run package-check python3 tools/check_package.py --archive "/out/package/naro-$version-x86_64-unknown-linux-gnu.tar.gz" --source-archive "/out/package/naro-$version-source.tar.gz" --out /out/package-check
python3 - <<'PY_FINISH'
import json,subprocess
from pathlib import Path
runtime=Path('/work/naro');package=Path('/work/package-source')
runtime_status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=runtime,text=True)
package_status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=package,text=True)
Path('/out/private-source-status-after.json').write_text(json.dumps({'runtime_copy':runtime_status,'package_source_copy':package_status},indent=2)+'\n')
Path('/out/complete').write_text('completed\n')
PY_FINISH
