#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
S=experiments/evolution-20261117/ship
A=artifacts/evolution-20261117/ship
mkdir -p "$A"
for impl in baseline candidate; do
 clang -O2 -dynamiclib "$S/$impl.c" -o "$A/$impl.dylib"
 clang -O2 -c -Drf2_aead=${impl}_aead "$S/$impl.c" -o "$A/$impl.o"
 clang -Oz -ffreestanding -fno-builtin -c -Drf2_aead=${impl}_aead "$S/$impl.c" -o "$A/$impl-oz.o"
 clang -O1 -g -fsanitize=address,undefined -c -Drf2_aead=${impl}_aead "$S/$impl.c" -o "$A/$impl-san.o"
done
swiftc -O "$S/CryptoOracle.swift" -o "$A/crypto-oracle"
python3 "$S/verify.py"
python3 "$S/check_limbs.py"
clang -O1 -g -fsanitize=address,undefined "$S/sanitize.c" "$A/baseline-san.o" "$A/candidate-san.o" -o "$A/sanitize"
"$A/sanitize" > "$A/SANITIZER.log"
clang -O2 "$S/bench.c" "$A/baseline.o" "$A/candidate.o" -o "$A/bench"
"$A/bench" > "$A/TIMINGS.csv"
clang -O2 "$S/bench.c" "$A/baseline-oz.o" "$A/candidate-oz.o" -o "$A/bench-oz"
"$A/bench-oz" > "$A/TIMINGS-OZ.csv"
# Explicitly optional: copies the reviewed external snapshot into artifacts and
# runs only local QEMU Unix-socket peers; no live VMs, SSH, or WAN.
if [ "${1:-}" = "--guest" ]; then python3 "$S/prepare_guest.py"; fi

python3 "$S/summarize.py"
