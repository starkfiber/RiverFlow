---
name: rf2
description: Check and execute RiverFlow Core/compact programs, lower checked kernels, use the versioned attendance exporter, and develop native compiler evidence.
---
# RiverFlow RF² 0.17

Use rf2_status first. Read docs/NATIVE-CORE.md and docs/STANDALONE.md for current profiles/effects. Nine native tools exist: rf2_status, rf2_check, rf2_run, rf2_lower, attendance_export, invoice_total, invoice_prepare, invoice_apply and invoice_release. Users require no Node/npm/Python/C++ runtime. The host provides AI intelligence; the executable has no embedded model.

## Core and compact source

RF2_U32_CORE_V0 supports ADD, MUL, LOAD, POPCOUNT, NONZERO, acyclic named scalar helpers, forward calls and bounded non-nested main loops. All functions are checked. Parameters/indices are immutable; loop-local values do not escape. Checked and wrapping u32 semantics are explicit. Core can only read the supplied array. Unknown effects, types, recursion and exceeded limits reject.

Compact V1 remains `rf2 v1 checked` or `wrap`, followed by `sum input`, `squares input`, `bits input` or `nonzero input`.

Use rf2_check/rf2_run with supplied text/data. Native run executes bounded IR; do not label every run as a separately compiled kernel. rf2_lower returns systems-profile kernel source only. It neither compiles nor writes a file. The explicit tools/build-core.sh route combines a trusted harness, native compiler and OS signing to create an ARM64 executable. General systems source is never admitted as Core or executed over MCP.

## attendance.local@1

attendance_export takes at most 1,000 records, each exactly student_id/date/status. IDs are constrained ASCII identifiers, dates canonical valid Gregorian YYYY-MM-DD, state present/absent/late. Duplicate student/date records reject. The tool returns CSV, counts and a byte fingerprint; no filesystem path or permission argument is accepted.

The CLI `rf2 attendance records.json new.csv` performs an explicitly requested file export, refuses existing paths/symlinks and validates before creation. Do not invent student records or field results. Included TEST fixtures are programming inputs only. Counts are computed through the versioned compiled Core kernel. Read the capability README before use; do not claim an authentication system or a full school app.

## Native builds and evidence

The systems compiler reproduces its own bounded source without Python. tools/build-runtime.sh composes the ten runtime modules; compiling native/rf2.rf2 alone is no longer a complete build. The historical Python seed and JS/C references remain development oracles, not user runtime dependencies. Source hashes establish byte identity, not independent approval or process isolation.

The plugin uses RF2_BIN or output/bin/rf2 and never silently builds/downloads/falls back to Node. Fresh checkouts need an explicit native binary. Current qualification is on Apple Silicon Mac; normal OS signing remains required. No universal speed, energy, token-saving, phone or fieldwork claim is established. Preserve failed tests and private data locally; do not put participant records in public releases.

## Compact application plan

RF2_APP_V1 admits `rf2 app v1 invoice total currency MYR tax 600 bps` with ASCII whitespace, exact order, three uppercase currency letters and canonical 0..10000 basis points. Use invoice_total with plan and lines, or explicit CLI `rf2 app plan.rf2 lines.json`. Read capabilities/invoice.total.v1/README.md. Lines contain exactly positive integer quantity and u32 unit_cents, at most 1000 lines. Checked line/subtotal/total limits and invoice-level half-up rounding apply. No fractional quantity, discount, tax-law determination, payment, ledger or file creation is implemented. Do not invent those effects.

Measurements in docs/CAPABILITY-MEASUREMENTS.md are mixed. The native invoice path is slower than the JS comparator for larger tested inputs. The 19-token plan costs more encoded interface tokens than direct configuration across the measured 20 calls. These are exact tokenizer fixture counts, not billed model usage or full-task savings. Preserve the raw results and do not turn compact syntax into an unmeasured advantage claim.

## Prepared plans and local workspace

Read docs/PREPARED-PLANS.md before reuse. Prepare an explicit plan, inspect returned currency/tax rules, apply to fresh lines, then release. Handles are immutable, bounded to 32 process-local slots, not authentication. Discard handles on reconnect. They grant no file or network effects. Internal OS entropy initializes a process-specific handle mask; no caller-controlled path is accepted.

Read docs/INVOICE-WORKSPACE.md for explicit CLI-only invoice save/inspect/set/remove/pdf. Each edit/export names a new file, refuses existing targets/symlinks and recomputes checked totals. This CLI is file-based. Release 0.9 also has an explicit graphical editor; neither route is a legally complete invoice/accounting service. All user runtime document/PDF operations run in RiverFlow. Test/publishing tools in other languages remain development dependencies.

0.8 measurement receipts compare final binary with frozen 0.7 and the JS reference. Reuse setup can cost more for short sessions. State exact measured scope; encoded fixture savings are not actual billed AI usage or universal acceleration. Do not inherit historical measurement values as permanent scores.

## RiverFlow Studio and systems platform ABI

