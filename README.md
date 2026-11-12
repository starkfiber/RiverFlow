# RF² RiverFlow

**Readable plans. Checked computation. Native tools.**

Created by **Ilangkhumanan Thirunavokkarasu**. Published by **SFE**.

![RiverFlow](site/assets/riverflow-hero.png)

RiverFlow is a language for readable application plans and explicit systems programming. Its own compiler emits ARM64 machine code. The compiler, runtime, document handlers and new graphical workspace are written in RiverFlow. The AI host supplies intelligence through a bounded MCP interface.

**0.12: checked collections, bytes and recoverable text processing.** The native RF2 compiler now supports fixed nominal u64/u8 arrays, typed byte I/O, guarded loop reductions and reusable modules. The new text-audit application validates streaming UTF-8 and reports failures through explicit status records. It closes its owned input file on tested normal/error paths. General exceptions, heap ownership and concurrency remain further language work.

[Download 0.12](https://github.com/starkfiber/RiverFlow/releases/tag/v0.12.0) · [Read the book](https://starkfiber.github.io/RiverFlow/book/) · [Text/byte contract](docs/TEXT-BYTES.md) · [Executed tests](docs/TEXT-BYTES-VERIFICATION.json)

Six delivered pieces: packed bytes, bounded byte I/O, recoverable status helpers, UTF-8 validation, checked decimal parsing and a complete file-audit app. No new speed or token-saving claim accompanies this release. [The previous optimizer comparison](docs/CONDITIONAL-REDUCTION.md) retains its exact inputs, raw trials, C formula baseline and limits.

```sh
printf 'Hello RF2\n' | ./rf2-text-audit
./rf2-text-audit document.txt
./rf2-latency 12 7 19 8 11 43 17
```

[Checked arrays](docs/CHECKED-ARRAYS.md) · [Latency analyzer](examples/latency/) · [Full-stack direction](docs/RF2-FULL-STACK-DIRECTION.md) · [Next six gates](docs/TEXT-BYTES.md#the-next-six-gates)

## Build beyond the first application

```rf2
profile RF2_SYSTEM_A64_V1
use "lib/workload.rf2"
fn main(argc, argv)
 let job = Job(7, 4, 12)
 let summary = Summary(0, 0, 0, 0)
 do workload_accept(job, summary)
 return summary.late
end
```

The complete [workload analyser](examples/workload/) reads a bounded CSV trace, computes input-order completion/deadline statistics and emits JSON. It uses shared I/O, CSV and accounting modules, with Job and Summary records. It does not claim a better scheduler or device measurements.

```sh
./tools/build-program.sh ./rf2c examples/workload/main.rf2 workload-build --opt
./workload-build/program examples/workload/jobs.csv
```

Imports, nominal record checks, stack storage and typed borrowed parameters are compiled in RF2. Current field types are u64 machine words. Strings, enums, nested records, general ownership and more machine targets remain further language work. [Exact limits](docs/MODULES-TYPES.md).

RiverFlow Studio remains available as a separate graphical worksheet example on Apple Silicon macOS. It renders through a private browser workspace. [Studio contract](docs/GRAPHICAL-EDITOR.md).

## Start with a real operation

This is a complete versioned application plan:

```rf2
rf2 app v1
invoice total
currency MYR
tax 600 bps
```

With the downloaded Apple Silicon Mac package:

```sh
./rf2 app capabilities/invoice.total.v1/quote.rf2 \
  capabilities/invoice.total.v1/test-lines.json
```

The supplied programming fixture returns subtotal 2899 cents, tax 174 cents and total 3073 cents. The rate is an explicit input, not tax advice. Line multiplication and subtotal run through a compiled Core helper/loop. Invoice-level rounding and checked bounds are specified, not guessed. [Input rules, effects and limitations](capabilities/invoice.total.v1/README.md).

For attendance CSV export:

```sh
./rf2 attendance capabilities/attendance.local.v1/test-records.json new-register.csv
```

Only an explicit new output file can be created. Existing files and symlinks are refused. Included TEST identifiers are programming fixtures, not participant data. [Attendance contract](capabilities/attendance.local.v1/README.md).

## Save, revise and print

```sh
./rf2 invoice save capabilities/invoice.total.v1/quote.rf2 \
  capabilities/invoice.total.v1/test-lines.json first.invoice.json
./rf2 invoice set first.invoice.json 0 2 250 edited.invoice.json
./rf2 invoice inspect edited.invoice.json
./rf2 invoice pdf edited.invoice.json worksheet.pdf
```

A file-based native workspace: explicit new-file revisions, checked totals and direct PDF output. The graphical editor shares this checked document model. Payment and tax-law determination are outside its contract. [Workspace contract](docs/INVOICE-WORKSPACE.md).

Prepare an immutable plan once, inspect its visible currency/tax rules, apply it to fresh lines, then release it. Up to 32 process-local plans; discard handles on reconnect. [MCP lifecycle](docs/PREPARED-PLANS.md).

[Graphical workspace and safety contract](docs/GRAPHICAL-EDITOR.md) · [Platform ABI](docs/PLATFORM-ABI.md)

## Compute and compile

A complete compact computation:

```rf2
rf2 v1 checked
sum input
```

```sh
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
./rf2 check book/examples/example-4.flow
./rf2 run book/examples/example-4.flow '[2,3,4]'
./tools/build-core.sh ./rf2 ./rf2c book/examples/example-4.flow squares-build
./squares-build/program '[2,3,4]'
```

The helper example returns 29. `run` checks source and executes bounded IR in the native runtime. The explicit build route lowers checked Core to RiverFlow systems functions and compiles an ARM64 executable. These are distinct paths. Core permits only supplied input reads, checked/wrapping u32 operations, bounded loops and acyclic scalar helpers. Trusted systems source has a separate profile and authority. [Native Core boundary](docs/NATIVE-CORE.md).

## Connect MCP

```sh
./rf2 mcp
```

The native server exposes nine tools: `rf2_status`, `rf2_check`, `rf2_run`, `rf2_lower`, `attendance_export`, `invoice_total`, `invoice_prepare`, `invoice_apply`, `invoice_release`. Application tools return data without filesystem access. Lower returns source without compiling or writing it. The Codex plugin launches the installed native executable; it never falls back to Node or silently downloads/builds software. [Plugin skill](plugin/skills/rf2/SKILL.md).

## Evidence before claims

- Invoice: 630 successful comparisons, 108 comparisons with 0.6 Core, 39 refusals, 200 seeded plan mutations and five CLI cases. [Receipt](docs/INVOICE-0.12-VERIFICATION.json).
- Core: 1095 execution comparisons and 317 admission checks. [Receipt](docs/GENERAL-CORE-0.12-VERIFICATION.json).
- Direct kernels: 18 builds and 163 executed cases. [Receipt](docs/DIRECT-KERNEL-0.12-VERIFICATION.json).
- Compact: 1016 compatibility comparisons, input guards and transport mutations. [Receipt](docs/COMPACT-0.12-VERIFICATION.json).
- Attendance: 34 successful exports/calendar cases, 45 refusals and three file-protection checks. [Receipt](docs/ATTENDANCE-0.12-VERIFICATION.json).
- Compiler: native fixed point, independently expected results and full runtime byte comparison with the historical encoder. [Receipt](docs/NATIVE-COMPILER-0.12-VERIFICATION.json).

The optional 0.11 optimiser has a new matched runtime-input comparison against0.10 and Clang -O3. The results and remaining branch gap are reported above. Opt-in `rf2 mcp --compact` reduces the tested complete session's encoded o200k text by 6.70%, retaining structured results and errors. Default MCP output remains compatible. These are local kernel timings and exact interface encodings, not universal speed, model billing or AI code-generation claims. [Raw evidence and method](docs/LANGUAGE-MEASUREMENTS.md).

Current native qualification is Apple Silicon macOS. There is no independent security audit, universal platform support, field outcome or model council approval. The retained JavaScript/C reference, Python bootstrap/tests and publishing tools are developer dependencies, not user runtime requirements. Naming research projects does not establish hardware integration or scientific novelty.

## Rebuild and improve

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
```

The build composes nine RiverFlow runtime modules. It invokes no Python, Node, C/C++ compiler, assembler or linker. macOS signing and platform interfaces remain external dependencies. The systems compiler now admits at most 256 functions, with accepted upper-bound executions and refusal at 257. [Build scope](docs/NATIVE-COMPILER.md).

The revised book has 23 numbered chapters, worked examples, application contracts, failures and measurements. Original code and text use the MIT licence. Referenced projects and dependencies retain their own licences.

## Why the GitHub language bar looks different

GitHub uses Linguist's supported-language list, which does not yet include RiverFlow. Generated book HTML and generated kernels are marked accurately in `.gitattributes`. We do not relabel RiverFlow as another language or hide the reference tools. This project-owned inventory counts RiverFlow source explicitly, alongside development and website code. [Method and file list](docs/SOURCE-INVENTORY.json) · [GitHub language documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-repository-languages).

![Source inventory](docs/SOURCE-INVENTORY.svg)

## Research direction

Kernel 8/9, Developmental AI, Tamil Time Continuum, VOIKE, RU'OS and the human-AI workplace study motivate testable questions. Their names are not implementation evidence. Next: profile large invoice inputs, independently review the compiler/parser, qualify more targets and measure complete AI tasks with real usage receipts. Keep each claim linked to its actual source, test and limitation.

### Release 0.11 qualification

Module/record tests execute 60 record cases, 150 comparisons with 0.9, 60 independently expected workload cases, 44 type refusals, 13 import refusals and 13 workload refusals. Boundary checks cover 16 fields, 32 record types, 32 source files, import depth and recursive record lifetime. Existing Core, compiler, direct kernel, SDK and application suites were rerun. [Module/type receipt](docs/MODULES-TYPES-0.11-VERIFICATION.json) · [Boundary receipt](docs/MODULE-BOUNDS-0.10.json).

The default MCP mode retains all readable results; `--compact` is for clients that consume structuredContent. It does not expand source/file/network permissions. RF2 does not embed a language model or yet replace the Java, C++, Python or assembly ecosystems.
