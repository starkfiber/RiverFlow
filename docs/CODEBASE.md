# RiverFlow codebase map

## Execution and trust boundaries

```text
Trusted developer source (.flow / .rf2)
    -> native/compiler/compiler.rf2
    -> ARM64 Mach-O executable
    -> explicit OS signing -> local execution

AI host -> native MCP runtime -> bounded Core / versioned application tools
    -> checked results; no arbitrary systems compilation or file/network authority

Independent developer controllers -> native executables -> retained receipts
```

The compiler and MCP runtime are separate execution routes. Never expose the trusted systems compiler through the bounded Core endpoint.

## Source ownership

| Area | Entry point | Responsibility |
| --- | --- | --- |
| Native compiler | `native/compiler/compiler.rf2` | Lexing, semantic checks, ARM64 emission and Mach-O layout |
| Native target cache | `native/build/incremental.rf2` | Explicit dependency snapshots and verified whole-image reuse; separate from MCP |
| Runtime entry | `native/rf2.rf2` | CLI/MCP transport and dispatch |
| Checked execution | `native/core.rf2` | Bounded Core semantics |
| Application capabilities | `native/attendance.rf2`, `native/invoice.rf2`, `native/prepared.rf2` | Schemas, checked totals and prepared handles |
| Read-only document workspace | `examples/documents/workspace.flow`, `examples/documents/lib/` | Shared text/table libraries, explicit corpus snapshot, bounded native browser reader and CLI |
| Booking and learning Studio | `examples/documents/booking.flow`, `booking-web.flow`, `studio.flow` and `lib/` | Shared date/time, journal and forms; bounded Core editor; see [Workbench](BOOKING-STUDIO.md) |
| Source experiment | `experiments/nested-records/` | Isolated borrowed-record candidate; no automatic release migration |
| Learning and examples | `book/learning-edition-1/`, `examples/README.md` | Runnable lessons and task/profile-based catalogue |
| Document UI | `native/workspace.rf2`, `native/editor.rf2`, `native/studio/` | Explicit file edits, PDF and local browser workspace |
| Reference tools | `bootstrap/`, `src/`, `bin/rf2.mjs` | Historical seed and independent developer controls |
| Native contracts | `examples/evidence-contract/` | Bounded research application, receipts and separate verifier |
| Browser experiment | `native/wasm/`, `examples/browser-lab/` | Bounded WASM backend and browser control |

Paths in this table are relative to the repository root. The runtime build script lists its composition order explicitly. The flat runtime modules are concatenated because this runtime retains its original shared namespace; converting them to separately linked modules is a separate compatibility project.

## Build and verify

1. Select an explicit qualified compiler, never an implicit download.
2. Start with `sh tools/dev.sh doctor` and [the first-app tutorial](FIRST-APP.md). The helper selects native binaries explicitly and delegates to existing routes. Use `tools/build-program.sh` for one program or `tools/build-runtime.sh` for the composed runtime.
3. Build into a new directory. Refusing overwrites is deliberate.
4. Run the relevant native acceptance tests with `RF2_TEST_COMPILER` set to the exact candidate.
5. For compiler changes, run `tests/standalone/compiler_verify.py` with `RF2_BOOTSTRAP_COMPILER` set to a qualified prior generator. Require fixed-point and independent reference agreement.
6. Keep raw failures and receipts under ignored `artifacts/` or `output/`; publish reviewed non-secret summary receipts under `docs/`.

Generated `docs/book/` mirrors `site/book/`; its source is `book/RiverFlow-First-Edition.md`. The learning edition source is `book/learning-edition-1/README.md`; `tools/book/build-learning.mjs` emits its local HTML and both `docs/learn/` and `site/learn/` mirrors. Edit the source and appropriate generator when book work is requested; do not hand-edit generated HTML. GitHub Pages uses `docs/`. ThesisPro projects and private papers are outside this software checkout and are not release inputs.

## Repository organization decisions

The landing page routes users by task. Historical release narratives live in RESEARCH-HISTORY.md. CODEBASE.md owns the architecture map; native/compiler/README.md owns compiler internals; tools/README.md and tests/README.md explain development routes. Public file paths and frozen receipts remain in place so previous reproductions continue to work. No source was moved solely to change GitHub's language chart.

## Where files belong

| Category | Canonical home | Keep separate |
| --- | --- | --- |
| Maintained native implementation | `native/` | Historical seeds/references in `bootstrap/`, `src/`, `bin/` |
| Runnable reusable programs | `examples/` and its [catalogue](../examples/README.md) | Unreleased compiler candidates in `experiments/` |
| Tests and independent controls | `tests/` | Explicit build, benchmark and publishing controllers in `tools/` |
| API contracts and reviewed public evidence | `docs/`, indexed by [documentation](README.md) | Private/raw execution output under ignored `artifacts/`, `output/`, `.whatif/` |
| Native MCP integration | `plugin/` | Host discovery manifests under `.codex-plugin/` and `.agents/plugins/` |
| Edition sources | `book/` | Generated readers in `docs/` and `site/`; don't edit copies |
| Versioned downloadable packages | `dist/<version>/` | Current package selection in [Start here](START-HERE.md); retain old receipts |

Root files provide identity, licensing, contribution rules and developer-reference dependencies. `package.json` describes the JavaScript reference tooling, not a requirement for native users. Directory size or language percentages do not decide whether a file is obsolete. Before moving/removing a public path, inspect imports, build composition, package manifests, tests and external reproduction links; supply a versioned migration when needed.

[Language reporting](LANGUAGE-REPORTING.md) defines generated-output rules and inventory regeneration. [RF2 everywhere](RF2-EVERYWHERE.md) records the maintainer's destination goals without claiming unimplemented targets.
