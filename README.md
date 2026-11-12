# RF² RiverFlow

### Readable programs. Explicit effects. Native tools.

Created by **Ilangkhumanan Thirunavokkarasu** · Published by **SFE** · **MIT licence**

[Download](https://github.com/starkfiber/RiverFlow/releases/latest) · [Read the book](https://starkfiber.github.io/RiverFlow/book/) · [Language capability map](docs/CAPABILITY-MAP.md) · [Byte and ASCII reference](docs/BYTE-REFERENCE.md) · [MCP skill](plugin/skills/rf2/SKILL.md)

![A luminous RiverFlow landscape](site/assets/riverflow-hero.png)

RiverFlow turns readable source into useful native programs. Its compiler emits ARM64 machine code directly. The compiler, runtime and application controllers are written in RF2. An AI host can work through the bounded MCP interface; intelligence is supplied by the host, with deterministic language rules around what runs.

**The direction:** one understandable language for application and systems work. Each capability ships with its input contract, failure behavior, target limits and executed evidence.

## Start with something real

The Apple Silicon Mac package contains ready-to-run tools. Users need no Node, npm, Python or C++ runtime.

```sh
./rf2 status
./rf2-file-kind document.bin
./rf2-hex document.bin
printf 'Hello world\n' | ./rf2-unicode-lines
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
```

The document auditor handles UTF-8 rows, reports malformed input and continues with later valid text. It distinguishes byte counts from Unicode scalar counts. The compact sum returns `6`.

| Build or use | What works | Open the example |
| --- | --- | --- |
| Owned file applications | Noncopyable file owners, typed I/O and visible cleanup errors | [Hex inspector](examples/hex/), [ownership contract](docs/RESOURCE-OWNERSHIP.md) |
| Text and byte processing | Checked arrays, strict UTF-8 views, scalar indexing and recoverable row validation | [Unicode auditor](examples/unicode-lines/) |
| Reusable native programs | Local modules, nominal records, functions and explicit file I/O | [Workload analyser](examples/workload/) |
| Checked computation | Bounded u32 Core, scalar helpers and explicit checked/wrapping arithmetic | [Core contract](docs/NATIVE-CORE.md) |
| Document applications | File revisions, exact integer totals, direct PDF output and graphical forms | [RiverFlow Studio](docs/GRAPHICAL-EDITOR.md) |
| AI tool integration | Nine native MCP tools with defined effects and prepared-plan lifecycle | [MCP interface](plugin/skills/rf2/SKILL.md) |

## Read it, compile it, inspect it

```rf2
profile RF2_SYSTEM_A64_V1
fn main(argc,argv)
 let ascii_a=0x41
 return ascii_a!=65
end
```

```sh
./tools/build-program.sh ./rf2c program.rf2 program-build --opt
./program-build/program
```

This complete systems program exits `0` when the byte values agree. The build script creates a new directory and applies normal macOS signing; it does not execute the result. [Hex, ASCII and byte order](docs/BYTE-REFERENCE.md) explain the representation. [The capability map](docs/CAPABILITY-MAP.md) separates released features from the wider roadmap.

![Two explicit execution routes through RiverFlow](site/assets/rf2-capabilities.svg)

## Connect an AI host

```sh
./rf2 mcp
```

Native tools: `rf2_status`, `rf2_check`, `rf2_run`, `rf2_lower`, `attendance_export`, `invoice_total`, `invoice_prepare`, `invoice_apply`, `invoice_release`.

MCP accepts bounded computation and defined application inputs. It does not expose arbitrary file paths, network access or systems-code execution. Lowering returns source; compiling a trusted program is an explicit developer action. The plugin launches an existing native binary and never silently builds, downloads or falls back to Node.

## Evidence stays beside the code

**0.16 adds short-circuit logical guards and read-only file signature inspection.** [Logical guards](docs/LOGICAL-GUARDS.md) build on owned files and cleanup errors. Atomic acquisition exposes no raw descriptor. I/O results require handling; release consumes the owner. Automatic close failure is visible while a primary error remains preserved. [Ownership contract](docs/RESOURCE-OWNERSHIP.md) · [Release receipt](docs/RELEASE-0.16-VERIFICATION.json).

Independent ownership probes and full-output hex comparisons sit beside existing Unicode, compiler, runtime and MCP tests. WhatIF also ran a bounded disposable Studio check; HTTP availability is separate from compiler correctness. The updated book explains the design and remaining limits.

Performance is workload-specific. Some guarded reductions remove repeated work; other workloads remain slower than mature compilers. Encoded interface counts are not billed model usage. [Measurement method and limits](docs/LANGUAGE-MEASUREMENTS.md).

## Build the next foundation

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
```

The native rebuild uses RF2 plus OS file/signing utilities. Python, JavaScript, C references and publishing tools remain development dependencies. Current native qualification is Apple Silicon macOS. Android, iOS, web, x86, boot, concurrency and optical/GPU integration need separate implementations and target tests. RF2 does not yet replace every mature language ecosystem.

Bring a small complete program, a precise expected result and a reproducible failure. Contributions should preserve the original oracle and report both improvements and remaining gaps.

[Full-stack direction](docs/RF2-FULL-STACK-DIRECTION.md) · [Source inventory](docs/SOURCE-INVENTORY.json) · [MIT licence](LICENSE)
