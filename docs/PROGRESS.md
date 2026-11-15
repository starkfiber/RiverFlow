# RF2 delivery progress

`████░░░░░░` **5/12 requested requirements complete (41%)**

This is the fixed delivery checklist reviewed with the owner on 15 November 2026. It counts accepted requirements equally, not engineering hours or universal language coverage. Partial implementations earn no completed-item credit. No sprint percentage is presented as product completion.

[Mission](PROJECT-CONTINUITY.md) · [Canonical ledger](PIPELINE.json) · [Current owned-field evidence](OWNED-VALUES-0.42.md)

| ID | State | Acceptance condition | Evidence and boundary |
| --- | --- | --- | --- |
| R01 | done | Owned text and u64 collection fields implemented and executed in an explicit candidate | [OWNED-VALUES-0.42.md](OWNED-VALUES-0.42.md) · Candidate scope only; stable compiler unchanged. |
| R02 | done | Local aggregate/field transfer and partial-failure cleanup executed in both compiler modes | [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) · Candidate scope only; stable compiler unchanged. |
| R03 | done | Ownership transfer and returns across function boundaries, including failure cleanup and escape refusals | [OWNED-FUNCTIONS-0.43.md](OWNED-FUNCTIONS-0.43.md), [OWNED-FUNCTIONS-0.43.json](OWNED-FUNCTIONS-0.43.json) · Bounded isolated candidate; conservative alias refusals and ordinary-return cleanup limitations remain explicit. |
| R04 | done | General nested owned records and collections of structured values with lifetime/cleanup tests | [NESTED-OWNERS-0.44.md](NESTED-OWNERS-0.44.md), [NESTED-OWNERS-0.44.json](NESTED-OWNERS-0.44.json) · Bounded recursive owned records and nominal flat-u64 structured rows; pointer-bearing row collections remain unimplemented. |
| R05 | active | Typed persistence, schemas and migrations with reopen/corruption/recovery tests |  |
| R06 | done | Single-room Booking baseline operating through CLI and browser GUI | [BOOKING-STUDIO.md](BOOKING-STUDIO.md), [WORKBENCH-0.38-VERIFICATION.json](WORKBENCH-0.38-VERIFICATION.json) |
| R07 | pending | Transactional multi-room Booking with overlap, simultaneous writers, failed saves and restart tests |  |
| R08 | pending | Reusable polished accessible UI components demonstrated in the real application |  |
| R09 | pending | Bounded Booking agent interface using the same typed business/storage logic as CLI and GUI |  |
| R10 | pending | Qualified downloadable compiler/application packages with fresh extraction and source-build checks |  |
| R11 | pending | Executed matched complete-development comparison against an established stack, retaining actual effort/usage and failures |  |
| R12 | pending | RiverFlow accepted in upstream GitHub Linguist; actual external acceptance verified | [LANGUAGE-REPORTING.md](LANGUAGE-REPORTING.md) · External adoption/review dependency; do not fabricate usage or acceptance. |

## Active implementation

R05: Build versioned typed persistence for the actual Booking row model: strict schema/payload validation, reopen, migration, failed/uncertain commit and recovery controls. Then transactional multi-room CLI/GUI/agent delivery.

The eight longer-term platform gates and historical sprint evidence remain in PIPELINE.json. They do not produce extra completion badges. GitHub recognition depends on real external adoption and review; implementing a grammar or documenting requirements does not complete R12.

The renderer checks the fixed scope, states and local evidence-file existence. It does not independently validate every claim. Reaching the final item requires reviewing its actual acceptance evidence. Run `python3 tools/project-progress.py --check` to detect stale rendering.
