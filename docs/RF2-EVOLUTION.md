# RF2 evolution specification, first working draft

Original design baseline: commit954762a199e1fc94e651f39fab87c2642bea71f8, Workbench0.38. Updated15November2026 against the source-pinned0.43/0.44 ownership work and qualified0.45 Booking development bundle. Stable Core/MCP runtime0.17 remains distinct. This specification evolves existing RF2 rather than restarting the language. Preserve .flow, current block syntax, direct native backends and historical test receipts. New semantics require versioned acceptance tests and a migration explanation.

## Mission and success

Help humans and AI build useful applications with understandable source, predictable permissions and recoverable failures. Native output is an implementation property. Practical advantage needs matched complete-task evidence: correctness, developer effort, installation, latency, memory and actual model usage. There is no universal speed or token target already achieved.

## Status vocabulary

Implemented means source/mechanism exists. Experimentally verified names an executed corpus, host and artifact; it never means universal correctness. Proposed names a design without implementation. A feature can be implemented and experimentally verified within a restricted scope. The API must not advertise proposed operations as available.

| Contract | Present rule | Evidence/status | Next gate |
| --- | --- | --- | --- |
| Numeric meaning | Systems unsigned words; Core checked/wrapping u32 | Implemented; local arithmetic probes and native Core receipts | Specify signed widths/conversions/overflow and floating-point policy before adding syntax |
| Values | Recursive inline owned records, owned text/collections and nominal flat-u64 row collections | Qualified bounded0.44 compiler in0.45 development bundle; [receipt](NESTED-OWNERS-0.44.md) | Pointer-bearing row collections and broader generic value forms remain open |
| Ownership | Explicit consuming parameters, caller-owned result storage, subtree moves and ordinary-return cleanup | [0.43 function ownership](OWNED-FUNCTIONS-0.43.md), [0.44 nested ownership](NESTED-OWNERS-0.44.md) | Broader alias/lifetime models, persistent OS refusal, signals/traps and raw interference remain limits |
| Modules | Entry-root local source graph and shared namespace | Implemented | Public names/interfaces, repeatable package/version resolution |
| Storage | Typed versioned full snapshots, explicit migration/recovery and lock/CAS multi-room transactions | [0.45 CLI/browser/agent evidence](TYPED-BOOKING-0.45.md); controlled faults, not actual power-loss tests | General schema/migration language, compaction and broader database targets remain open |
| Effects | Nine original bounded runtime tools; separate launch-selected Booking read/write tools | Existing SDK checks plus [0.45 agent qualification](TYPED-BOOKING-0.45.md) | General capability-contract framework remains work; no arbitrary Systems admission |
| Concurrency | OS processes/locks and polling in apps | Implemented app mechanisms, not a language task model | Proposed structured tasks: lifetimes, data races, cancellation and joins |
| Platforms | Mac ARM64 apps; separate bounded ESP32-C3 backend | Native/emulator evidence; no physical board qualification | Each target needs actual backend, ABI, runtime and acceptance executions |
| General project Studio | Core teaching editor exists | Implemented; bounded editor tests | Proposed systems project editing, explicit build/run approval, diagnostics/test runner |
| Shared typed IR | Bounded Core IR exists; systems/backend unification not established | Broader shared IR proposed | Preserve behavior in differential tests before replacing direct paths |

## Answers the language must make explicit

Subtraction below zero follows the selected number contract, not familiar spelling from another language. Current systems comparison is unsigned. The0.43/0.44 compiler supports explicit consuming parameters and typed owned results, not implicit owner copying. Recursive inline owned records are bounded and qualified in the0.45 development bundle; arbitrary pointer-bearing row storage is not implemented. A failed save can have a verified rollback or an uncertain outcome. Tool timeout is not universal asynchronous cancellation. Raw syscalls are trusted, not a whole-language memory-safety guarantee.

## Ordered implementation checklist

- [x] Qualify bounded nested scalar/owned record layout, initialization, field access and refusal cases in the explicit development candidate.
- [x] Qualify owned text/collection fields, explicit function transfer/return and partial cleanup within the documented bounds.
- [ ] Provide typed maps, iteration and schema-checked serialization shared by CLI/GUI.
- [ ] Specify numeric signed/floating semantics and independent edge-case oracles.
- [x] Use typed Booking rows and explicitly version the new storage codec. The older Workbench RF2BOOK1 journal is refused; no historical importer is claimed.
- [x] Execute cooperative transactional multi-room storage with competing writers, reopen and explicit recognized-tail recovery. Controlled failure tests do not prove real power-loss durability.
- [ ] Expand Studio to general projects without routing unrestricted source through Core/MCP.
- [ ] Design structured concurrency and qualify each target separately.
- [x] Execute the scoped four-attempt complete-app SDK construction task, preserving failures and actual usage/effort. General productivity advantage and stricter model-pinned comparisons remain open.

Each box requires design, implementation, executable example, refusal/boundary tests, documentation and a version-bound receipt. Teaching coverage does not complete an engineering box. No reset to a fictional v0.1 or Rust/LLVM rewrite is adopted. Alternative backends may be investigated if they solve a measured problem; they are not prerequisites imposed by this document.

## Educational acceptance

A new learner should be able to install the stated package, explain the Core/systems boundary, predict a result, diagnose one refusal and operate Booking while understanding its storage limits. The first learning edition includes exercises for these goals; a real learner usability trial is still needed. AI-assisted editorial review is not an external academic council.

## Delivery and education status

The fixed [twelve-item owner ledger](PROGRESS.md) remains authoritative for delivery progress. The0.45 public archive was downloaded and rebuilt from its included native source. The [four-attempt SDK construction experiment](SDK-CONSTRUCTION-0.45.md) is complete; it did not establish RF2 model-usage or complete-development advantage. The [editor grammar](../editors/vscode/README.md) adds lexical support and snippets, not a general IDE or GitHub language acceptance. The original unanswered platform/numeric/concurrency and actual learner gates stay open.
