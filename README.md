<p align="center"><img src="site/assets/riverflow-mark.png" width="130" alt="RiverFlow glass river mark"></p>
<h1 align="center">RF² · RiverFlow</h1>
<p align="center">Let your ideas flow. Make every step explicit.</p>

![RiverFlow conceptual landscape](site/assets/riverflow-hero.png)

A programming language by **Ilangkhumanan Thirunavokkarasu**. AI assisted development, deterministic language rules, open source foundations.

RF² now has an experimental **standalone Apple Silicon macOS executable**, with a compact human-readable front end, native ARM64 computation and built-in MCP. **No Node, npm, C++ or Python runtime is required by users.** The runtime is written in a separate RiverFlow systems profile and emitted directly to machine code by a small Python build-time seed. It is not self-hosted yet.

The original JavaScript Core implementation remains a reference and browser playground. Native 0.4 implements four compact reductions, not every historical dialect or all ten reference MCP tools. [Exact native scope and verification](docs/STANDALONE.md).

[Try the playground](https://starkfiber.github.io/RiverFlow/rf2/) · [Language specification](docs/SPEC.md) · [Research foundation](docs/RESEARCH.md)

## Where RiverFlow is heading

RF² is intended to become a compact human/AI intent interface: describe the outcome, bind versioned capabilities and checks, and let the runtime supply known implementations. The current Core is its execution foundation. The compact service layer and end-to-end token savings remain to be implemented and measured. [Intent-layer direction](docs/INTENT-LAYER.md).

## Quick start

On Apple Silicon macOS 14+, use the [standalone executable from release 0.4](https://github.com/starkfiber/RiverFlow/releases/tag/v0.4.0), or build it from source. End users do not need npm or Node. Building currently needs Python 3 and the macOS code-signing tool; no C/C++ compiler, assembler or linker is invoked.

```sh
git clone https://github.com/starkfiber/RiverFlow.git
cd RiverFlow
python3 bootstrap/seed.py native/rf2.rf2 output/bin/rf2
./output/bin/rf2 run examples/compact/sum.rf2 '[1,2,3,4,5]'
# value 15; checked native arithmetic
./output/bin/rf2 check examples/compact/sum.rf2
./output/bin/rf2 expand examples/compact/sum.rf2
```

```text
rf2 v1 checked
sum input
```

Choose `sum`, `squares`, `bits` or `nonzero`, and explicit `checked` or `wrap` arithmetic. Unknown syntax/effects reject. Expand the short source to inspect its full Core meaning. General Core helpers and service/application construction remain outside the native subset. This is a first native foundation, not a universal language completion claim.

## Codex and MCP

```sh
codex mcp add rf2-native -- /absolute/path/to/rf2 mcp
```

The executable supplies `rf2_status`, `rf2_check` and `rf2_run` over stdio. The client provides AI intelligence. The native process does not embed a model or expose network, file-access or deployment tools. The repository plugin uses the same executable through `plugin/launch-mcp.sh`; configure `RF2_BIN` when the binary lives elsewhere. No automatic Node fallback or build occurs at launch. [Build, limits and compatibility](docs/STANDALONE.md).

## What is proven today?

Local language tests compare 100 deterministic arrays with an independent sum and challenge overflow, wrap arithmetic, type/bounds errors, helper recursion, loop scope and the execution budget. MCP integration tests exercise actual stdio discovery, successful execution and rejection.

This release does not establish universal compatibility, native-code performance superiority, an OS, a new transistor, or million-year durability. It implements a deliberately small profile. Future changes must earn their claims through tests and measurement. Historical private RF²/CompilerX prototypes are separate evidence and are not redistributed here.

## Explore the identity

Five original AI-generated concept artworks appear in the website and repository. They express flow, structure, research and possibility; they are not experimental diagrams.

| Checked language | Research tributaries | Human possibility |
|---|---|---|
| ![Language](site/assets/riverflow-language.png) | ![Research](site/assets/riverflow-research.png) | ![Future](site/assets/riverflow-future.png) |

## Contribute

Start with a failing programme or a reproducible experiment. Propose syntax and semantics before implementation. Keep profile compatibility explicit, include counterexamples and compare against the simplest credible alternative. Separate feature proposals, modeled results and hardware observations.

MIT applies to original code and documentation. Concept artwork provenance is recorded in `docs/ARTWORK.json`; no trademark registration or exclusive legal rights are claimed. Dependencies retain their own licences.

## Reference implementation research bridge · 0.2

The retained JavaScript reference has ten MCP tools that connect checked RiverFlow execution to a pinned catalog of 20 public SFE repositories. Browse each repository and read its public README through `sfe_repositories`, `sfe_repository` and `sfe_repository_document`. Research links and measurement arithmetic are explicit about what is proposed, supplied or observed. Existing applications retain their own execution interfaces.

`rf2_run_batch` checks one program once before evaluating several inputs. In the retained one-host sum experiment this reduces repeated small-job overhead, while a direct JavaScript loop remains substantially faster. [Scope, tools and limitations](docs/MCP-RESEARCH.md) · [Raw benchmark](docs/BENCHMARK.json).

## RiverFlow 0.3 and the first book

[Read the book online](https://starkfiber.github.io/RiverFlow/book/) · [Download the first edition](https://github.com/starkfiber/RiverFlow/releases/tag/v0.3.0)

**RiverFlow RF²: Ideas into checked computation**, by Ilangkhumanan Thirunavokkarasu, is an independently published SFE guide with 15 chapters in the revised edition,, runnable examples, exercises, native ABI reference and retained measurement tables. PDF, EPUB and source are openly available. It is not an independently peer-reviewed academic monograph.

Version0.3 adds validated C11 emission through CLI emit-c and the text-only rf2_emit_c MCP tool. A conservative backend and a narrowly recognized sum reduction preserve Core semantics. Native host tests compare values, work counts and errors under sanitizers, including all complete book examples. The selected sum approaches a strong handwritten baseline in retained host runs; no universal advantage or phone qualification is asserted.

Build the book with the optional document dependencies in book/requirements.txt and python3 tools/build-book.py. These are publication tools, not a RiverFlow runtime dependency.

## Standalone 0.4 and the revised book

The machine encoder, RF2 systems source, compact examples and executable-level verification are public. The revised book explains both the native subset and the older reference toolchain. Native test evidence is retained in [STANDALONE-VERIFICATION.json](docs/STANDALONE-VERIFICATION.json). No new speed claim is made.

The systems profile is a new implementation dialect, distinct from Core and historical ASMX. Its trusted seed is still written in Python. Completing a native seed, general Core migration and a self-hosted fixed-point build are open work, explicitly tracked rather than claimed complete.
