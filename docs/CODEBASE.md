# RiverFlow codebase map

## Execution and trust boundaries

```text
Trusted developer source (.rf2)
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
| Document UI | `native/workspace.rf2`, `native/editor.rf2`, `native/studio/` | Explicit file edits, PDF and local browser workspace |
| Reference tools | `bootstrap/`, `src/`, `bin/rf2.mjs` | Historical seed and independent developer controls |
| Native contracts | `examples/evidence-contract/` | Bounded research application, receipts and separate verifier |
| Browser experiment | `native/wasm/`, `examples/browser-lab/` | Bounded WASM backend and browser control |

Paths in this table are relative to the repository root. The runtime build script lists its composition order explicitly. The flat runtime modules are concatenated because this runtime retains its original shared namespace; converting them to separately linked modules is a separate compatibility project.

## Build and verify

1. Select an explicit qualified compiler, never an implicit download.
2. Use `tools/build-program.sh` for one program or `tools/build-runtime.sh` for the composed runtime.
3. Build into a new directory. Refusing overwrites is deliberate.
4. Run the relevant native acceptance tests with `RF2_TEST_COMPILER` set to the exact candidate.
5. For compiler changes, run `tests/standalone/compiler_verify.py` with `RF2_BOOTSTRAP_COMPILER` set to a qualified prior generator. Require fixed-point and independent reference agreement.
6. Keep raw failures and receipts under ignored `artifacts/` or `output/`; publish reviewed non-secret summary receipts under `docs/`.

Generated `docs/book/` mirrors `site/book/`. Edit `book/RiverFlow-First-Edition.md` and its generator when book work is requested. Do not hand-edit generated HTML. ThesisPro projects and private papers are outside this software checkout and are not release inputs.

## Repository organization decisions

The landing page routes users by task. Historical release narratives live in RESEARCH-HISTORY.md. CODEBASE.md owns the architecture map; native/compiler/README.md owns compiler internals; tools/README.md and tests/README.md explain development routes. Public file paths and frozen receipts remain in place so previous reproductions continue to work. No source was moved solely to change GitHub's language chart.
