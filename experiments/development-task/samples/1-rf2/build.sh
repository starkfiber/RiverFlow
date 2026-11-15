#!/bin/sh
set -eu
cd "$(dirname "$0")"
# rf2c deliberately refuses to overwrite existing output.
rm -f app tests/http_harness
./rf2c main.flow app --opt
/usr/bin/codesign -s - app
./rf2c http-test.flow tests/http_harness --opt
/usr/bin/codesign -s - tests/http_harness
