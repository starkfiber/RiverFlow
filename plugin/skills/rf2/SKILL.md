---
name: rf2
description: Check and execute RiverFlow Core/compact programs, lower checked kernels, use the versioned attendance exporter, and develop native compiler evidence.
---
# RiverFlow RF² 0.11

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
