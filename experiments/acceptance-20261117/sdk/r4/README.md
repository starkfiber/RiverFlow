# Direct-fallback JSON writer candidate (R4)

This isolated candidate keeps the original scalar writer body directly in the public entry for every length. Inputs above 256 bytes first call a leaf alias/density eligibility predicate; only eligible sparse disjoint inputs enter the span writer. The R3 and original scalar SDK remain unchanged.

Correctness is recorded separately in `artifacts/acceptance-20261117/sdk/r4-correctness` (8,040 original oracle controls), and `r4-integration` (original 73,728 alias states per mode, overlapping 172,032 boundary states per mode, unchanged Passage Desk 80 checks per mode). These finite controls establish this tested corpus, not universal correctness.

`clock_maps.py` verifies eleven checked tick-scaling cases and native clock availability in plain/optimized builds. It persists function maps and instruction counts to show that the eligibility predicate is a leaf; this is source/assembly evidence, not a speed claim. Two failed preparation attempts remain under `r4-clock-maps` and `r4-clock-maps-r2`: the former incorrectly expected Mach-O sections; the latter used an invalid Writer constructor in its probe. `r4-clock-maps-r3` corrects both without altering the candidate.

`benchmark.py` uses the same `vm_clock_ticks` / Mach monotonic clock and checked timebase scaling for baseline, R3 and R4. Tick subtraction precedes scaling; invalid ratio, overflow and backward ticks fail. Controller monotonic time encloses each process and bounds the native duration. Native elapsed excludes startup, input and HTML preprocessing, warmups and final output; the enclosing process measure includes them. Neither is CPU-cycle measurement.

The frozen campaign has 26 nonduplicate profiles: empty once per mode, then 32 bytes / 1 KiB / 16 KiB / 256 KiB with ordinary, mixed and escape-heavy bytes, in plain and optimized modes. Baseline-only warmup calibrates each to approximately 100 ms, then freezes the same repeat count for all three variants before comparisons. Thirty-one shuffled paired trials retain every result and validate complete output and consumed state. Paired bootstrap 95% intervals use fixed seeds. No trial dropping, automatic retry or campaign rerun for winner selection.

Small acceptance requires R4/baseline median ratio <=1.03, upper 95% <=1.05, minimum native duration >=50 ms. The known optimized 16 KiB escaped regression additionally requires R4/R3 upper 95% <=1.0. Failed or inconclusive gates reject promotion; no all-cases-faster claim follows from passing these gates. Preparation and measurement source/program identities are bound and compared.

Reproduce using the pinned compiler and cache wrapper documented by the parent project. `--baseline-record` points at the preserved R3 results only for initial iteration estimates; live calibration is baseline-only. Run without `--measure` first; measurement requires the coordinated exclusive CPU slot. A `STARTED.json` campaign cannot be reused.
