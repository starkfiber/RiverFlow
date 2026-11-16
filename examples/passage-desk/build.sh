#!/bin/sh
set -eu
if [ "$#" -ne 3 ]; then
  printf '%s\n' 'Usage: build.sh qualified-rf2c absolute-sdk-root new-build-directory' >&2
  exit 2
fi
entry=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -- "$3"
"$1" "$entry/main.flow" "$3/app" --compact --opt --sdk-root "$2" --diagnostic-json
/usr/bin/codesign -s - "$3/app"
/usr/bin/codesign --verify "$3/app"
printf '%s\n' 'Built. Run the app explicitly with report, html or mcp and a selected file/query.'
