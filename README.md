<p align="center"><img src="site/assets/riverflow-mark.png" width="130" alt="RiverFlow glass river mark"></p>
<h1 align="center">RF² · RiverFlow</h1>
<p align="center">Let your ideas flow. Make every step explicit.</p>

![RiverFlow conceptual landscape](site/assets/riverflow-hero.png)

A programming language by **Ilangkhumanan Thirunavokkarasu**. AI assisted development, deterministic language rules, open source foundations.

RF² starts with a small executable promise: write typed, bounded computations, inspect their effects and run them locally. Core 0.1 includes a parser, semantic checks, JSON intermediate representation, interpreter, CLI, browser playground and MCP server. Its bootstrap is JavaScript with **no Python runtime dependency**.

[Try the playground](https://starkfiber.github.io/RiverFlow/rf2/) · [Language specification](docs/SPEC.md) · [Research foundation](docs/RESEARCH.md)

## Quick start

Requires Node 22 or newer. Native execution and the full native differential suite additionally require Clang with AddressSanitizer and UndefinedBehaviorSanitizer support.

```sh
git clone https://github.com/starkfiber/RiverFlow.git
cd RiverFlow
npm ci
node bin/rf2.mjs run examples/sum.flow '[1,2,3,4,5]'
# { "value": 15, ... }
node bin/rf2.mjs check examples/sum.flow
node bin/rf2.mjs compile examples/sum.flow program.json
npm test
```

```text
FLOW "Hello, RiverFlow"
PROFILE RF2_U32_CORE_V0
ARITHMETIC CHECKED
FUNCTION main(data: u32[], count: u32) RETURNS u32
  STEP answer = ADD WITH { a: 500, b: 20, result: value }
  RETURN value
END
```

Programs use explicit checked or wrapping u32 arithmetic, array reads, scalar helpers and bounded loops. Unknown operations and effects reject. AI can help propose source through a connected host; it cannot silently change language permissions.

## Codex and MCP

The repository root is the Codex plugin package; its skill and launcher live in `plugin/`. After cloning and `npm ci`, register the repository's marketplace:

```sh
codex plugin marketplace add /absolute/path/to/RiverFlow
codex plugin add rf2@riverflow-local
```

The skill is `rf2`. Client UI determines whether `/rf2` appears; the package cannot force a slash command. Alternatively register MCP directly:

```sh
codex mcp add rf2 -- /bin/sh /absolute/path/to/RiverFlow/plugin/launch-mcp.sh
```

Use one registration route to avoid duplicate servers. The plugin includes `rf2_status`, `rf2_check` and `rf2_run`. MCP receives source and data; no file, network or phone access tools are exposed. Other MCP clients can launch the same script. Intelligence comes from the client, not an embedded Astra/SLM API.

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

## SFE research bridge · 0.2

Ten local MCP tools now connect checked RiverFlow execution to a pinned catalog of 20 public SFE repositories. Browse each repository and read its public README through `sfe_repositories`, `sfe_repository` and `sfe_repository_document`. Research links and measurement arithmetic are explicit about what is proposed, supplied or observed. Existing applications retain their own execution interfaces.

`rf2_run_batch` checks one program once before evaluating several inputs. In the retained one-host sum experiment this reduces repeated small-job overhead, while a direct JavaScript loop remains substantially faster. [Scope, tools and limitations](docs/MCP-RESEARCH.md) · [Raw benchmark](docs/BENCHMARK.json).

## RiverFlow 0.3 and the first book

[Read the book online](https://starkfiber.github.io/RiverFlow/book/) · [Download the first edition](https://github.com/starkfiber/RiverFlow/releases/tag/v0.3.0)

**RiverFlow RF²: Ideas into checked computation**, by Ilangkhumanan Thirunavokkarasu, is an independently published SFE guide with14chapters, runnable examples, exercises, native ABI reference and retained measurement tables. PDF, EPUB and source are openly available. It is not an independently peer-reviewed academic monograph.

Version0.3 adds validated C11 emission through CLI emit-c and the text-only rf2_emit_c MCP tool. A conservative backend and a narrowly recognized sum reduction preserve Core semantics. Native host tests compare values, work counts and errors under sanitizers, including all complete book examples. The selected sum approaches a strong handwritten baseline in retained host runs; no universal advantage or phone qualification is asserted.

Build the book with the optional document dependencies in book/requirements.txt and python3 tools/build-book.py. These are publication tools, not a RiverFlow runtime dependency.
