#!/bin/sh
set -eu
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
 printf '%s\n' 'Usage: build-program.sh native-rf2c source.rf2 new-directory [--opt]' >&2
 exit 1
fi
if [ "$#" -eq 4 ] && [ "$4" != '--opt' ]; then
 printf '%s\n' 'Only --opt is supported' >&2
 exit 1
fi
/bin/mkdir -- "$3"
"$1" "$2" "$3/program" ${4:+"$4"}
/usr/bin/codesign -s - --force "$3/program"
/usr/bin/codesign --verify "$3/program"
printf '%s\n' 'Program built and signed; execution is a separate action.'
