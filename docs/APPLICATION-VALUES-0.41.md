# Foundation sprint 0.41: continuity and borrowed Booking values

15 November 2026. Baseline `60d301537c6c7fb3cd25153eb56d478bf4d1fca3`. This is a source/example and developer-tool sprint, not a new compiler release. [Machine-readable qualification](APPLICATION-VALUES-0.41.json) binds source, compiler and dependency identities.

## Outcomes

The owner’s cross-platform RF2 direction, competitive goals and anti-drift rules now live in [project continuity](PROJECT-CONTINUITY.md). The [pipeline](PIPELINE.json) and generated [progress view](PROGRESS.md) separate a bounded sprint from the eight larger platform expansion gates. Root AGENTS.md directs future repository work to these files. No remote memory service or unattended worker was configured.

The [application-value contract](APPLICATION-VALUES.md) specifies twelve acceptance requirements for ownership, partial construction, transfer, cleanup and persistence. They remain design requirements. The compiler candidate still implements borrowed nesting only.

A new [Booking conflict prototype](../experiments/nested-records/examples/booking-conflict.flow) uses the real date/time, text and I/O libraries. Two nominal ReservationValue records borrow TimeWindow records. The program validates dates and intervals, computes conflicts and reports a scalar result. It makes no reservation or journal changes and does not replace the existing Booking app.

## Executed evidence

| Check | Result | Scope |
| --- | ---: | --- |
| Native application/value controller | 687 passed assertions | Builds, execution, errors and refusals; not 687 distinct users or experiments |
| Date/interval oracle comparisons | 606 native executions | 303 inputs in each mode; generated and boundary cases, compared with independent Python date/interval expectations |
| Invalid CLI inputs | 18 refusals | Nine inputs in each mode; no success output |
| Closed standard output | 2 failures handled | One per mode; not arbitrary I/O-fault coverage |
| Nominal/initialization/escape rules | 16 compiler refusals | Eight cases in each mode; specific diagnostic and no output executable checked |
| Deep/wide record boundaries | 8 native executions | Four shapes per mode, including depth 31 and width 16; alias and single-evaluation checks |
| Existing heap ownership/fault controls | 78 passed | Test-only fault injections remain labelled; no real host OOM claim |
| Existing shared collection applications | 308 passed | Both application/library regression routes |
| Progress-tool controls | 8 passed | Rendering, staleness, missing/outside evidence, duplicate IDs and unknown states |
| Existing native MCP | 9 tools retained | Systems prototype refused; subsequent valid bounded sum returned 6 |

A fresh isolated candidate was rebuilt and matched the previously qualified candidate byte-for-byte. The native acceptance and regression executions bind to that exact candidate identity. The maintained compiler, stable downloads and MCP executable were not modified. These checks do not close the broader compiler/ABI/cache/independent-encoder promotion requirements.

## Failures and corrections

The first baseline probe tried the experimental example without its copied library fixture and got a missing-module refusal. That could not establish type safety. The controller now checks a dependency-resolved copy and requires the actual unsupported-child-type diagnostic. Two expected-diagnostic assertions were corrected to match the existing compiler’s precise messages. Admission expectations and expected program results were not weakened; initial failed reports remain local.

No new compiler defect was reproduced by the completed corpus. That result is limited to these cases. General owned-value behavior is not implemented and cannot be counted as passing by refusing its syntax.

## Reproduce

From the repository root, select an existing qualified native Mac compiler explicitly. Use new output directories:

```sh
python3 experiments/nested-records/prepare.py artifacts/values-reproduction/source
sh tools/build-program.sh /absolute/qualified/rf2c artifacts/values-reproduction/source/compiler.flow artifacts/values-reproduction/compiler --opt
RF2_NESTED_COMPILER="$PWD/artifacts/values-reproduction/compiler/program" RF2_TEST_COMPILER=/absolute/qualified/rf2c python3 tests/standalone/application_values_verify.py
python3 tools/project-progress.py --check
```

The Python program is development verification tooling. Native execution uses RF2-produced binaries. The acceptance controller snapshots only the three reviewed shared library files, retains their hashes and never silently builds/downloads a tool or writes a journal. Raw reports live under ignored `artifacts/`.

## Next decisive gate

Specify actual owned layout, move/return, borrow lifetimes and partial-cleanup state, then implement an isolated candidate with fault-injected acceptance pairs. Only afterward migrate a real Booking data structure and preserve or explicitly migrate its journal schema. Keep this prototype and all failures as regression controls. No speed, token, energy, learner, hardware, independent approval or universal portability result is claimed.
