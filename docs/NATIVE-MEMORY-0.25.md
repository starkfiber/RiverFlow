# Native memory and SHA preparation: 0.25 source candidate

This candidate reduces repeated SHA setup and call overhead on the measured Apple ARM64 host. It does not change SHA-256, establish a new complexity class or demonstrate a universal advantage over C. Stable downloads remain unchanged.

## Mechanisms and contracts

`fill_zero(dst, bytes)` writes exactly the requested bytes. `bswap32_copy(dst, src, words)` reverses bytes within each four-byte word. Both accept unaligned ranges; zero counts do not dereference pointers. Copy supports disjoint ranges or exactly in-place operation. Partial overlap is outside its raw contract. The optional literal-size paths are bounded at 256 bytes or 64 words.

`sha256_chain_armv8` chains two complete-block spans without restoring SIMD state between them. Two zero counts perform no pointer reads. Nonzero spans require valid memory and the ARM SHA256 feature. These are raw operations, not general memory ownership or permission enforcement.

Optimised scalar frame omission is restricted to proven call-free helpers with at most seven named scalar local slots, no structured values and no cleanup. Other functions retain their frames. Direct argument register placement applies only to the narrow fixed-arity memory operations with simple scalar locals or literals. Complex expressions retain normal evaluation and checks. Broader argument lowering failed compiler self-generation and was reverted.

The SHA wrapper caches feature discovery and constants, uses bulk zeroing and vector byte conversion, and keeps the hot helper within the scalar register budget. Shared scratch remains nonreentrant. Independent concurrent states are not implemented by this interface.

## Why it helps

A useful cost decomposition is `T = Tsetup + B*Tblock + Tformat`, where B is the number of complete blocks. Removing repeated setup matters most for short messages. SHA compression and its modular arithmetic are unchanged; work remains linear in input length. Amdahl's standard model, `S = 1 / ((1-p) + p/s)`, explains why improving one part cannot remove unrelated costs. No fraction p was measured or fitted here. This is an application of established optimisation ideas, not a claim that earlier engineers missed a new law.

Primary background: [Amdahl, 1967](https://doi.org/10.1145/1465482.1465560) and [Arm Advanced SIMD intrinsics](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html). RF2's contribution here is the implemented compiler integration, guarded lowering and reproducible evaluation.

## Repeated complete hash API measurements

Twenty-one rotated trials after warmup, one Mac, milliseconds. Startup, input loading and first feature/setup discovery are excluded. All output digest sums were checked. Lower is better.

| Bytes per hash; hashes | RF2 0.24 | Candidate | CommonCrypto | Direct ARM C | Python hashlib |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0; 20000 | 0.845 | 0.355292 | 3.246375 | 0.302167 | 5.052083 |
| 64; 20000 | 1.103417 | 0.666042 | 3.397958 | 0.627375 | 5.994875 |
| 4096; 4000 | 5.118958 | 5.008208 | 5.474 | 5.005875 | 6.233167 |
| 32768; 2000 | 20.260250 | 20.145458 | 20.410458 | 20.185792 | 20.866291 |

The direct C control remains about six percent faster on the 64-byte case. Larger-message candidate-minus-C paired intervals cross zero. This does not establish a reliable larger-message win. Small literal unrolling alone did not establish a useful overall hash improvement.

## Actual project file workload

Ten source, document, SVG and generated object snapshots, each at most 1 MiB, were checked through real CLI processes. The whole task includes startup, file metadata, reading, hashing and output with a warm operating-system cache. Corpus medians were 15.739418 ms for RF2 0.24, 16.155835 ms for the candidate and 16.479207 ms for C. Paired intervals cross zero against both controls. No reliable end-to-end improvement was demonstrated. A warm-loop improvement must not be substituted for this result.

## Verification and retained failures

Passed: 4288 memory comparisons, 648 literal-size comparisons, 12 memory refusals; 672 two-span chain cases and five refusals; 8280 byte-swap comparisons, 144 reused-state digests, 126 CLI cases, 150 C full-digest checks and eight application refusals; 5120 ABI cases; 900 SHA cases, 192 arbitrary compression cases and six refusals. Compiler fixed-point, reference/runtime, guest, trust, protocol and independent MCP SDK checks also passed locally. These are finite tests, not a proof of all programs or hardware.

Retained failures include the reverted general argument-register experiment and unsuccessful setup/unrolling attempts. Earlier corrected byte-swap encoding, FIFO handling and register-spill faults remain documented in the 0.24 record. No second-host, energy, token-billing or AI-task benefit is claimed.

## Evidence and reproduction

- [Warm API trials](MEMORY-0.25-STEADY.json), [whole-file trials](MEMORY-0.25-FILES.json), [paired analysis](MEMORY-0.25-ANALYSIS.json)
- [Memory](MEMORY-0.25-VERIFICATION.json), [two-span chaining](MEMORY-0.25-CHAIN.json), [application](MEMORY-0.25-APPLICATION.json), [ABI](MEMORY-0.25-ABI.json), [SHA](MEMORY-0.25-DIGESTS.json)
- [Compiler](MEMORY-0.25-COMPILER.json), [integration](MEMORY-0.25-REGRESSIONS.json)
- Controllers: `tests/standalone/memory_intrinsics_verify.py`, `sha_chain_verify.py`, `sha_preparation_verify.py`, `sha_acceleration_verify.py`; `tools/benchmark-sha-steady.py` and `benchmark-checksum-files.py`.
- Retained comparator sources: `tests/fixtures`. Development controllers use Python and C; generated RF2 programs do not require them.

Next: qualify another host, independently review raw-memory contracts, reduce the remaining short-message gap without weakening checks, and improve end-to-end workloads before making broader performance claims.
