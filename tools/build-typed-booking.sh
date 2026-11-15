#!/bin/sh
# Explicit trusted development build. No implicit downloads or runtime fallbacks.
set -eu
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
 printf '%s\n' 'Usage: build-typed-booking.sh selected-native-rf2c new-directory [--opt]' >&2
 exit 2
fi
if [ "$#" -eq 3 ] && [ "$3" != '--opt' ]; then
 printf '%s\n' 'Only --opt is supported.' >&2
 exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
compiler=$1
destination=$2
/bin/mkdir -- "$destination"
/bin/mkdir -- "$destination/source" "$destination/source/lib"
/bin/cp "$root"/experiments/typed-booking/*.flow "$destination/source/"
/bin/cp "$root"/experiments/typed-booking/lib/*.flow "$destination/source/lib/"
for name in io storage text datetime; do
 /bin/cp "$root/examples/documents/lib/$name.flow" "$destination/source/lib/"
done
/bin/cp "$root/examples/evidence-contract/lib/sha256.rf2" "$destination/source/lib/"
/bin/cp "$root/examples/collection-tools/lib/output.rf2" "$destination/source/lib/"
for entry in main web agent; do
 name=booking
 if [ "$entry" != main ]; then name="booking-$entry"; fi
 "$compiler" "$destination/source/$entry.flow" "$destination/$name" ${3:+"$3"}
 /usr/bin/codesign -s - --force "$destination/$name"
 /usr/bin/codesign --verify "$destination/$name"
done
printf '%s\n' 'Built native CLI, browser GUI and bounded agent server. No program has been launched.'
