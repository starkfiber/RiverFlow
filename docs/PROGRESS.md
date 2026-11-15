# RF2 development progress

Generated from [PIPELINE.json](PIPELINE.json). Progress counts the declared acceptance checks below, not language coverage, market leadership or universal platform readiness.

[Mission and continuity](PROJECT-CONTINUITY.md) · [RF2 everywhere](RF2-EVERYWHERE.md) · [Typed application values](APPLICATION-VALUES.md)

## Platform expansion gates

`░░░░░░░░░░` **0/8 complete (0%)**

| ID | State | Acceptance condition | Evidence / current boundary |
| --- | --- | --- | --- |
| G1 | active | Qualified nested owned application values, transfer and cleanup | [APPLICATION-VALUES.md](APPLICATION-VALUES.md), [OWNED-VALUES-0.42.md](OWNED-VALUES-0.42.md) · Owned text/collection fields and local moves now have isolated native evidence. Owner returns, transfer parameters and release qualification remain open. |
| G2 | pending | Signed/floating numerical contract and edge-case conformance | [RF2-EVOLUTION.md](RF2-EVOLUTION.md) · References describe current boundaries; this gate is not complete. |
| G3 | pending | Typed persistence, migration and uncertain-save recovery | [RF2-EVOLUTION.md](RF2-EVOLUTION.md) · References describe current boundaries; this gate is not complete. |
| G4 | pending | Versioned reusable SDK and repeatable package builds | [RF2-EVERYWHERE.md](RF2-EVERYWHERE.md) · References describe current boundaries; this gate is not complete. |
| G5 | pending | General Systems Studio and first-time learner acceptance | [BOOKING-STUDIO.md](BOOKING-STUDIO.md) · References describe current boundaries; this gate is not complete. |
| G6 | pending | A second qualified general application platform | [CAPABILITY-MAP.md](CAPABILITY-MAP.md) · References describe current boundaries; this gate is not complete. |
| G7 | pending | Structured concurrency and a qualified RU’OS component | [RF2-EVERYWHERE.md](RF2-EVERYWHERE.md) · References describe current boundaries; this gate is not complete. |
| G8 | pending | Matched complete-task comparisons with actual usage and failures | [RF2-PLATFORM-RESEARCH.md](RF2-PLATFORM-RESEARCH.md) · References describe current boundaries; this gate is not complete. |

## Current sprint: Owned text and collection fields, isolated candidate

`██████████` **6/6 complete (100%)**

| ID | State | Acceptance condition | Evidence / current boundary |
| --- | --- | --- | --- |
| O1 | done | Implement nominal Unicode text and explicitly owned text/collection fields | [compiler-extension.flow](../experiments/owned-values/compiler-extension.flow), [prepare.py](../experiments/owned-values/prepare.py), [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) |
| O2 | done | Implement local aggregate transfer and per-field automatic cleanup without duplicate owners | [compiler-extension.flow](../experiments/owned-values/compiler-extension.flow), [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) |
| O3 | done | Run a real labelled-batch application against independent text/numeric expectations | [owned-batch.flow](../experiments/owned-values/examples/owned-batch.flow), [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) |
| O4 | done | Execute invalid Unicode, ownership refusals and allocation/retirement/partial-construction faults in both modes | [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) |
| O5 | done | Run relevant prior regressions and verify bounded MCP authority | [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) |
| O6 | done | Record source-bound findings and remaining promotion gates, then review for SFE publication | [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json), [OWNED-VALUES-0.42.md](OWNED-VALUES-0.42.md) |

## Read these counters correctly

Platform expansion counts the eight new gates from the roadmap. Its zero completed gates does not erase the existing compiler, applications, libraries, MCP tools or emulator evidence. Active work is visible but earns no completed-gate credit.

The current sprint counts only its named deliverables. A design/documentation check is labelled as such. Passing borrowed-record examples does not complete general owned values. Reaching 100% of this sprint does not mean RF2 runs everywhere.

The generator validates IDs, states and local evidence-file existence. It does not independently endorse the evidence or inspect every claim. Reviewers must inspect the linked result and its limitations. Run `python3 tools/project-progress.py --check` from the repository root to detect stale rendering.
