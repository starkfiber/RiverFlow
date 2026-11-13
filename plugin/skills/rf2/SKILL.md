---
name: rf2
description: Check and execute RiverFlow Core/compact programs, lower checked kernels, use the versioned attendance exporter, and develop native compiler evidence.
---
# RiverFlow RF²: stable 0.17 and development 0.18

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

RF2C1 research replay: `rf2-contract capsule planfile` emits exact plan bytes, source ID and receipt; `rf2-contract replay capsulefile` validates them in a fresh process. The normal0.17 MCP schemas remain unchanged. Read docs/CONTRACT-REPLAY-RESEARCH.md and the verification/overhead records. Shared defects escaped agreement in executed negative controls; a recomputed unsigned receipt was accepted. Never call receipts authenticated, confidential or tamperproof. Idle-FIFO waiting was fixed with Darwin O_NONBLOCK, not a universal I/O timeout. Singlebyte exhaustive coverage is not all-plan verification; measured dual checking cost exceeded the reference-only harness.

## 0.18 development trust service

Read docs/TRUST-0.18.md and its verification/measurement records. The original nine native tools remain in the stable server. A separate native service exposes contract_status, contract_run and contract_verify for bounded RF2E1/RF2A1 only. It uses an administrator-selected32-byte mode0600key loaded at startup; no caller key/path override or automatic key generation is permitted. The launcher uses RF2_TRUST_BIN and RF2_TRUST_KEY_FILE, with documented local defaults. Existing0.17plugin installations need reload/reinstallation to activate the new source configuration. Do not claim these tools are already connected merely because the binaries exist.

The separate verifier has its own parser and original-element trajectory algorithm, but shares RF2 compiler/cryptographic helpers. HMAC-SHA256 is shared-key authentication, not a public signature, nonrepudiation, replay protection or hardware attestation. Key holders can forge tags. A shared three-path defect escaped the executed control. The optimized eligible XOR/reversal path retains nonzero-ADD fallback and abstract work semantics. Engine timings exclude independent checking, hashing and transport; complete MCP timings are separate. Retain raw failures, finite-test boundaries and stable0.17release identity.

## 0.19 development foundation

Read docs/FOUNDATION-0.19.md. The trusted systems compiler supports platform_call("Hypervisor", literal_symbol, scalar_arguments) for a finite allowlist and exact arities. It emits direct Mach-O bindings to the system Hypervisor framework. It is CLI-only, not a Core or MCP hardware effect. The guest foundation manages code/data permissions, vCPU registers, expected exits and explicit cleanup; it runs a fixed three-instruction ARM64 payload, not Linux. Apple supplies hardware virtualization. The explicit entitlement is required.

The separate rf2-wasm native tool encodes checked CoreV0 into a WASM1 module without OS imports, with fixed memory and run/status/work exports. --generic preserves the non-specialized comparator. Only a structurally matched sum gets guard hoisting; preserve overflow and work counts. Raw systems/FFI, DOM, WASI and threads are not this backend. Browser host glue and limited compatibility JavaScript remain explicit. No physical Android4.1 qualification exists.

Nine existing Core/application MCP tools and the three contract tools retain their authority. Do not silently run guests or raw systems programs over MCP. Worker code is locally tested, not cloud-deployed; no inference/model training or Redis hive is configured. Read docs/FREE-CLOUD-0.19.md before using free services, record actual provider usage and never upgrade a plan automatically. Stable0.17 and frozen0.18 candidate artifacts remain unchanged.

## VM owners and admitted images, 0.20 development

Read docs/VM-OWNERSHIP-0.20.md and examples/vm-runner/README.md. resource Machine(IO,vm) and CPU(IO,vcpu) are function-local, noncopyable owners with checked parent release and reverse ordinary-return cleanup. Typed operations require IO handling. Cleanup errors replace success and preserve primary errors; raw platform operations, fatal traps and signals remain outside the guarantee. Mapped buffers remain manually managed.

The native CLI loader validates exact RF2G020 headers, bounded entry/code and every admitted instruction before VM acquisition. It is not an arbitrary ARM64/ELF/Linux loader or signed image format. The admitted subset cannot modify its virtual timer or X2. Timed loops return a platform virtual-timer exit using the mach_absolute_time clock domain, while explicit pre-entry cancellation uses hv_vcpus_exit. Host scheduling excludes hard real-time guarantees; wider guest instructions require fresh cancellation analysis. No Core or MCP hardware authority is added. Existing nine Core tools and three separate contract tools remain unchanged. New evidence is local, not a relabelled hosted0.19 run; stable0.17 and frozen0.18 archives remain unchanged. No speed, energy or token claim.

## Owned mappings and authenticated boot contract, 0.21 development

