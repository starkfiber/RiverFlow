<p align="center"><img src="site/assets/riverflow-mark.png" width="130" alt="RiverFlow glass river mark"></p>
<h1 align="center">RF² · RiverFlow</h1>
<p align="center">Let your ideas flow. Make every step explicit.</p>

![RiverFlow conceptual landscape](site/assets/riverflow-hero.png)

A programming language by **Ilangkhumanan Thirunavokkarasu**. AI assisted development, deterministic language rules, open source foundations.

RF² starts with a small executable promise: write typed, bounded computations, inspect their effects and run them locally. Core 0.1 includes a parser, semantic checks, JSON intermediate representation, interpreter, CLI, browser playground and MCP server. Its bootstrap is JavaScript with **no Python runtime dependency**.

[Try the playground](https://starkfiber.github.io/RiverFlow/rf2/) · [Language specification](docs/SPEC.md) · [Research foundation](docs/RESEARCH.md)

## Quick start

Requires Node 22 or newer.

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
