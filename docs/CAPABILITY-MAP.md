# What can RF2 build today?

RiverFlow is an implemented language with a native compiler, useful applications and a bounded MCP server. It is not yet a replacement for every Java, C++, Python or assembly workflow. The stable inventory describes the **0.17** release, with owned files and visible cleanup errors. Qualification receipts define its exact tested scope.

The long-term direction is one readable language across application and systems work. Each additional target needs its own implementation, contract and executed tests.

## Development additions through 0.21

These are source-development capabilities with scoped evidence, separate from the stable 0.17 download. Native stdio authenticated contract tools, direct Apple Hypervisor VMM control, bounded Core WebAssembly, VM/vCPU ownership, owned guest mappings and shared-key image authentication now have local tests. See [0.21 boot contract](BOOT-CONTRACT-0.21.md). No Linux boot, x86 backend or general mobile platform qualification follows from those tests.

RF2 is **not at 100% Python, C or assembly coverage**. It still lacks major foundations such as floating-point types, arbitrary-precision arithmetic, general heap/ownership transfer, comprehensive libraries, concurrency, broad FFI, every CPU instruction/ABI and every machine target. Existing native applications do not establish ecosystem parity. Its AI host can write source, but RF2 has no embedded general model and no measured complete AI-task superiority.

See [the current benchmark report](BENCHMARKS-0.21.md), including losses and the historical inventory. No single speed score summarizes these workloads.

## Choose the execution contract

| Route | What it does | Authority |
| --- | --- | --- |
| Compact V1 | Four short input-array reductions | Supplied input reads only |
| Checked Core | u32 computations, bounded loops and acyclic scalar helpers | Supplied input reads only; checked or wrapping arithmetic is explicit |
| Systems compiler | Trusted local programs compiled directly to ARM64/Mach-O | Explicit platform operations, including raw memory and OS calls |
| Native MCP | Nine tools for checked computation, lowering and fixed application capabilities | No caller-controlled file, network or arbitrary systems-code execution |

`rf2 run` executes checked internal IR in the native runtime. `rf2 lower` returns systems source. The explicit compiler/build route produces a per-program machine-code executable. These are separate operations, not interchangeable performance claims.

## Working capabilities

| Area | Released behavior | Present boundary | Contract or example |
| --- | --- | --- | --- |
| Native compiler | Compiler and runtime written in RF2; direct ARM64/Mach-O emission; self-reproduction checks | Qualified on Apple Silicon macOS; OS signing remains external | [Compiler](NATIVE-COMPILER.md) |
| Logical decisions | true/false, short-circuit all/any, not; normalized scalar truthiness | Trusted systems profile only; no separate Boolean type | [Logical guards](LOGICAL-GUARDS.md), [file inspector](../examples/file-kind/) |
| Integer programming | u64 systems scalars; arithmetic, comparisons, branches, loops and functions | Systems integer behavior differs from checked u32 Core; no floating-point type | [Core](NATIVE-CORE.md), [source](../native/compiler/compiler.rf2) |
| Hex and bytes | Decimal and lowercase `0x` hex spelling; packed u8 arrays; byte I/O; bitwise operators | No `0b` binary spelling, uppercase `0X` prefix or numeric separators | [Byte reference](BYTE-REFERENCE.md) |
| Modules and records | Explicit local imports; nominal records with u64 fields; typed borrowed parameters | Shared namespace, bounded source graph; no package registry, nested records or generic types | [Modules](MODULES-TYPES.md), [workload app](../examples/workload/) |
| Growable bytes | Noncopyable reservation-backed byte vectors; capacity grows within declared maximum | Max 1 MiB, function-local, no transfer, vector views or general heap | [Storage/results](STORAGE-RESULTS.md) |
| Checked arrays | Nominal fixed u64/u8 arrays, bounds checks and typed byte I/O | Function/frame bounds; bounded byte vectors available; no general heap/relocating vectors | [Arrays](CHECKED-ARRAYS.md), [bytes](TEXT-BYTES.md) |
| Results | Nominal scalar `ok`/`err` returns and mandatory exhaustive handlers | Structured ok records up to 4 scalar fields; errors u64 only; no generic payloads/resultlocals/params | [Results](RESULTS-VIEWS.md) |
| Unicode text | Validated UTF-8 views, byte/scalar counts and scalar indexing | Scalars are not grapheme clusters; no normalization, collation or language detection | [Unicode](UNICODE-CLEANUP.md), [document app](../examples/unicode-lines/) |
| Cleanup | Noncopyable owned files, handled release and automatic cleanup errors; legacy deferred close | Ordinary returns only; raw syscalls remain unsafe; no transfer, async or heap ownership | [Ownership](RESOURCE-OWNERSHIP.md) |
| Files and CLI | Trusted explicit file operations and bounded example parsers | Caller must handle short I/O and failures; not automatic access containment | [Text auditor](../examples/text-audit/), [Unicode auditor](../examples/unicode-lines/) |
| Documents | Native invoice revisions and direct PDF output | One defined document model; not a general publishing engine or accounting service | [Workspace](INVOICE-WORKSPACE.md) |
| Graphical application | RF2-controlled private loopback editor, browser forms and document exports | Not a native widget toolkit; not a general mobile UI framework | [Studio](GRAPHICAL-EDITOR.md) |
| MCP | Status, check, run, lower, attendance export, invoice total and three prepared-plan lifecycle tools | Host supplies AI intelligence; no embedded model; systems compiler is CLI-only | [Plugin](../plugin/skills/rf2/SKILL.md) |
| Optimization | Optional register/instruction lowering and narrowly guarded loop reductions | Results vary by workload; ordinary-loop fallbacks and slower cases remain | [Optimizer](NATIVE-OPTIMIZATION.md), [measurements](LANGUAGE-MEASUREMENTS.md) |

## Foundations still to implement or qualify

| Goal | Missing foundation or decisive test |
| --- | --- |
| Broader ownership | Ownership transfer, generic resources, async cancellation and richer cleanup error aggregation |
| Larger application data | General growable containers, heap/transfer lifetime rules, richer result payloads and a broader standard library |
| Concurrent services | Tasks/threads, synchronization, cancellation and resource behavior under concurrency |
| Network applications | A reviewed networking library, connection ownership, protocol/error handling and real service acceptance tests |
| Android, iOS and web targets | Concrete backends/adapters, platform integration, packaging and target-specific acceptance tests |
| x86 and boot software | Code generation and boot/ABI implementations, tested on each actual target |
| GPU, optical or transistor claims | A real backend or physical apparatus, measurements and independent evidence; paper references do not supply this |
| AI productivity claims | Matched complete-task trials, real usage receipts, correctness review and failure accounting |
| General security assurance | Threat model, supported tooling, adversarial executions and independent audit beyond the finite local corpus |

## What “full programming” means here

RF2 can already express working native programs using its implemented control flow, functions, memory and platform interfaces. That does not establish library compatibility, every machine target, every safety guarantee or parity with mature language ecosystems. A byte chart is a useful reference, not a CPU instruction set; hexadecimal is a representation, not a new execution model.

Build the next program around an explicit input, output, error contract and target. Add independent expected results and retain the failing cases. [Full-stack direction](RF2-FULL-STACK-DIRECTION.md) records the wider route; [0.14 qualification](RELEASE-0.14-VERIFICATION.json) records what was actually tested.
