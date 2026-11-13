# Local RF2 0.22 candidate: native rotation and a measured SHA improvement

This is a development source candidate, not a stable release. The selected SFE connector returned authenticated login `starkfiber`, account ID 6210371, before publication. No old-account credential fallback is permitted.

The trusted systems compiler now lowers `ror32(value,amount)` directly to ARM64 RORV W0,W0,W1. The input is reduced to its low32bits, the amount is modulo32, and the result is zero extended to the existing u64 scalar ABI. This is an established integer instruction, not floating point, new transistor logic, a new cryptographic construction or a new Core/MCP effect. Pure arithmetic can consume scalar view reads; nested calls retain the existing view restrictions.

The SHA implementation replaces its repeated rotation helper calls with this primitive. It otherwise retains its existing schedule, constants, padding and round arithmetic. The previous SHA source and frozen0.21 benchmark binaries remain local controls. Native compiler self-generation/reference byte comparisons and the original Core/runtime SDK passed.

## Correctness and integration

The native default and optimized programs each passed3989runtime rotation pairs, including zero/full-width shifts, high-word inputs, every single-bit position and seeded random values. Four invalid-name/arity cases refused. Thirty-four SHA messages across both modes matched Python hashlib at padding boundaries and sizes up to65536bytes. The authenticated guest suite passed34runs/77refusals/23mapping scenarios; trust520, protocol245 and the independent three-tool MCP SDK passed. These are finite local checks, not whole-language or cryptographic certification.

## Fresh matched measurements

Twenty-one rotated fresh-process trials per task, after a retained warmup, on one Apple Silicon Mac. Same file, exact output oracle and frozen0.21 binaries; process startup and file read are included. The batch varies the first byte for each of50hashes of32KiB. C/CommonCrypto and Python/hashlib use different optimized implementations.

| Task, median ms | Frozen RF2 0.21 | Rotate candidate | Clang/CommonCrypto | Python/hashlib |
| --- | ---: | ---: | ---: | ---: |
| One32KiB hash | 2.871 | 2.366 | 1.831 | 11.515 |
| Fifty hashes | 56.983 | 35.345 | 2.556 | 13.102 |

The candidate batch median is about38%below the frozen RF2 baseline. Both library comparators still beat it. The one-file advantage over a fresh Python process is not evidence of a faster hash implementation. The raw ranges and every retained trial are in [the measurement receipt](SHA-ROTATE-0.22-MEASUREMENTS.json). There is no new energy, billed-token, complete AI-task or universal language-speed result.

This narrows a measured performance gap. It does not implement floating-point types, a general heap, ownership transfer, concurrency, comprehensive libraries, x86 or all assembly instructions. The next useful work is profiling the remaining SHA schedule/round costs and separately specifying the next numeric type, without using one specialized kernel as a whole-language score.

[Rotation/SHA checks](ROTATE32-0.22-VERIFICATION.json) · [Compiler](COMPILER-0.22-REGRESSION.json) · [Integration](ROTATE32-0.22-REGRESSIONS.json).
