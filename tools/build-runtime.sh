#!/bin/sh
set -eu
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
 printf '%s\n' 'Usage: build-runtime.sh native-rf2c new-output-directory [--opt]' >&2
 exit 1
fi
rf2_compiler=$1
rf2_out=$2
rf2_root=$(CDPATH= cd -- "${0%/*}/.." && pwd)
/bin/mkdir -- "$rf2_out"
/bin/cat "$rf2_root/native/rf2.rf2" "$rf2_root/native/core.rf2" "$rf2_root/native/attendance.rf2" "$rf2_root/native/attendance-kernel.rf2" "$rf2_root/native/fingerprint.rf2" "$rf2_root/native/invoice.rf2" "$rf2_root/native/invoice-kernel.rf2" "$rf2_root/native/prepared.rf2" "$rf2_root/native/workspace.rf2" "$rf2_root/native/editor.rf2" > "$rf2_out/runtime.rf2"
"$rf2_compiler" "$rf2_out/runtime.rf2" "$rf2_out/rf2" ${3:+"$3"}
/usr/bin/codesign -s - --force "$rf2_out/rf2"
/usr/bin/codesign --verify "$rf2_out/rf2"
