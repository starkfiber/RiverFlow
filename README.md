<p align="center"><img src="site/assets/riverflow-mark.png" width="130" alt="RiverFlow glass river mark"></p>
<h1 align="center">RF² · RiverFlow</h1>
<p align="center">Readable intent. Checked computation. Explicit effects.</p>

![RiverFlow conceptual landscape](site/assets/riverflow-hero.png)

By **Ilangkhumanan Thirunavokkarasu**, independently published by **Stark Fiber Enterprise**.

RiverFlow 0.6 runs general Core programs and scalar helpers natively, lowers checked programs into per-program ARM64 executables, and includes one working application capability: a validated attendance CSV exporter. **No Node, npm, Python or C++ runtime is required by users.** The compiler and runtime are written in RiverFlow systems source. A connected AI host can use the native MCP tools; no model is embedded in the executable.

[Download0.6](https://github.com/starkfiber/RiverFlow/releases/tag/v0.6.0) · [Read the book](https://starkfiber.github.io/RiverFlow/book/) · [Core and native execution](docs/NATIVE-CORE.md) · [Exact standalone boundary](docs/STANDALONE.md)

## Quick start

The download targets Apple Silicon Mac and includes both executables, sources and build scripts. Actual qualification is on the recorded local Mac. The encoded minimum is macOS 14; binaries are ad-hoc signed, not notarized.

```sh
./rf2 check examples/sum.flow
./rf2 run examples/sum.flow '[1,2,3,4,5]'
# value 15, work events18
./rf2 run book/examples/example-4.flow '[2,3,4]'
# scalar helper example: value29
```

For a compact reduction:

```text
rf2 v1 checked
sum input
```

```sh
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
```

Checked/wrap u32 arithmetic, named scalar helper calls, forward calls and bounded main loops follow the frozen Core contract. All functions are validated, including unused ones. Unknown effects, recursion, wrong types, scope leaks and exceeded limits reject.

## Per-program native compilation

```sh
./tools/build-core.sh ./rf2 ./rf2c examples/sum.flow sum-build
./sum-build/program '[1,2,3]'
```

`rf2 run` executes checked IR in the native runtime. The build script instead lowers Core to RiverFlow systems functions, compiles them with native `rf2c`, and explicitly applies macOS signing. The resulting kernel executes per-program ARM64 code. Source generation and execution are separate steps; the MCP lowering tool returns source only.

[How it works and what was tested](docs/NATIVE-CORE.md)

## A real application capability

```sh
./rf2 attendance capabilities/attendance.local.v1/test-records.json register.csv
```

`attendance.local@1` validates student IDs, Gregorian dates and present/absent/late states, rejects duplicate student/date records, and exports CSV with counts and a byte fingerprint. The included TEST records are programming fixtures, not field observations. The counts come from a compiled Core helper/loop program.

A CLI output path is an explicit file-write request; existing files and symlinks are refused. Over MCP, `attendance_export` returns CSV text and accepts no filesystem path. [Input rules, implementation and tests](capabilities/attendance.local.v1/README.md).

## Native MCP and Codex

```sh
codex mcp add rf2 -- /absolute/path/to/rf2 mcp
```

Five tools: `rf2_status`, `rf2_check`, `rf2_run`, `rf2_lower`, `attendance_export`.

The plugin launcher selects RF2_BIN or output/bin/rf2, without Node fallback or automatic builds. The client supplies AI intelligence. Read the advertised boundary before calling tools; no machine-source execution, arbitrary file access or network tool is exposed. Configure one registration route per client.

## RiverFlow builds RiverFlow

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
```

The native systems compiler reproduces its unsigned image across three native generations and matches the historical encoder. It builds the complete 0.6 runtime without Python, C/C++, an assembler or a linker. OS signing remains explicit. The Python seed is retained for initial bootstrap and development comparison. [Self-hosting scope and limitations](docs/NATIVE-COMPILER.md).

## Evidence

- [General Core](docs/GENERAL-CORE-VERIFICATION.json):109 program entries,317 admission checks,1,095 executions, including 180 seeded source mutations.
- [Direct kernels](docs/DIRECT-KERNEL-VERIFICATION.json):18 build cases and163 actual executable runs.
- [Application](docs/ATTENDANCE-VERIFICATION.json):CSV round trips, count/calendar checks, refusals and file protection.
- [Compact compatibility](docs/COMPACT-0.6-VERIFICATION.json):the retained 1,016 comparison corpus and transport/input guards.
- [Compiler](docs/NATIVE-COMPILER-0.6-VERIFICATION.json):fixed point and complete runtime image comparison.

These are executed local checks, not independent security certification, proof of every program, workplace/school findings or performance superiority. **No speed, energy or token-saving ratio is claimed.** The historical JavaScript server/playground and C backend remain explicit reference-development paths. Their tools and benchmark results do not automatically qualify native 0.6.

## The book and research

**RiverFlow RF²: Ideas into checked computation** documents the syntax, compiler, native Core path, application contract and retained failures. [Book downloads](https://github.com/starkfiber/RiverFlow/releases/tag/v0.6.0).

Kernel8/9, Developmental AI, Tamil Time Continuum, VOIKE and RU'OS motivate research questions. Naming them does not establish working hardware integration or scientific novelty. The compact application-intent syntax remains a separate design proposal; use the implemented schemas rather than inventing a working operation.

| Checked language | Research tributaries | Human possibility |
| --- | --- | --- |
| ![Language](site/assets/riverflow-language.png) | ![Research](site/assets/riverflow-research.png) | ![Future](site/assets/riverflow-future.png) |

MIT applies to original code and documentation. Concept artwork provenance is recorded in docs/ARTWORK.json. Dependencies retain their licences. AI assisted development and concept artwork are disclosed. Contribute reproducible programs, counterexamples and matched experiments.
