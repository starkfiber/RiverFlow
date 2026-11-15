# What can RF2 build today?

RiverFlow is an implemented language with a native compiler, useful applications and a bounded MCP server. It is not yet a replacement for every Java, C++, Python or assembly workflow. The stable runtime is **0.17**. **Workbench 0.38** adds Booking and a bounded learning editor; **Documents 0.37** adds read-only Mac document apps; **embedded 0.36** contains the separate ESP32-C3 compiler. These packages reuse qualified Mac tools and the unchanged bounded runtime. The table below labels development-only capabilities explicitly. Qualification receipts define its exact tested scope.

The long-term direction is one readable language across application and systems work. Each additional target needs its own implementation, contract and executed tests.

## Source sprint 0.40 and Workbench 0.38

The [source sprint](PLATFORM-SPRINT-0.40.md) qualifies shared lower/upper-bound lookup and an isolated borrowed-record candidate with typed nested scalar updates. The candidate does not add general owned nested values to released compilers. Its 72 role/failure briefs are planning cards, not 72 executed application tests.

[Workbench 0.38](BOOKING-STUDIO.md) provides one-room Booking CLI/GUI with cooperative locking, stale-form checks and explicit uncertain-save outcomes. Studio checks, runs and builds bounded Core lessons. It is not a general Systems IDE; Booking is not a production multi-room service. [Qualification](WORKBENCH-0.38-VERIFICATION.json) is separate from source experiments.

## Development 0.37: reusable text, tables and document reading

[Shared text/collection APIs](../examples/documents/LIBRARIES.md) add validated text statistics, exact/ASCII-folded KMP matching, line iteration, canonical integer parsing, bounded form decoding/HTML escaping, sorted unique items and four-field row tables. Two real apps consume the same physical modules: [a browser document workspace and a line-search CLI](../examples/documents/README.md). The workspace imports explicit regular UTF-8 files read-only into a bounded in-memory snapshot. PDF extraction, editing, persistent indexing and watched updates remain missing. These are trusted systems libraries, not new generic types or a whole-language memory-safety proof. Nine MCP tools retain their previous authority.

## Development 0.36: ESP32-C3 interrupts and peripheral leases

[A native cross-compiler](ESP32C3-INTERRUPTS-0.36.md) emits RV32 machine code, ELF32 and ROM-loaded RAM images. One bounded interrupt dispatcher, register preservation, a private stack and checked timer/watchdog leases have emulator controls and two 600-second virtual runs. Vendor QEMU boot/UART and explicitly scripted TMP102 bus controls pass. The compiler host remains Apple Silicon macOS; physical board and sensor validation are pending. This is a bounded u32 embedded profile, not complete Mac-language, Arduino, x86 or Linux parity.

## Development 0.33: owned u64 collections

[Relocating heap collections](HEAP-COLLECTIONS-0.33.md) support recoverable growth/access, checked local moves and typed mutable borrows, with explicit retirement retry and partial-release rules. Two `.flow` apps share parsing/sorting libraries and handle up to65536 values. No owner returns, concurrency or general raw-pointer safety is established. The separately implemented [ESP32-C3 subset](EMBEDDED-DIRECTION.md) does not make these Mac heap applications portable firmware.

## Development 0.32: structured fixed arrays

[Separate array arenas and larger bounded frames](STRUCTURED-STORAGE-0.32.md) remove the former per-element scalar-slot cost. The tested bounds are4096 u64 elements or32768 u8 bytes per declaration and49152 aggregate payload bytes per function. Named-local metadata stays bounded. Two native applications share the same library and support4096-byte queries. This is fixed function-local storage, not general heap transfer, concurrency or ecosystem parity.

## Development additions through 0.21

These are source-development capabilities with scoped evidence, separate from the stable 0.17 download. Native stdio authenticated contract tools, direct Apple Hypervisor VMM control, bounded Core WebAssembly, VM/vCPU ownership, owned guest mappings and shared-key image authentication now have local tests. See [0.21 boot contract](BOOT-CONTRACT-0.21.md). No Linux boot, x86 backend or general mobile platform qualification follows from those tests.

