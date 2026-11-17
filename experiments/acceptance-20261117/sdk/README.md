# Small-field JSON path and native-loop benchmark

The earlier span writer measured a small escape-heavy report regression. Its
entry performed alias tests, and at32bytes scanned a prefix before calling the
original scalar writer. A32byte input can produce192bytes of escaped HTML, which
is then serialized as a second JSON field in the same complete report.

The candidate places the exact original scalar body directly in the public entry
for lengths0..256. It pays one size branch, with no alias scan, density probe or
extra scalar-wrapper call. Larger values retain the previous alias/density/span
route. The256threshold was selected from the tiny report's input/output bound
before any comparative timing, not selected from a winning benchmark sample.
Small aliases preserve the copied scalar behavior; larger aliases still delegate
to the original scalar function. The source package keeps the writer_json export.

`stage_sdk.py NEW-DIRECTORY` creates a fresh opt-in source package with a manifest.
It refuses a changed original SDK hash. It never edits the default SDK, stable
runtime, previous experiment, release or another checkout.

## Executed correctness

-8040 original non-benchmark controls pass in both compiler modes. The previous
 8760total included720benchmark-output checks; these are not silently counted as
 fresh performance evidence.
- Original73728alias states per mode pass unchanged. A separate172032-state
 boundary corpus covers31/32/33,63/64/65,127/128/129,255/256/257; it includes
 original cases, so the totals must not be summed as unique states.
- The unchanged Passage Desk grader passes80checks per mode.
- A native gettimeofday pointer/layout probe falls within a host UTC envelope.
 This proves timer plumbing, not clock monotonicity or a performance benefit.

Raw receipts: `artifacts/acceptance-20261117/sdk/correctness2/RESULTS.json`, its
append-only CHECKS.jsonl, `integration2/INTEGRATION.json`, and `timer-probe/`.
The first direct64-byte candidate also passed8040controls and is retained as
candidate-64.flow; it was not timed or promoted.

## Benchmark protocol

`benchmark.py --compiler PINNED-COMPILER --out NEW-EVIDENCE-DIRECTORY` prepares
source, fixture, SDK and controller identities and performs one-iteration output
smokes. `--measure` on that directory runs once, only after the parent grants an
exclusive sprint timing slot. The parent pauses other local sprint CPU work;
unrelated Mac background load remains outside that control.

The final prepared campaign is benchmark-r3. R2 was preparation only, and was
superseded before measurement to bind controller/oracle/template identities as
well. There are no comparative results in either preparation receipt.

The benchmark executes31shuffled paired process trials for each input shape and
compiler mode. Tiny profiles also include the earlier span writer, preserving the
old comparator rather than claiming a regression disappeared from source review.
Every process performs16untimed warm-up iterations and an explicit bounded number
of measured report serializations. It consumes output length and boundary bytes
each iteration and publishes the final complete report, independently checked.

Native-loop elapsed time comes from Darwin gettimeofday in microseconds and is
wall time, not CPUcycles or a monotonic guarantee. Read, initial HTML conversion,
warmups and output are outside that interval. The controller separately retains
an enclosing monotonic process measurement. A backward clock, native duration
outside the enclosing clock+2ms allowance, invalid output or bad checksum stops
the campaign without automatic retry. Raw outliers remain in the31samples.

The tiny-input acceptance criterion is a paired median candidate/baseline ratio
at most1.03, paired-bootstrap95% upper bound at most1.05, and at least50ms of
native-loop work in every compared small sample. Bootstrap uses10000resamples
with a fixed seed; it does not certify every workload or future hardware.

The first frozen campaign completed once in699.116seconds, with all12small gates
passing and identical preparation/measurement program hashes. Complete30-profile
results, native versus enclosing-process scope, same-run prior comparator and
retained large escape-heavy losses are in REPORT.md. The optimized16KiBescaped
case is about2.8%slower; do not call the candidate universally regression-free.

## Cache and scope

Invoke substantial checks through the guarded local bank with stable label
rf2-sdk-accept after checking its status. Rebuildable native binaries explicitly
use supplied TMPDIR. Sources, unique inputs, frozen manifests, results and logs
stay in project-owned persistent paths. Passage Desk's expected ./app is only a
local link to the rebuildable cached binary; its source and grader evidence stay
persistent. Missing cache files are rebuilt, not treated as unique evidence loss.

No KHC offload is claimed: these checks require native Darwin execution and the
project's retained shared-job boundary is unverified. No remote Memory, company
service, network request, GitHub write or stable mutation occurs in this task.