Read docs/GRAPHICAL-EDITOR.md and docs/PLATFORM-ABI.md. Launch `rf2 editor` or RiverFlow Studio.app for a private loopback browser workspace. The RF2-compiled controller renders standard HTML forms, checks revisions and exact cents, and handles document upload/download and PDF generation. The browser displays the interface; this is not an AppKit widget window. CLI-only launch has no automatic browser effect unless --open is supplied. Graphical effects are not new MCP tools.

The trusted systems profile provides syscall6 and fork_process. These compile to ARM64 machine instructions with Darwin-specific ABI handling, not portable Core effects. Never admit raw systems code through the bounded MCP checker. Nine MCP tool names and schemas remain unchanged from 0.8.

The 0.9 receipt reports similar MCP invoice performance to 0.8 and no encoded token reduction for matched prepared exchanges. GUI HTTP timings exclude browser layout. Read docs/STUDIO-MEASUREMENTS.md before citing numbers. No billed model usage experiment, universal speed claim, x86 backend or arbitrary Python/C++ compatibility is established.

## Modules, records and compact machine clients

Read docs/MODULES-TYPES.md, docs/COMPACT-MCP.md and docs/LANGUAGE-MEASUREMENTS.md. The systems compiler supports explicit local use imports, nominal records of u64 fields and typed borrowed record parameters. Build through tools/build-program.sh; no imported code is automatically run. At most 32 files, 16 active traversal levels, 32 record types, 16 fields per record and 256 local slots per function. Imports share a namespace and resolve from the entry directory. Trusted source compilation is CLI-only; do not pass systems/modules source to bounded Core tools or infer filesystem containment.

Use examples/workload/main.rf2 for a real CSV workload analyser, independently checked for input-order deadline accounting. It is not a measured OS scheduler or claim of optimal policy. Use --opt explicitly for the tested numeric-right-operand machine-code lowering. The release runtime uses that option; default compiler output retains the previous path.

rf2 mcp --compact omits redundant successful check/run summary text only. All structured results, schemas and errors remain. Text-only clients should retain default mode. Set RF2_MCP_COMPACT=1 for an explicitly opted-in plugin launcher. Measured smaller transcripts do not prove smaller provider bills or faster AI generation. The related-project review is static and never substitutes for executed target comparisons.

## Optional native optimiser, 0.11

Read docs/NATIVE-OPTIMIZATION.md and versioned receipts. --opt includes leaf-aware register locals, direct arithmetic, loop rotation, restricted expression coalescing and guarded u32 word selection. An exact side-effect-free periodic masked-sum recurrence can use fixed-size arithmetic. Similar-looking loops with unsupported masks, comparisons or effects must retain the ordinary path. Raw systems compilation remains CLI-only; bounded Core/MCP authority is unchanged.

The 20 million-step eligible reduction improved from 24.878 ms in 0.10 to 1.842 ms, versus 3.841 ms for Clang's loop in one matched runtime-input run. Mixed arithmetic medians were 22.496 ms RF2 versus 22.232 ms Clang; branch-heavy code remained 20.216 ms versus 6.501 ms. The equally specialised C formula and startup-sensitive smaller cases remain visible. Cite exact scope; no global speed, novel mathematics, AI inference or universal exponential performance claim is established. No new token-saving measurement is claimed for 0.11; preserve the separate 0.10 compact-MCP result as historical evidence.

## Checked arrays, 0.12

Read docs/CHECKED-ARRAYS.md. This feature is included in 0.12. The new compiler supports nominal fixed u64 arrays, zero initialization, typed borrowed parameters, .length capacity and bounds-checked indexing in the trusted systems profile. Owned arrays remain function-local, with no ordinary copy/rebind/return or raw-intrinsic passage. Runtime bounds failure prints RF2 bounds and exits2, before a write RHS runs. This is not recoverable error handling, heap ownership, full memory safety, concurrency or Core/MCP permission expansion.

Use examples/latency/main.rf2 for a complete supplied-sample summary with explicit lower-median/nearest-rank percentile rules. It does not measure a clock. Reproduce the new compiler from the frozen native release, then build/run as documented. Preserve existing release receipts. Launch-inclusive small-input timing differences do not establish general speed or isolated check cost. Current research checks and roadmap remain separate from shipped platform support.

## Text, bytes and recoverable libraries, 0.12

Read docs/TEXT-BYTES.md. Packed nominal u8 arrays and typed read_bytes/write_bytes are trusted systems-compiler capabilities, never raw Core/MCP effects. Ordinary indexing/value errors trap; the byte library provides explicit recoverable Outcome records. Callers must inspect status and handle short I/O. Streaming UTF-8 audit has a documented invalid-grouping policy, ASCII whitespace counts and a 1 MiB app cap; it is not normalization or grapheme handling. Named input descriptors close on tested normal/error paths; no general RAII, exception, heap-ownership or concurrency model is claimed. Use examples/text-audit/main.rf2 and exact verification receipts. No new speed or token result is established.

## Typed results and immutable byte views, 0.13

