# Borrowed record composition experiment

Isolated candidate design retained for reproduction, not enabled in the released RF2 compiler. Baseline954762a199e1fc94e651f39fab87c2642bea71f8; current qualified compiler produces the experimental compiler. Run from a clean source checkout with a new artifacts/nested-039 directory:

```sh
mkdir -p artifacts/nested-039
python3 experiments/nested-records/prepare.py
sh tools/build-program.sh /absolute/qualified/rf2c artifacts/nested-039/compiler.flow artifacts/nested-039/compiler-build --opt
python3 experiments/nested-records/verify.py
```

prepare.py writes a separate compiler source, never replaces native/compiler/compiler.rf2. verify.py expects the new experimental compiler in that output directory and fresh probe destinations. Development Python is a controller, not a user runtime. macOS ARM64 only.

A field may refer to an earlier plain record type. The constructor takes a correctly typed, initialized borrowed record reference. Reading can traverse that relationship; a typed helper can mutate child leaves and the alias observes the change. Nested leaf updates such as `set booking.clock.finish=12` traverse checked field types; the receiver is preserved across RHS evaluation. Child rebinding and structured result payloads containing borrowed records refuse. Cyclic/forward fields and owned resource fields refuse.

This is borrowed composition, not nested inline value layout, deep copying, owner transfer or nested growable collections. Existing trusted raw-memory escape routes are not contained. General collection elements remain u64. Cache/reuse interaction, compiler fixed point, bootstrap agreement, full existing regressions, deeper lifetime/adversarial tests and independent review are not qualified for this candidate. Do not distribute it as a replacement compiler or claim general memory safety. The maintained compiler source and native bundles remain unchanged.

Twelve default/optimized admission controls ran; the admitted borrowed example was actually executed in both modes. See RESULTS.json. Further work should evaluate whether borrowed composition is the desired public design before freezing syntax; the roadmap still calls for a full value/ownership specification.

## Source extension sprint0.40

prepare.py now pins the baseline compiler source SHA-256, requires each assignment patch exactly once and refuses an existing generated compiler file. Pass an optional output directory to retain older experiment evidence. The extension adds nested scalar leaf assignment, including call-valued RHS and alias checks. The broader generated suite is tests/standalone/platform_sprint_verify.py; see docs/PLATFORM-SPRINT-0.40.md for final results. It remains a candidate, with no new owner transfer or generic collection element support.

## Booking value boundary, source sprint 0.41

`examples/booking-conflict.flow` is a borrowed nested-record application using the actual `examples/documents/lib/{datetime,text,io}.flow` modules. The acceptance controller copies only these reviewed dependencies into a fresh local fixture, compiles in both modes, compares conflicts with an independent Python date/interval oracle, and checks malformed inputs, closed output, nominal types, escape refusals and record boundaries.

```sh
RF2_NESTED_COMPILER=/absolute/experimental/compiler \
RF2_TEST_COMPILER=/absolute/qualified/baseline/rf2c \
python3 tests/standalone/application_values_verify.py
```

Run from the source root. The candidate is created through `prepare.py` and the explicit build route above. Do not compile the experimental example using a released compiler and count an unrelated missing-import refusal as type safety. The controller captures library/source/compiler hashes and retains raw results under ignored `artifacts/application-values-*`.

The prototype accepts six arguments: `DATE START END DATE START END`, with canonical Gregorian dates and `HH:MM` times. An end may be `24:00`; a start may not. Intervals must be nonempty, same-day and half-open. Output is `{"conflict":0}` or `{"conflict":1}`; invalid arguments and failed output exit 2 without success JSON. There are no journal or room-state writes. General owned values and the real Booking storage migration remain work; see docs/APPLICATION-VALUES.md and the progress tracker.