Read docs/BOOT-CONTRACT-0.21.md and docs/BENCHMARKS-0.21.md. resource Pages(IO,mapping) owns bounded host allocation and guest mapping as a VM child. Static/runtime guards prevent mutation or release with a live CPU and prevent compatibility VM-map calls bypassing owned children. Ordinary cleanup unmaps guest before host. Failed guest unmap deliberately retains host memory; raw operations, fatal traps and signals remain outside safety. No general move/borrow or physical page-release proof.

The native guest CLI generates keys, seals and verifies RF2A021 shared-key HMAC-SHA256 images, then enforces a fixed memory/register/slice contract. Valid MAC does not override policy. Keys remain local owner-only regular files; no public signatures, anti-rollback, measured hardware boot or Linux/ELF support. Replay is allowed. Current admitted exit is HVC #1; a retained HVC #0 counterexample invalidated broader register-preservation assumptions. New hardware authority remains CLI-only, never Core or MCP.

Fresh matched task, HTTP and MCP reports retain the fifty-hash loss versus Python/hashlib and Clang/CommonCrypto. No 100% Python/C/assembly parity, universal speed, actual billed-token or full AI-task claim. The19report inventory distinguishes historical measurements from reruns. Native artifact metadata is not complete REA API/runtime coverage, and WhatIF source scanning skips RF2. Stable packages and the exact0.18archive remain unchanged.

## Local native rotate candidate, 0.22

ror32(value,amount) in trusted systems source emits ARM64 RORV over low32input bits with amount modulo32 and zero-extended u64 result. It is pure arithmetic, not floating point or a new Core/MCP effect. SHA uses the primitive instead of helper calls.3989pairs per compiler mode,34SHAcases and existing guest/trust/SDK checks passed. The selected50-hash batch median fell56.98to35.35ms in21matched trials; Python/hashlib and C/CommonCrypto still win that batch. Read docs/ROTATE32-0.22.md. No broad parity, energy, fullAI-task or billedtoken claim.

SFE GitHub identity must be verified before remote writes. The explicitly selected SFE connector returned `starkfiber`, account ID 6210371, before publishing this source candidate. Stable downloads remain unchanged. Never use the old credential workaround or treat an installed SFE repository as proof of the acting account.

## Local 0.23 SHA acceleration candidate

Read docs/SHA-ACCELERATION.md. The trusted systems intrinsic sha256_blocks_armv8(state,input,count,constants) emits an inline ARM SHA2 block kernel. Nonzero count requires verified FEAT_SHA256 and valid nonoverlapping raw ranges; it is not a checked-memory/Core/MCP effect. Zero count returns zero without dereferencing pointers. The library queries the Darwin feature and retains the scalar implementation when absent or the query fails. Shared named scratch buffers remain nonreentrant. Existing SHA instructions and algorithm are prior art, not new cryptography or transistor design.

Final local 21-trial process medians: 50 x32KiB hashes, candidate2.556ms versus scalar35.592ms, CommonCrypto2.527ms and Python/hashlib13.383ms; 2000 hashes22.720ms versus1325.124ms,22.458ms and33.288ms. C retains a small lead in the larger task. No reliable C win, universal speed, AI intelligence or token-billing result. These local measurements are historical; the implementation is integrated in the later source candidate. Stable downloads remain unchanged. Verify actual SFE identity for every publishing route.

## Local 0.24 preparation and call-classification candidate

Read docs/SHA-PREPARATION.md. bswap32 reverses the low four bytes and zero-extends; bswap64 reverses all eight. They are pure trusted arithmetic, including scalar view reads, not new Core syntax/effects. A narrow inline-intrinsic allowlist permits caller-saved locals for functions using at most seven slots; real calls, platform calls, syscalls and owned cleanup retain conservative preservation. Larger frames retain eight callee-saved local registers.

SHA constant initialization is cached; padding uses word stores and digest/length conversion uses byte swaps. Existing shared scratch remains nonreentrant. In-process warm-loop measurements exclude startup and initialization. The 64-byte task measured1.093ms/20,000 calls versus0.23's6.065ms,CommonCrypto3.419ms,and direct specialised C0.624ms. Retain stronger-control losses and noisy32KiB results. No universal speed or AI/token claim. examples/file-checksum.rf2 is a trusted read-only regular-file checksum CLI with a1MiB limit, nofollow/nonblock open and fstat check; exit0 success/match,1mismatch,2error. It does not authenticate origin or prevent concurrent file mutation.

## 0.25 source candidate: memory operations and split-span chaining