Read docs/RESULTS-VIEWS.md. Result declarations have scalar ok/err payloads; result-returning functions require explicit final root return and calls require exact exhaustive handle syntax. Payload bindings are immutable and arm-scoped. This is not generic payloads, result locals/parameters, exceptions or exhaustive numeric error-code checking. Uninitialized/block-escaped scalar reads now refuse, including optimizer paths.

Function-local byte views are zero-copy, nonescaping and read-only. Multiple windows may coexist; after the first, all calls and array element updates reject until return, including aliased owners. Bounds use subtraction and view length. These are byte views, not automatic UTF-8 validation or logical content counts. Creation/access traps remain distinct from explicit recoverable guards. Use examples/number-audit/main.rf2, preserve adversarial receipts and do not claim a full borrow checker/security proof. Existing nine bounded MCP effects remain unchanged; raw systems source stays CLI-only. No new speed/token claim.

## Unicode scalar views and deferred cleanup, 0.14

Read docs/UNICODE-CLEANUP.md. textview values validate strict UTF-8 over the selected byte range, expose .byte_length and scalar .length, and index scalar values. Scalar counts are not grapheme counts; no normalization or constant-time indexing is claimed. Invalid construction/index traps; the real app prevalidates for recovery. Existing immutable function-wide view freeze remains.

Function-level defer close(expression) captures once and automatically attempts close on ordinary returns/fallthrough, preserving scalar/typed results. Up to16 registrations, reverse order, two hidden slots each. This is best-effort close, not linear ownership, arbitrary destructors or cleanup on fatal traps/exit/signals. Raw descriptor early-close/reuse remains unsafe. Do not register borrowed stdin. Use examples/unicode-lines and finite native/oracle receipts. No new MCP effects, speed or token claim.

## Owned files and cleanup errors, 0.15

Read docs/RESOURCE-OWNERSHIP.md. resource File(IO) plus own file=File(path,flags,mode) acquires internally, propagates open failure through a same-IO result function, and exposes no descriptor. Owners cannot be values, copied, rebound, passed or returned. read_owned/write_owned return handled IO outcomes; release consumes on either outcome and disarms before close. Source consumption is conservative across branches; repeated loop release is runtime-guarded.

Automatic cleanup on ordinary returns reports err(65536+errno) if the primary result was ok, preserves primary err and reports only the first cleanup failure. Legacy defer remains best effort. Raw syscalls, traps, exit and signals remain outside checked ownership. No move/transfer, heap or async ownership is established. Use examples/hex, docs/BYTE-REFERENCE.md and docs/CAPABILITY-MAP.md; nine MCP schemas unchanged and no new speed/token claim.

## Logical guards, 0.16

Read docs/LOGICAL-GUARDS.md. Trusted systems source supports true/false and all(a,b), any(a,b), not(a). Scalars use zero/nonzero truthiness and normalize to0/1. all/any short-circuit at runtime, but skipped operands remain statically checked. Bitwise operators remain eager. Pure logical intrinsics may read live views; actual calls in operands still obey view freeze. These five names are now reserved. No distinct Boolean type, Core/MCP grammar/effect expansion or new speed/token result. Use examples/file-kind for owned read-only signature inspection, not full file validity or security.

## Growable bytes and structured success results, 0.17

Read docs/STORAGE-RESULTS.md. vector Bytes(IO,max) requires canonical decimal 1..1048576. own b=Bytes() reserves virtual address space with PROT_NONE; reserve/push enable a prefix before committing logical capacity. Stable address does not mean an unbounded heap, relocating malloc or measured physical commitment. buffer_reserve/push/get/clear return handled scalar IO outcomes; indexes and properties check logical bounds and lifetime. Release/automatic unmap use the owned cleanup protocol. No vector copy, passing, return, views or raw-pointer extraction.

result Report(Stats,u64) supports 1..4 scalar fields in a nominal record success. return ok(local_record) copies x1..x4; the annotated ok summary:Stats handler copies into its own frame. Payloads are immutable and arm-scoped; passing the whole payload to a mutable helper refuses, while scalar field arguments are allowed. Existing scalar ABI is unchanged. Owners require scalar IO, so a structured wrapper calls a scalar IO helper before returning a record. No generic structured errors, deep ownership or general FFI claim. Use examples/buffer-audit and qualification receipts. The external review brief and second opinion distinguish baseline, proposals and qualified evidence. Nine MCP schemas remain unchanged; no new speed/token claim.

## Evidence Contract research candidate

Read docs/EVIDENCE-CONTRACT.md, docs/FIVE-HYPOTHESES-REVIEW.md and docs/TOP-TEN-LANGUAGE-AUDIT.md. The RF2E1 native byte-plan runner is a separately built research example, not a 0.17 release asset or new MCP tool. It supports bounded checked ADD/XOR/reversal with permissions, abstract work limits, private reference/candidate execution, full-byte agreement before commit, source-bound SHA-256 receipts and plan-plus-JSON replay. Use tools/build-contract.py with a new output path to refresh source identity and capture compiler/executable hashes. The standalone result needs no Python/Node runtime; the builder and independent test controllers are development tools. Do not admit systems source via Core MCP or claim source receipts authenticate the running binary, novel physics, universal security or performance. Retain prior-art and finite-test limits.
