# Local 0.24 candidate: remove preparation cost and qualify call preservation

This candidate adds `bswap32` and `bswap64`, improves SHA preparation and adds a real file-checksum utility. Stable downloads are unchanged. This historical 0.24 work is included in the later 0.25 source candidate, published through the verified SFE browser session.

## Mechanisms and boundaries

`bswap32(value)` reverses the low four bytes and returns a zero-extended u64. `bswap64(value)` reverses all eight bytes. They lower to established ARM REV W0,W0 and REV X0,X0 instructions. They are pure arithmetic in the trusted systems profile, including reads of scalar view elements. They add no bounded Core grammar, MCP effect, novel binary encoding or transistor mechanism.

A narrow classification pass recognises inline buffer, load/store, rotate, byte-swap, logical and SHA-block intrinsics that make no actual calls and preserve x9-x15. Functions with at most seven local slots may use the existing caller-saved local registers. Actual calls, syscalls, unknown constructors, platform calls and owned cleanup retain conservative preservation. Larger frames retain eight callee-saved registers rather than spilling a hot eighth local. This is a tested compiler optimisation, not a whole-program ABI proof.

The accelerated SHA path initializes its fixed constants once, removes unused scalar locals, clears padding with word stores, writes the bit length with bswap64 and writes the digest with bswap32. Empty full-block processing is skipped. Hardware compression and the runtime feature fallback are unchanged. Shared buffers remain nonreentrant; this is not a general concurrent crypto API. The CommonCrypto API has different generality and state management, so a task win is not a whole-language comparison.

## In-process acceptance measurements

Each native process loads its file, initializes its clock, performs one warmup hash, then times only the repeated complete SHA API task. First-byte mutation and the final digest-byte sum match across variants. Reported time excludes process startup, file I/O, allocation, initial feature discovery and first constant initialization. Native variants use mach_absolute_time with the returned timebase; Python uses perf_counter_ns. These are elapsed API-loop intervals, not CPU-cycle or compression-only measurements.

There are 21 rotated trials per case on one uncontrolled Apple Silicon Mac. The RF2 0.23 source and compiler are retained as explicit test fixtures; the controller rebuilds that historical generator before compiling the control. Both reference and candidate perform actual hashes on every iteration. A direct ARM SHA2 C implementation is included as a stronger control. A volatile function pointer prevents repeated empty-message calls from being hoisted or folded. It uses static scratch like RF2 and is not a runtime dependency.

| Bytes/hash | Hashes | RF2 0.23 ms | Candidate ms | CommonCrypto ms | Direct C SHA2 ms | Python/hashlib ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 20,000 | 5.990 | 0.847 | 3.261 | 0.298 | 5.089 |
| 64 | 20,000 | 6.065 | 1.093 | 3.419 | 0.624 | 6.028 |
| 4,096 | 4,000 | 6.105 | 5.140 | 5.512 | 5.028 | 6.179 |
| 32,768 | 2,000 | 20.601 | 20.175 | 20.387 | 20.137 | 20.755 |

The short-message task improves substantially over the prior RF2 version and beats the selected general-purpose library APIs. It still loses to direct specialised C. The larger messages converge near the same hardware cost. The candidate-minus-CommonCrypto paired bootstrap interval at 32 KiB includes zero; no reliable larger-message advantage is claimed. An earlier session had strong host-load variation and a candidate median above CommonCrypto; all local sessions remain in artifacts/sha-stream. The final receipt follows the reproducibility correction that rebuilds the historical generator from retained source. It is not the minimum selected across sessions.

[All final trials and hashes](SHA-PREPARATION-MEASUREMENTS.json). To reproduce with an explicitly built candidate compiler, run tools/benchmark-sha-steady.py with RF2_TEST_COMPILER. Clang is a development comparator, not an RF2 runtime dependency. No token, AI-generation, energy, universal speed or second-host result is inferred.

## Real application

examples/file-checksum.rf2 produces a SHA-256 digest or compares one supplied by the user. It reads a regular file up to 1 MiB, uses nonblocking/nofollow open, checks the opened descriptor's file type and closes it on tested ordinary success/error paths. It never writes the input. It rejects an oversized input, directory, FIFO or final-component symlink. A file changing while read is not an immutable snapshot. A digest comparison does not authenticate an author or trusted source.

The native local build is output/file-checksum-0.24. Invocation is `file-checksum-0.24 path [expected_hex_digest]`. stdout is the computed digest and newline. Exit 0 means success/match, 1 means mismatch and 2 means input/I/O/usage failure. This is a CLI capability, not a new MCP permission.

## Executed checks

- 8,280 independent byte-swap comparisons across widths and compiler modes; eight reserved-name/arity refusals.
- 144 changing-length digest comparisons within reused processes; 126 real file-utility cases.
- 150 full-digest checks qualify the stronger C control against hashlib.
- 5,120 ABI comparisons across intrinsic-only and actual-call functions, register/spill boundaries, nested calls and eight live caller locals.
- The existing 900 digest checks, 192 arbitrary compression cases, six refusals and assembly oracle pass again.
- Compiler fixed point, reference encoder, runtime corpus and SDK pass. Conditional-reduction, register-ABI and optimizer-control regressions pass without overwriting historical receipts.
- Guest 34 runs/77 refusals/23 mapping cases, trust 520, protocol 245 and the independent three-tool SDK pass. Disposable keys were removed.

## Failures retained and corrected

An initial byte-swap word encoded bit reversal rather than byte reversal; the first digest test caught it. A pure-call classification experiment spilled an eighth hot local and slowed the historical SHA source; larger frames now retain the eight-register strategy, and the final control uses the historical generator. The first direct C benchmark allowed repeated empty-input work to be hoisted; the opaque-call control corrects that. The CLI's first version treated an unwritten FIFO as an empty input; descriptor type validation fixes it. An invalid parent-directory import was refused and replaced by a valid local-segment import. Earlier artifacts remain local, not reclassified as passes.

The next performance target is the direct-C short-message gap. Another host and an independent compiler review are still needed. These improvements do not complete floating point, general ownership, concurrency, libraries or additional targets.

[Primitive/application verification](SHA-PREPARATION-VERIFICATION.json), [ABI cases](INTRINSIC-LEAF-VERIFICATION.json), [digest checks](SHA-PREPARATION-DIGESTS.json), [compiler](SHA-PREPARATION-COMPILER.json), [integration](SHA-PREPARATION-REGRESSIONS.json).
