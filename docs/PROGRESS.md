# RF2 development progress

Generated from [PIPELINE.json](PIPELINE.json). Progress counts the declared acceptance checks below, not language coverage, market leadership or universal platform readiness.

[Mission and continuity](PROJECT-CONTINUITY.md) · [RF2 everywhere](RF2-EVERYWHERE.md) · [Typed application values](APPLICATION-VALUES.md)

## Platform expansion gates

`░░░░░░░░░░` **0/8 complete (0%)**

| ID | State | Acceptance condition | Evidence / current boundary |
| --- | --- | --- | --- |
| G1 | active | Qualified nested owned application values, transfer and cleanup | [APPLICATION-VALUES.md](APPLICATION-VALUES.md) · References describe current boundaries; this gate is not complete. |
| G2 | pending | Signed/floating numerical contract and edge-case conformance | [RF2-EVOLUTION.md](RF2-EVOLUTION.md) · References describe current boundaries; this gate is not complete. |
| G3 | pending | Typed persistence, migration and uncertain-save recovery | [RF2-EVOLUTION.md](RF2-EVOLUTION.md) · References describe current boundaries; this gate is not complete. |
| G4 | pending | Versioned reusable SDK and repeatable package builds | [RF2-EVERYWHERE.md](RF2-EVERYWHERE.md) · References describe current boundaries; this gate is not complete. |
| G5 | pending | General Systems Studio and first-time learner acceptance | [BOOKING-STUDIO.md](BOOKING-STUDIO.md) · References describe current boundaries; this gate is not complete. |
| G6 | pending | A second qualified general application platform | [CAPABILITY-MAP.md](CAPABILITY-MAP.md) · References describe current boundaries; this gate is not complete. |
| G7 | pending | Structured concurrency and a qualified RU’OS component | [RF2-EVERYWHERE.md](RF2-EVERYWHERE.md) · References describe current boundaries; this gate is not complete. |
| G8 | pending | Matched complete-task comparisons with actual usage and failures | [RF2-PLATFORM-RESEARCH.md](RF2-PLATFORM-RESEARCH.md) · References describe current boundaries; this gate is not complete. |

## Current sprint: Durable pipeline and borrowed Booking values

`██████████` **6/6 complete (100%)**

| ID | State | Acceptance condition | Evidence / current boundary |
| --- | --- | --- | --- |
| S1 | done | Record owner mission, anti-drift rules and next priorities (documentation) | [PROJECT-CONTINUITY.md](PROJECT-CONTINUITY.md) |
| S2 | done | Render progress; reject stale output and unsupported completion states (developer tooling) | [project-progress.py](../tools/project-progress.py), [APPLICATION-VALUES-0.41.json](APPLICATION-VALUES-0.41.json) |
| S3 | done | Specify owned application-value acceptance rules without claiming implementation (design) | [APPLICATION-VALUES.md](APPLICATION-VALUES.md) |
| S4 | done | Execute borrowed Booking conflict cases with an independent date/interval oracle | [booking-conflict.flow](../experiments/nested-records/examples/booking-conflict.flow), [APPLICATION-VALUES-0.41.json](APPLICATION-VALUES-0.41.json) |
| S5 | done | Execute nominal/escape/init/boundary refusals and closed-output failures in both modes | [application_values_verify.py](../tests/standalone/application_values_verify.py), [APPLICATION-VALUES-0.41.json](APPLICATION-VALUES-0.41.json) |
| S6 | done | Record actual results, failures and remaining promotion gates in a source-bound receipt | [APPLICATION-VALUES-0.41.json](APPLICATION-VALUES-0.41.json), [APPLICATION-VALUES-0.41.md](APPLICATION-VALUES-0.41.md) |

## Read these counters correctly

Platform expansion counts the eight new gates from the roadmap. Its zero completed gates does not erase the existing compiler, applications, libraries, MCP tools or emulator evidence. Active work is visible but earns no completed-gate credit.

The current sprint counts only its named deliverables. A design/documentation check is labelled as such. Passing borrowed-record examples does not complete general owned values. Reaching 100% of this sprint does not mean RF2 runs everywhere.

The generator validates IDs, states and local evidence-file existence. It does not independently endorse the evidence or inspect every claim. Reviewers must inspect the linked result and its limitations. Run `python3 tools/project-progress.py --check` from the repository root to detect stale rendering.
