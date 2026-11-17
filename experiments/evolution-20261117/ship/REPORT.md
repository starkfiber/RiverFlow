# RF2Ship: accelerate the actual secure-transport authenticator

17 November 2026. Isolated candidate, original development tree and stable release unchanged.

## Change

RF2Ship 0.18's `aead_reference.c` multiplies the Poly1305 accumulator using 128 bit-serial iterations. Each iteration masks three limbs and performs two modular additions. This is repeated for every authenticated block. The candidate replaces only `mulp` with fixed-work 44/44/42-bit multiplication and reduction modulo `2^130 - 5`. ChaCha20, wire format, 128-byte input limits, tag comparison, status codes and fail-before-decrypt behavior stay identical.

This is an optimization of RF2Ship's existing Clang-encoded freestanding x86 reference, incorporated by its checked RF2 bootstrap emitter. It is not a new cryptographic algorithm or evidence of general native x86 compilation by RF2.

The original source SHA-256 is `7a58bfcd20f6bd9a15555bd2052cadc6b2dae63e108d6d2d27dbbb95a35eb222`; candidate `d5fe29eaf2dcf57499105972cbbe59d199cf5b6067848a8448540c59119a57db`.

## Measured full AEAD call performance

ARM64 native compiled C, Apple clang 21.0.0, this Mac. Each workload has 11 paired samples in alternating baseline/candidate order, 4,000 calls per sample, 20 warm-up calls. Timed loops are C; Python only checks and summarizes. Inputs and output tags are consumed so calls cannot be optimized out. Nonce changes per invocation; this is synthetic computation timing, not a secure sender for reuse.

| Data / AAD bytes | Baseline `-O2` ns | Candidate `-O2` ns | Speedup | Speedup with both `-Oz -ffreestanding -fno-builtin` |
|---|---:|---:|---:|---:|
| 0 / 32 | 1,754.25 | 223.75 | 7.84× | 4.25× |
| 16 / 32 | 2,384.50 | 338.25 | 7.05× | 3.83× |
| 64 / 32 | 3,947.00 | 370.00 | 10.67× | 5.39× |
| 128 / 32 | 6,167.25 | 515.00 | 11.98× | 5.67× |
| **72 / 40: existing secure envelope** | **5,077.25** | **470.25** | **10.80×** | **5.11×** |

For that existing envelope at `-Oz`, baseline median was 5,388.50 ns and candidate 1,055.25 ns. Paired sample speedups ranged 4.91–5.34×. Raw samples and full ranges are in `TIMINGS*.csv` / `PERFORMANCE.json`.

These numbers measure host-native bounded AEAD, not guest packet throughput, whole firewall speed, energy, AI tokens or physical hardware. In particular the 10.80× host result must not be presented as a 10.80× RF2Ship network speedup.

## Executed correctness and integration

- **15,348 checks:** baseline and candidate against Apple's independent CryptoKit ChaChaPoly. 1,100 inputs include all 144 cross-pairs of 12 important AAD/data lengths, random keys/nonces and remaining random lengths. Seal, successful open, altered tags, altered AAD and oversized/maximum lengths are checked. Bad authentication preserves ciphertext.
- **12,024 arithmetic inputs per implementation:** independent exact-integer multiplication modulo `2^130 - 5`, including canonical accumulator extrema and full 128-bit multiplier extrema (a wider multiplier range than the normal clamped input).
- **10,000 sanitizer comparisons:** AddressSanitizer plus UndefinedBehaviorSanitizer, exact-sized allocated AAD/data buffers, baseline/candidate seal/open outputs. Oversized null-pointer contexts refuse before access. No sanitizer findings.
- **Actual local x86 guest execution:** generated candidate assembly with the existing `-Oz`, freestanding, no-SSE, no-MMX, no-red-zone flags; asserted no external crypto calls; assembled and rebuilt complete isolated images using hash-pinned RF2 SDK 0.50 emitter. Baseline **40/40 PC + 40/40 Q35** secure transport controls passed; candidate **40/40 PC + 40/40 Q35** passed, using QEMU TCG and Unix sockets only. The original campaign exercises encrypted transport, malformed/authentication/replay refusal, state and erasure behavior. These are existing campaign tests, not 160 newly invented tests.
- `prepare_guest.py` was run end to end after isolating the copied source/build paths; logs are saved. The first adaptation failed before compilation due to missing Path-expression parentheses; corrected locally and recorded in `GUEST-HARNESS-FAILURE.txt`.

Guest images SHA-256: baseline `b5cee78c7294eb2f475b064536495260bf6da85224d3d29c98411424b3af53a8`; candidate `4ac4f627c82f403865facf94235bf58ea4952c1ce4d9c594f0c20f659d9e2450`.

## Reproduce and review

From the experiment repository root:

```sh
experiments/evolution-20261117/ship/run.sh --guest
```

This needs existing clang, Swift/CryptoKit, xorriso, local `qemu-system-x86_64`, and the pinned external RF2Ship 0.18 snapshot. It creates only local experiment/artifact files; it does not invoke SSH, use host network peers, touch VM102 or deploy. `prepare_guest.py` fails if its original C-source hash changes. Source snapshot hashes, compiler hash and guest manifests are retained in artifacts.

Artifacts: `artifacts/evolution-20261117/ship/` — `RECEIPT.json`, `CORRECTNESS.json`, `LIMB-CORRECTNESS.json`, `SANITIZER.log`, `PERFORMANCE.json`, raw CSVs, source hash manifest, `GUEST-REPRODUCE.log`, and each image's `SECURE-VERIFICATION.json`.

The next source integration is the single reviewed `mulp` replacement, regenerated `crypto.s` and combined `console.s`, followed by the full RF2Ship acceptance suite. Existing copies in this experiment are not an instruction to overwrite active development. VM102, live networking, production/stable releases and remote Memory were untouched.

Cryptographic review remains required before promotion: the source makes no verified constant-time or complete register-erasure guarantee. The scratch-erasure intent remains, but replacing three array temporaries with wide arithmetic changes compiler register allocation. Tests establish outputs and bounded controls; they do not establish side-channel immunity. The guest campaign is a subset of the full firewall acceptance ledger.