RF2 is **not at 100% Python, C or assembly coverage**. It still lacks major foundations such as floating-point types, arbitrary-precision arithmetic, general heap/ownership transfer, comprehensive libraries, concurrency, broad FFI, every CPU instruction/ABI and every machine target. Existing native applications do not establish ecosystem parity. Its AI host can write source, but RF2 has no embedded general model and no measured complete AI-task superiority.

See [the retained 0.21 benchmark report](BENCHMARKS-0.21.md), including losses and the historical inventory. No single speed score summarizes these workloads.

Start with the [tested .flow tutorial](FIRST-APP.md) and [package choices](START-HERE.md#choose-a-package).

## Choose the execution contract

| Route | What it does | Authority |
| --- | --- | --- |
| Compact V1 | Four short input-array reductions | Supplied input reads only |
| Checked Core | u32 computations, bounded loops and acyclic scalar helpers | Supplied input reads only; checked or wrapping arithmetic is explicit |
| Systems compiler | Trusted local programs compiled directly to ARM64/Mach-O | Explicit platform operations, including raw memory and OS calls |
| Native MCP | Nine tools for checked computation, lowering and fixed application capabilities | No caller-controlled file, network or arbitrary systems-code execution |

`rf2 run` executes checked internal IR in the native runtime. `rf2 lower` returns systems source. The explicit compiler/build route produces a per-program machine-code executable. These are separate operations, not interchangeable performance claims.

## Working capabilities

| Area | Implemented behavior (versioned contracts apply) | Present boundary | Contract or example |
| --- | --- | --- | --- |
| Native compiler | Compiler and runtime written in RF2; direct ARM64/Mach-O emission; self-reproduction checks | Qualified on Apple Silicon macOS; OS signing remains external | [Compiler](NATIVE-COMPILER.md) |
| Logical decisions | true/false, short-circuit all/any, not; normalized scalar truthiness | Trusted systems profile only; no separate Boolean type | [Logical guards](LOGICAL-GUARDS.md), [file inspector](../examples/file-kind/) |
| Integer programming | u64 systems scalars; arithmetic, comparisons, branches, loops and functions | Systems integer behavior differs from checked u32 Core; no floating-point type | [Core](NATIVE-CORE.md), [source](../native/compiler/compiler.rf2) |
| Hex and bytes | Decimal and lowercase `0x` hex spelling; packed u8 arrays; byte I/O; bitwise operators | No `0b` binary spelling, uppercase `0X` prefix or numeric separators | [Byte reference](BYTE-REFERENCE.md) |
| Modules and records | Explicit local imports; nominal records with u64 fields; typed borrowed parameters | Shared namespace, bounded source graph; no package registry, released general nested records or generic types; borrowed nesting is an isolated experiment | [Modules](MODULES-TYPES.md), [workload app](../examples/workload/) |
| Growable bytes | Noncopyable reservation-backed byte vectors; capacity grows within declared maximum | Max 1 MiB, function-local, no transfer, vector views or general heap | [Storage/results](STORAGE-RESULTS.md) |
| Checked arrays | Nominal fixed u64/u8 arrays, bounds checks and typed byte I/O | Function/frame bounds; bounded byte vectors available; separate bounded heap collections; no general heap transfer | [Arrays](CHECKED-ARRAYS.md), [bytes](TEXT-BYTES.md) |
| Results | Nominal scalar `ok`/`err` returns and mandatory exhaustive handlers | Structured ok records up to 4 scalar fields; errors u64 only; no generic payloads/resultlocals/params | [Results](RESULTS-VIEWS.md) |
| Unicode text | Validated UTF-8 views, byte/scalar counts and scalar indexing | Scalars are not grapheme clusters; no normalization, collation or language detection | [Unicode](UNICODE-CLEANUP.md), [document app](../examples/unicode-lines/) |
| Cleanup | Noncopyable owned files, handled release and automatic cleanup errors; legacy deferred close | Ordinary returns only; raw syscalls remain unsafe; local collection moves added in development0.33; no cross-function owner transfer or async | [Ownership](RESOURCE-OWNERSHIP.md) |
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
