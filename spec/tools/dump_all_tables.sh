#!/bin/sh
# Dump the effective key and function tables of the pinned reference builds
# under every profile that changes shortcut registration.
# Reference revision: 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
#
# Requires: tmux, gdb, the builds under ~/src/nano-install/{default,tiny}.
# Output: spec/evidence/tables/<profile>.json  (raw gdb dumps)

set -u
SPEC=$(cd "$(dirname "$0")/.." && pwd)
OUT=$SPEC/evidence/tables
WORK=${TMPDIR:-/tmp}/nano-spec-tables.$$
mkdir -p "$OUT" "$WORK/home"
DEF=$HOME/src/nano-install/default/bin
TINY=$HOME/src/nano-install/tiny/bin

run() {  # profile  term  lang  binary  args...
	profile=$1; term=$2; lang=$3; bin=$4; shift 4
	rm -f "$OUT/$profile.json"
	tmux -L nanospec-tables -f /dev/null new-session -d -x 80 -y 24 \
		"env -i HOME=$WORK/home TERM=$term LANG=$lang PATH=/usr/bin DUMP_OUT=$OUT/$profile.json \
		 gdb -q -batch -x $SPEC/tools/dump_tables.py --args $bin $*; sleep 1"
	i=0
	while [ ! -s "$OUT/$profile.json" ] && [ $i -lt 60 ]; do sleep 0.5; i=$((i+1)); done
	sleep 0.5
	tmux -L nanospec-tables kill-server 2>/dev/null
	if [ -s "$OUT/$profile.json" ]; then echo "ok   $profile"; else echo "FAIL $profile"; fi
}

T=tmux-256color
run default-utf8        $T en_US.UTF-8 $DEF/nano  -I
run default-C           $T C           $DEF/nano  -I
run default-modern      $T en_US.UTF-8 $DEF/nano  -I --modernbindings
run default-preserve    $T en_US.UTF-8 $DEF/nano  -I --preserve
run default-restricted  $T en_US.UTF-8 $DEF/nano  -I --restricted
run default-rnano       $T en_US.UTF-8 $DEF/rnano -I
run default-view        $T en_US.UTF-8 $DEF/nano  -I --view
run default-saveonexit  $T en_US.UTF-8 $DEF/nano  -I --saveonexit
run default-modern-vt220 vt220 en_US.UTF-8 $DEF/nano -I --modernbindings
run tiny-utf8           $T en_US.UTF-8 $TINY/nano
run tiny-C              $T C           $TINY/nano
run tiny-modern         $T en_US.UTF-8 $TINY/nano --modernbindings
run tiny-restricted     $T en_US.UTF-8 $TINY/nano --restricted
rm -rf "$WORK"
