# Borrowed record composition experiment

Private-candidate design now retained for reproduction, not enabled in the released RF2 compiler. Baseline954762a199e1fc94e651f39fab87c2642bea71f8; current qualified compiler produces the experimental compiler. Run from a clean source checkout with a new artifacts/nested-039 directory:

```sh
mkdir -p artifacts/nested-039
python3 experiments/nested-records/prepare.py
sh tools/build-program.sh /absolute/qualified/rf2c artifacts/nested-039/compiler.flow artifacts/nested-039/compiler-build --opt
python3 experiments/nested-records/verify.py
```

prepare.py writes a separate compiler source, never replaces native/compiler/compiler.rf2. verify.py expects the new experimental compiler in that output directory and fresh probe destinations. Development Python is a controller, not a user runtime. macOS ARM64 only.

A field may refer to an earlier plain record type. The constructor takes a correctly typed, initialized borrowed record reference. Reading can traverse that relationship; a typed helper can mutate child leaves and the alias observes the change. Child rebinding and structured result payloads containing borrowed records refuse. Cyclic/forward fields and owned resource fields refuse.

This is borrowed composition, not nested inline value layout, deep copying, owner transfer or nested growable collections. Existing trusted raw-memory escape routes are not contained. General collection elements remain u64. Cache/reuse interaction, compiler fixed point, bootstrap agreement, full existing regressions, deeper lifetime/adversarial tests and independent review are not qualified for this candidate. Do not distribute it as a replacement compiler or claim general memory safety. The maintained compiler source and native bundles remain unchanged.

Twelve default/optimized admission controls ran; the admitted borrowed example was actually executed in both modes. See RESULTS.json. Further work should evaluate whether borrowed composition is the desired public design before freezing syntax; the roadmap still calls for a full value/ownership specification.
