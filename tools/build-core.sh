#!/bin/sh
set -eu
if [ "$#" -ne 4 ]; then
 printf '%s\n' 'Usage: build-core.sh native-rf2 native-rf2c source.flow new-output-directory' >&2
 exit 1
fi
rf2_runtime=$1
rf2_compiler=$2
rf2_source=$3
rf2_out=$4
rf2_root=$(CDPATH= cd -- "${0%/*}/.." && pwd)
/bin/mkdir -- "$rf2_out"
"$rf2_runtime" lower "$rf2_source" > "$rf2_out/kernel.rf2"
/bin/cat "$rf2_root/native/lowered-harness.rf2" "$rf2_out/kernel.rf2" > "$rf2_out/program.rf2"
"$rf2_compiler" "$rf2_out/program.rf2" "$rf2_out/program"
/usr/bin/codesign -s - --force "$rf2_out/program"
/usr/bin/codesign --verify "$rf2_out/program"
