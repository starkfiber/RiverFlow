# Local 0.23 candidate: direct ARM SHA2 compression

The large SHA gap was an instruction-selection and implementation gap. RF2 now emits an inline SHA256H, SHA256H2, SHA256SU0 and SHA256SU1 block kernel. The runtime calls neither CommonCrypto nor Python. These established processor instructions are available to other languages too. This is an RF2 implementation, not a new hash algorithm, transistor design or a comparison of human and AI intelligence.

These are historical local 0.23 measurements. Their implementation is included in the later 0.25 source candidate, published through the verified SFE browser session. Stable releases and downloads are unchanged.

## Contract and runtime selection

`sha256_blocks_armv8(state, input, count, constants)` is a trusted systems intrinsic. State contains eight native little-endian u32 words; constants contain 64 native u32 words; input contains count complete 64-byte blocks. State, constants and input must be valid nonoverlapping ranges. Caller establishes ARM FEAT_SHA256 before a nonzero call. The return is zero; the state is updated, while constants/input remain unchanged. A zero-block call does not read or write any pointer. Invalid pointers/counts are outside the trusted raw-memory contract, as with existing raw load/store operations. No bounded Core/MCP caller gains these effects.

The inline kernel uses caller-saved SIMD registers v0-v7 and v16-v18, scalar x0-x2, and no stack space or external calls. It byte-reverses message lanes, expands the schedule with SHA instructions and preserves chaining state across blocks. The exact instruction sequence is independently assembled in tests/standalone/sha256_blocks_armv8.s and compared with the emitted native bytes. The assembler is a development oracle, not an application dependency.

The SHA library queries Darwin syscall 274 for `hw.optional.arm.FEAT_SHA256`, checks query success, result length and value, then caches the selected path. Absence or query failure retains the 0.22 scalar implementation. Full input blocks use the native kernel; the final one or two blocks are padded in RF2. The existing shared scratch buffers remain nonreentrant. This does not establish a concurrency-safe crypto API, cryptographic certification or general memory safety.

## Executed checks

900 digest comparisons cover every length 0 through 139, padding/block boundaries and messages through 1 MiB, across default/optimized compilation and automatic, forced-software and failed-feature-query paths. Another 192 arbitrary-state/constant compression cases cover offsets 0 through 15 and zero through five complete blocks against an independent Python round implementation. Canaries, input and constants remain unchanged. A null-pointer zero-block probe passes. Six invalid programs refuse for reserved declarations, arity, record passage and live-view effects.

Native compiler self-generation, reference encoder agreement, the runtime corpus and official SDK pass. The authenticated guest suite passes 34 runs, 77 image refusals and 23 mapping cases. Trust tests pass 520 checks and protocol/key tests 245. The separate three-tool MCP SDK passes with server PATH=/nonexistent and a disposable test key removed afterwards. These are finite local checks, not independent academic approval or proof against all attacks.

## Final matched task measurements

21 rotated fresh-process trials per task follow one warmup per variant on one Apple Silicon Mac. Each hash consumes 32 KiB. Before each hash, the first input byte changes to the loop index modulo 256. Every final digest-byte sum matches the independent oracle. Process startup, feature discovery and initial file reading are included. C uses Clang O3, native CPU targeting and CommonCrypto; Python uses hashlib. Both libraries are allowed their established hardware acceleration.

| Hashes per process | RF2 0.22 scalar, ms | RF2 candidate, ms | C/CommonCrypto, ms | Python/hashlib, ms |
| --- | ---: | ---: | ---: | ---: |
| 50 | 35.592 | 2.556 | 2.527 | 13.383 |
| 2,000 | 1325.124 | 22.720 | 22.458 | 33.288 |

These medians support a large improvement over RF2's scalar source and a win over the Python task in this experiment. They do not support a reliable win over C. The larger-task C median is about 1.2% lower; the paired candidate-minus-C median difference is 0.276 ms, with an exploratory bootstrap interval of 0.129 to 0.490 ms. The smaller-task paired interval includes zero. One exploratory earlier run favoured RF2; it is not selected as the headline result.

The comparison measures complete task processes with different I/O/runtime implementations. It does not isolate hash throughput, CPU cycles, instruction latency, energy, model generation or billed tokens. It cannot establish language-wide speed. The measurement controller embeds the matched harnesses and fixture recipe and retrieves the frozen 0.22 SHA source from commit 3ecbf7f4ab1fb7c262810cb39ddb784613186ebf. The final receipt retains every trial and source/binary hashes.

## Rejected approaches and corrections

An unrolled scalar helper plus full-block copy avoidance did not improve the batch. A later experiment keeping constants in vector registers also failed to establish a benefit and added register-preservation complexity; it was rejected. One exploratory controller initially retained the unrolled input path while labelling it SHA2. Its source hash exposed the error; that measurement is excluded. An assembler-check assertion also initially expected one inline kernel, although the probe contained three calls; the count was corrected after confirming byte-for-byte agreement. The earlier records remain local. None is reported as a successful speed improvement.

The next experiment should compare sustained in-process throughput with an equally direct hardware kernel, then repeat on another host. Wider types, heap ownership, concurrency, libraries and new targets remain separate language work. A specialised SHA result does not close those gaps.

## Evidence and sources

[Digest and raw compression checks](SHA-ACCELERATION-VERIFICATION.json), [matched measurements](SHA-ACCELERATION-MEASUREMENTS.json), [compiler checks](SHA-ACCELERATION-COMPILER.json), [application/MCP regressions](SHA-ACCELERATION-REGRESSIONS.json), [experiment ledger](SHA-ACCELERATION-EXPERIMENTS.json).

Instruction semantics: [Arm Neon Intrinsics Reference](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html), SHA256H/H2/SU0/SU1 entries. Darwin query ABI: [Apple XNU syscalls.master](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/syscalls.master), syscall 274. These sources support instruction/ABI definitions, not RF2 performance claims.