Read docs/NATIVE-MEMORY-0.25.md. fill_zero(dst,bytes) and bswap32_copy(dst,src,words) are trusted raw memory intrinsics, with zero-count no-op, unaligned access, disjoint or exactly in-place word copy; partial overlap is outside contract. They remain blocked under live views and do not expand Core/MCP effects. Optimized small literal ranges may unroll only after ordinary argument/type checks and evaluation. A narrow direct-argument path covers only fixed-arity memory calls with scalar locals/literals; complex arguments retain ordinary evaluation.

sha256_chain_armv8 handles two ranges of complete SHA blocks in one state chain without concatenating. Nonzero work requires FEAT_SHA256 and valid raw ranges. Strict call-free scalar functions with at most seven live slots, no structured locals/results or cleanup may omit a stack frame in --opt. This is standard native-code optimisation, not new physics or a complete ABI proof. Broad generic argument lowering failed self-generation and was excluded.

Final short-message medians0.666ms versus0.24's1.103ms and directC0.627ms; direct C still leads byabout6%. Ten-file end-to-end corpus has no reliable advantage against either previous RF2 or direct C. Warm-loop and whole-process results are distinct. No language-wide, energy, AI-generation or token-billing claim. SFE browser identity was verified before source publication; terminal pushes stay locked without their own verified credential.

## 0.26 source candidate: native target-level incremental builds

Read docs/INCREMENTAL-BUILDS.md before using rf2-build. This is explicit trusted local CLI compilation, not a new bounded MCP effect. Select the existing native compiler, source entry, new output path and existing private cache directory. Actual compiler bytes, options, builder-source identity and every raw transitive dependency bind the key. Hits verify the complete cached image. Misses compile captured source and compiler snapshots. Existing outputs refuse; --clean bypasses image reuse.

Reuse is whole-target, not function/object/AST reuse. The native compiler and nine stable MCP tools remain unchanged. Private cache owner trust is required; hashes are not authenticated shared-cache receipts. Preserve mixed timings and cold-build costs; there is no universal twofold speed, Clang/Python replacement, energy or AI-token claim.

## 0.27 source candidate: compact images and function-change evidence

Read docs/COMPACT-IMAGES-0.27.md. Native rf2c --compact separates file bytes from zero-filled VM tails; it changes raw object layout and is optional. rf2-build binds this flag into the whole-target cache key. Use a qualified current compiler; no silent older-tool fallback. This is distinct from compact Core syntax and MCP reply compaction.

--functions emits diagnostic token fingerprints, code ranges, relocations and direct-call edges. tools/function-impact.py reports change propagation with machineCodeReused false. No function/object reuse, complete semantic-effect replay or stable linker ABI is implemented. Keep type context and compiler provenance explicit.

Matched local complete build trials improved the tested legacy routes, including the smaller checksum target, but compact misses still cost more than direct compact compilation. File bytes and child CPU-time observations do not establish electrical energy or general runtime superiority. Nine MCP tools and their effects remain unchanged. Examples and failure controls are developer references, not field or hardware results.

## 0.28 source candidate: restricted code reuse and compiler stores

Read docs/FUNCTION-REUSE-0.28.md and docs/COMPILER-STORE-0.28.md. Explicit native compiler --reuse-cache requires an existing private directory, reparses an admitted scalar single-return grammar and reuses pre-resolution templates with current exit-label fixups. Keys bind kernel-reported executable-path file identity, options, declaration context and body tokens. This is not loaded-image attestation or authenticated shared caching. All other functions compile normally; --functions disables code reuse to retain diagnostic map equivalence. Report actual hits and mixed timings: the tested function-reuse route is slower than direct clean compilation and remains opt-in.

rf2-build --compiler-store names an explicit existing private store for checked compiler snapshots shared across project target caches. It retains ownership, hash, link/mode checks and locking. One-time first launch still occurs. Both features remain trusted CLI development effects, not new MCP tools. Preserve clean-byte and execution oracles, failed attempts, first-ever setup costs and native target limits. Linux/Windows execution, GUI toolkit parity, arbitrary language equivalence, runtime speed, energy and model-token savings are unestablished.

## 0.29 source candidate

Read docs/FUNCTION-REUSE-0.29.md. RF2FN002 supports validated straight-line scalar let/set before final return. Exact raw body/declaration context/compiler/options identity can reuse prior checked eligibility; misses perform full whitelist and normal validation. Metadata/code digest and stored/current local-count equality remain mandatory. Expose validationReused/fullValidationChecks. Diagnostic maps use their canonical path and disable machine-code reuse. Native hash feature query retains software fallback; updated independent seed encoder is not an unchanged historical seed.

Report workload-specific gains and losses: substantial SHA40 compile and edited-entry rebuilds improve; small examples still favor clean builds. Native NumberLab CLI and private browser app are tested learning examples, not classroom or toolkit parity evidence. No actual AI-token/provider-billing or energy benefit established. Nine bounded MCP tools unchanged; arbitrary systems source remains CLI-only.
