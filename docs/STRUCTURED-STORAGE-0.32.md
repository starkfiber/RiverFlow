# Structured array storage and shared applications, development 0.32

Fixed-array payloads no longer consume one local-variable metadata slot per element. Arrays now occupy a separate, checked, per-function stack arena. This lets real applications use larger typed workspaces while keeping named-local metadata bounded.

A separate [native development bundle](../dist/0.32-candidate/README.md) includes both apps, their one shared source library, compiler and MCP runtime. [Fresh extraction and execution receipt](STRUCTURED-STORAGE-0.32-PACKAGE.json). Stable 0.17 downloads remain unchanged; the candidate is ad-hoc signed and not notarized.

## Implemented bounds

| Resource | Bound |
| --- | ---: |
| Declared u64 array |4096 elements |
| Declared u8 array |32768 bytes |
| Aggregate array payload arena per function |49152 bytes |
| Named and record/resource metadata slots |256 |
| Lowered frame reservation guard |65536 bytes |

The frame reservation also includes aligned scalar/record storage and applicable register saves. The usual 16-byte frame-pointer/link-register pair and transient expression/call stack use are additional. The current combined budgets make 51,200 bytes (51,264 with applicable register saves) the largest fixed reservation; the 65,536-byte emitter guard is not an executed claim for a presently constructible layout. Individual declarations do not override aggregate limits. These are explicit current budgets, not an unlimited heap or a guarantee against exhausting the process stack through arbitrary recursion.

Previously an array used a pointer local plus anonymous scalar slots for its payload. Main's arguments and other variables could therefore make a nominal 255-element declaration impossible to construct. Each owned array now uses one pointer slot and a separate payload offset. Ordinary record/resource layout is retained.

The constructor zeroes its rounded payload inside the current call frame. Packed byte arrays round allocation to 8 bytes; distinct payloads do not overlap. Borrowing, indexing checks, copy/escape restrictions and immutable view rules remain. Arrays remain excluded from scalar-template reuse and frameless functions.

## Larger frames must use legal machine instructions

The emitter materializes high and low address portions using legal ARM64 ADD encodings. Allocation proceeds in aligned steps of at most 4096 bytes, touching the newly reserved stack at each step. This is conservative on the qualified Mac's larger pages. High register-save offsets use a materialized base instead of overflowing the scaled-load/store immediate. Deallocation restores the complete frame reservation.

An independent test-only native probe reads SP and checks alignment/restoration. Its patched instruction bytes are checked against the system assembler; this instrumentation is not an RF2 source-language SP API. Actual tests exercise frames above 49,000 bytes and multiple recursive activations. No other OS/ABI, arbitrary-recursion safety or whole-language memory-safety result follows.

## Two applications, one source module

- [text-search](../examples/text-search/README.md): exact-byte match count and first offset.
- [log-scan](../examples/log-scan/README.md): matching lines, total matches and first matching line for supplied log/text input.

Both entry files directly import `examples/text-search/lib/search.rf2`. They use a caller-owned 4096-element u64 prefix workspace, supporting 4096-byte queries with a 1 MiB input budget. The shared-library test mutates one isolated library copy and demonstrates changed results in both apps while verifying canonical source remains unchanged. This is source-module reuse, not dynamic linking or a new framework.

Line scanning uses LF delimiters and retains CR in line contents. Byte matching is not Unicode normalization, regex or semantic search. Demonstration input and test fixtures are supplied programming inputs, not observed production incidents. This release does not establish a new speed, AI usage, energy or hardware advantage.

## Qualification

- [92 engine storage controls](STRUCTURED-STORAGE-0.32-ENGINE.json).
- [82 independent frame and boundary controls](STRUCTURED-STORAGE-0.32-REDTEAM.json), including actual SP probes, assembler comparison, nested/recursive arrays, high-offset saves, packed tails, aggregate-limit refusals, ownership/view restrictions and bounds-before-effect behaviour.
- [Existing array/application regressions](STRUCTURED-STORAGE-0.32-ARRAYS.json). The old 256-element refusal is intentionally replaced by 4097, and the formerly refused 255-element main allocation is now executed successfully. Named-scalar over-capacity still refuses.
- [Compiler reproduction, independent maintained encoder and MCP](STRUCTURED-STORAGE-0.32-COMPILER.json), plus [compact runtime checks](STRUCTURED-STORAGE-0.32-RUNTIME.json).
- [726 search API/CLI controls](STRUCTURED-STORAGE-0.32-SEARCH.json) and [406 shared-app controls](STRUCTURED-STORAGE-0.32-APPS.json).
- [ABI](STRUCTURED-STORAGE-0.32-ABI.json), [views](STRUCTURED-STORAGE-0.32-VIEWS.json), [cleanup](STRUCTURED-STORAGE-0.32-CLEANUP.json), [results/views adversarial controls](STRUCTURED-STORAGE-0.32-RESULTS-VIEWS.json), [target cache](STRUCTURED-STORAGE-0.32-INCREMENTAL.json), [function packs](STRUCTURED-STORAGE-0.32-PACK.json) and [actual default-size compiler store admission](STRUCTURED-STORAGE-0.32-STORE.json).

The signed default compiler image is 16,631,264 bytes, below the existing 16,777,216-byte snapshot limit with 145,952 bytes remaining. Compact builds remain preferable for development snapshots. This bound was not silently widened.

## Scope and remaining work

Qualified on one Apple Silicon Mac. The native backend emits Darwin Mach-O and uses the Darwin ABI; a Linux LXC does not make that binary a Linux program. Prime was not changed or used for this work. Linux qualification needs an actual target/backend and its own acceptance cases.

WhatIF's automatic web/backend runners do not cover native compiler frames. This work applies its boundary/invariant/replay discipline using explicit native controllers and actual independent agent review. It is not a built-in WhatIF engine result or external certification.

The first bootstrap comparison rejected compactly spaced assignments in the new compiler source because the maintained reference encoder expects spaced assignments. Source formatting was corrected and the independent check rerun. An early red-team harness assumed a named Mach-O text section; it was corrected to support RF2's actual LC_MAIN entry format. Neither is presented as a passing initial attempt or a compiler-codegen defect.

General heap transfer, richer structured values, concurrency, floating point, standard application libraries and additional targets remain separate work. No thesis, book or PDF was changed.
