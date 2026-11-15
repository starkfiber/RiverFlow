# RF2 delivery progress

`████████░░` **10/12 requested requirements complete (83%)**

This is the fixed delivery checklist reviewed with the owner on 15 November 2026. It counts accepted requirements equally, not engineering hours or universal language coverage. Partial implementations earn no completed-item credit. No sprint percentage is presented as product completion.

[Mission](PROJECT-CONTINUITY.md) · [Canonical ledger](PIPELINE.json) · [Current owned-field evidence](OWNED-VALUES-0.42.md)

| ID | State | Acceptance condition | Evidence and boundary |
| --- | --- | --- | --- |
| R01 | done | Owned text and u64 collection fields implemented and executed in an explicit candidate | [OWNED-VALUES-0.42.md](OWNED-VALUES-0.42.md) · Candidate scope only; stable compiler unchanged. |
| R02 | done | Local aggregate/field transfer and partial-failure cleanup executed in both compiler modes | [OWNED-VALUES-0.42.json](OWNED-VALUES-0.42.json) · Candidate scope only; stable compiler unchanged. |
| R03 | done | Ownership transfer and returns across function boundaries, including failure cleanup and escape refusals | [OWNED-FUNCTIONS-0.43.md](OWNED-FUNCTIONS-0.43.md), [OWNED-FUNCTIONS-0.43.json](OWNED-FUNCTIONS-0.43.json) · Bounded isolated candidate; conservative alias refusals and ordinary-return cleanup limitations remain explicit. |
| R04 | done | General nested owned records and collections of structured values with lifetime/cleanup tests | [NESTED-OWNERS-0.44.md](NESTED-OWNERS-0.44.md), [NESTED-OWNERS-0.44.json](NESTED-OWNERS-0.44.json) · Bounded recursive owned records and nominal flat-u64 structured rows; pointer-bearing row collections remain unimplemented. |
| R05 | done | Typed persistence, schemas and migrations with reopen/corruption/recovery tests | [TYPED-BOOKING-0.45.md](TYPED-BOOKING-0.45.md), [TYPED-BOOKING-0.45.json](TYPED-BOOKING-0.45.json) · Two strict Booking-specific codecs, explicit migration/recovery; no import of the older Workbench event journal. |
| R06 | done | Single-room Booking baseline operating through CLI and browser GUI | [BOOKING-STUDIO.md](BOOKING-STUDIO.md), [WORKBENCH-0.38-VERIFICATION.json](WORKBENCH-0.38-VERIFICATION.json) |
| R07 | done | Transactional multi-room Booking with overlap, simultaneous writers, failed saves and restart tests | [TYPED-BOOKING-0.45.md](TYPED-BOOKING-0.45.md), [TYPED-BOOKING-0.45.json](TYPED-BOOKING-0.45.json) · Cooperative single-file lock/CAS transactions across real native processes; no hostile same-user isolation or distributed database claim. |
| R08 | done | Reusable polished accessible UI components demonstrated in the real application | [TYPED-BOOKING-0.45.md](TYPED-BOOKING-0.45.md), [TYPED-BOOKING-0.45.json](TYPED-BOOKING-0.45.json) · Reusable RF2 HTML/CSS components, actual browser/keyboard inspection; no human learner or screen-reader trial. |
| R09 | done | Bounded Booking agent interface using the same typed business/storage logic as CLI and GUI | [TYPED-BOOKING-0.45.md](TYPED-BOOKING-0.45.md), [TYPED-BOOKING-0.45.json](TYPED-BOOKING-0.45.json) · Separate selected-journal agent, read-only by default. Existing nine-tool Core runtime unchanged. |
| R10 | done | Qualified downloadable compiler/application packages with fresh extraction and source-build checks | [TYPED-BOOKING-0.45.json](TYPED-BOOKING-0.45.json) · Development archive published by starkfiber, downloaded/hash-matched and freshly rebuilt; Apple Silicon Mac only, ad-hoc signed and not notarized. |
| R11 | active | Executed matched complete-development comparison against an established stack, retaining actual effort/usage and failures |  |
| R12 | pending | RiverFlow accepted in upstream GitHub Linguist; actual external acceptance verified | [LANGUAGE-REPORTING.md](LANGUAGE-REPORTING.md) · External adoption/review dependency; do not fabricate usage or acceptance. |

## Active implementation

R11: Freeze an equal complete-app task and available libraries, execute fresh matched development attempts, retain actual usage/effort and failures, then independently grade features. Genuine upstream Linguist recognition remains a separate external gate.

The eight longer-term platform gates and historical sprint evidence remain in PIPELINE.json. They do not produce extra completion badges. GitHub recognition depends on real external adoption and review; implementing a grammar or documenting requirements does not complete R12.

The renderer checks the fixed scope, states and local evidence-file existence. It does not independently validate every claim. Reaching the final item requires reviewing its actual acceptance evidence. Run `python3 tools/project-progress.py --check` to detect stale rendering.
