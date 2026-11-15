# RF2 evolution specification, first working draft

Baseline: commit954762a199e1fc94e651f39fab87c2642bea71f8, Workbench0.38; unchanged Core/MCP runtime0.17. This specification evolves existing RF2 rather than restarting the language. Preserve .flow, current block syntax, direct native backends and historical test receipts. New semantics require versioned acceptance tests and a migration explanation.

## Mission and success

Help humans and AI build useful applications with understandable source, predictable permissions and recoverable failures. Native output is an implementation property. Practical advantage needs matched complete-task evidence: correctness, developer effort, installation, latency, memory and actual model usage. There is no universal speed or token target already achieved.

## Status vocabulary

Implemented means source/mechanism exists. Experimentally verified names an executed corpus, host and artifact; it never means universal correctness. Proposed names a design without implementation. A feature can be implemented and experimentally verified within a restricted scope. The API must not advertise proposed operations as available.

| Contract | Present rule | Evidence/status | Next gate |
| --- | --- | --- | --- |
| Numeric meaning | Systems unsigned words; Core checked/wrapping u32 | Implemented; local arithmetic probes and native Core receipts | Specify signed widths/conversions/overflow and floating-point policy before adding syntax |
| Values | Scalar-field records, fixed arrays, limited structured results | Implemented, versioned type/frame tests | Nested typed values without raw-pointer disguises; layout/alias/initialization tests |
| Ownership | Scoped files/vectors; local move/borrow for bounded u64 collections | Implemented with known limits | Cross-function transfer/return, nested cleanup and partial-failure semantics |
| Modules | Entry-root local source graph and shared namespace | Implemented | Public names/interfaces, repeatable package/version resolution |
| Storage | Cooperative locked append/replay with uncertain outcomes | Implemented in Booking; finite race/write-failure tests | Transactional multi-room save, migration, crash/recovery, compaction contract |
| Effects | Core reads supplied numbers; nine MCP tools with fixed schemas | Implemented; MCP refusal checks | Explicit capability contracts for new application tools, no silent systems execution |
| Concurrency | OS processes/locks and polling in apps | Implemented app mechanisms, not a language task model | Proposed structured tasks: lifetimes, data races, cancellation and joins |
| Platforms | Mac ARM64 apps; separate bounded ESP32-C3 backend | Native/emulator evidence; no physical board qualification | Each target needs actual backend, ABI, runtime and acceptance executions |
| General project Studio | Core teaching editor exists | Implemented; bounded editor tests | Proposed systems project editing, explicit build/run approval, diagnostics/test runner |
| Shared typed IR | Bounded Core IR exists; systems/backend unification not established | Broader shared IR proposed | Preserve behavior in differential tests before replacing direct paths |

## Answers the language must make explicit

Subtraction below zero follows the selected number contract, not familiar spelling from another language. Current systems comparison is unsigned. Owned collections cannot currently be returned freely. Records do not currently contain arbitrary nested owned data. A failed save can have a verified rollback or an uncertain outcome. Tool timeout is not universal asynchronous cancellation. Raw syscalls are trusted, not a whole-language memory-safety guarantee.

## Ordered implementation checklist

- [ ] Define nested scalar record layout and field access, including initialization, borrowing and refusal cases.
- [ ] Extend the model to owned text/collection fields only after specifying move, return and partial cleanup.
- [ ] Provide typed maps, iteration and schema-checked serialization shared by CLI/GUI.
- [ ] Specify numeric signed/floating semantics and independent edge-case oracles.
- [ ] Replace Booking's manual data packing with typed application values where implemented; preserve journal compatibility or version it explicitly.
- [ ] Design transactional multi-room storage and demonstrate competing writers and restart recovery.
- [ ] Expand Studio to general projects without routing unrestricted source through Core/MCP.
- [ ] Design structured concurrency and qualify each target separately.
- [ ] Run a matched full application build task against an established stack, keeping failures and actual effort receipts.

Each box requires design, implementation, executable example, refusal/boundary tests, documentation and a version-bound receipt. Teaching coverage does not complete an engineering box. No reset to a fictional v0.1 or Rust/LLVM rewrite is adopted. Alternative backends may be investigated if they solve a measured problem; they are not prerequisites imposed by this document.

## Educational acceptance

A new learner should be able to install the stated package, explain the Core/systems boundary, predict a result, diagnose one refusal and operate Booking while understanding its storage limits. The first learning edition includes exercises for these goals; a real learner usability trial is still needed. AI-assisted editorial review is not an external academic council.
