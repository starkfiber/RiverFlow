# RF² RiverFlow

**Readable plans. Checked computation. Native tools.**

Created by **Ilangkhumanan Thirunavokkarasu**. Published by **SFE**.

![RiverFlow](site/assets/riverflow-hero.png)

RiverFlow 0.7 runs Core programs and reusable helpers, builds per-program ARM64 executables, and provides attendance export and invoice totals through native MCP. The compiler, runtime and application adapters are written in RiverFlow. **Users need no Node, npm, Python or C++ runtime.** The AI host supplies intelligence; the executable does not contain a model.

[Download 0.7](https://github.com/starkfiber/RiverFlow/releases/tag/v0.7.0) · [Read the book](https://starkfiber.github.io/RiverFlow/book/) · [Specification](docs/SPEC.md) · [Measured results](docs/CAPABILITY-MEASUREMENTS.md)

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

The native server exposes six tools: `rf2_status`, `rf2_check`, `rf2_run`, `rf2_lower`, `attendance_export`, `invoice_total`. Application tools return data without filesystem access. Lower returns source without compiling or writing it. The Codex plugin launches the installed native executable; it never falls back to Node or silently downloads/builds software. [Plugin skill](plugin/skills/rf2/SKILL.md).

## Evidence before claims

- Invoice: 630 successful comparisons, 108 comparisons with 0.6 Core, 39 refusals, 200 seeded plan mutations and five CLI cases. [Receipt](docs/INVOICE-VERIFICATION.json).
- Core: 1095 execution comparisons and 317 admission checks. [Receipt](docs/GENERAL-CORE-0.7-VERIFICATION.json).
- Direct kernels: 18 builds and 163 executed cases. [Receipt](docs/DIRECT-KERNEL-0.7-VERIFICATION.json).
- Compact: 1016 compatibility comparisons, input guards and transport mutations. [Receipt](docs/COMPACT-0.7-VERIFICATION.json).
- Attendance: 34 successful exports/calendar cases, 45 refusals and three file-protection checks. [Receipt](docs/ATTENDANCE-0.7-VERIFICATION.json).
- Compiler: native fixed point, independently expected results and full runtime byte comparison with the historical encoder. [Receipt](docs/NATIVE-COMPILER-0.7-VERIFICATION.json).

Measurements are mixed. The invoice operation beats a JavaScript comparator on one-line requests and loses on larger inputs. The 19-token plan costs more than direct configuration when repeated across the measured 20 tool calls. Raw timings and exact encoded fixtures are published. **No general speed, energy or AI-task token-saving claim is established.** [Method and results](docs/CAPABILITY-MEASUREMENTS.md).

Current native qualification is Apple Silicon macOS. There is no independent security audit, universal platform support, field outcome or model council approval. The retained JavaScript/C reference, Python bootstrap/tests and publishing tools are developer dependencies, not user runtime requirements. Naming research projects does not establish hardware integration or scientific novelty.

## Rebuild and improve

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
```

The build composes seven RiverFlow runtime modules. It invokes no Python, Node, C/C++ compiler, assembler or linker. macOS signing and platform interfaces remain external dependencies. The current systems compiler admits at most 128 functions, and this runtime reaches that limit; widening it needs compiler boundary tests, not silent truncation. [Build scope](docs/NATIVE-COMPILER.md).

The revised book has 19 numbered chapters, worked examples, application contracts, failures and measurements. Original code and text use the MIT licence. Referenced projects and dependencies retain their own licences.

## Why the GitHub language bar looks different

GitHub uses Linguist's supported-language list, which does not yet include RiverFlow. Generated book HTML and generated kernels are marked accurately in `.gitattributes`. We do not relabel RiverFlow as another language or hide the reference tools. This project-owned inventory counts RiverFlow source explicitly, alongside development and website code. [Method and file list](docs/SOURCE-INVENTORY.json) · [GitHub language documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-repository-languages).

![Source inventory](docs/SOURCE-INVENTORY.svg)

## Research direction

Kernel 8/9, Developmental AI, Tamil Time Continuum, VOIKE, RU'OS and the human-AI workplace study motivate testable questions. Their names are not implementation evidence. Next: profile large invoice inputs, independently review the compiler/parser, qualify more targets and measure complete AI tasks with real usage receipts. Keep each claim linked to its actual source, test and limitation.
