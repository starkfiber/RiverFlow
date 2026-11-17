# RF2Net native DHCP parser: measured tail scan

17 November 2026 · isolated candidate; original active source and live services unchanged.

## Change

`candidate.flow` preserves the DHCP implementation and scans post-END padding in a dedicated checked loop instead of sending every padding byte through the option dispatcher. It retains rejection of any nonzero trailing byte. No raw pointer escape, networking, compiler modification, cache or lease-policy change. `baseline.flow` is the exact original source; hashes and original source snapshots are retained.

## Native results

Mac ARM64, exact0.50 compilerSHA2564e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c. Each cell is the median of15 paired process runs; each process performs150,000 parses. Packet transaction IDs and baseline/candidate order are seeded-randomized. Both receive identical bytes and must match the independent Python byte-slice oracle checksum. Timing includes startup/read/output but excludes compilation/signing.

| Mode | Payload | Baseline ms | Candidate ms | Baseline/candidate |
|---|---|---:|---:|---:|
| plain | short-valid | 15.659 | 15.614 | 1.003× |
| plain | normal-300 | 40.836 | 37.309 | 1.095× |
| plain | max-576 | 176.329 | 150.378 | 1.173× |
| plain | bad-last-byte | 163.061 | 142.217 | 1.147× |
| plain | early-reject | 2.465 | 2.406 | 1.024× |
| opt | short-valid | 7.540 | 7.609 | 0.991× |
| opt | normal-300 | 14.482 | 12.088 | 1.198× |
| opt | max-576 | 45.418 | 33.600 | 1.352× |
| opt | bad-last-byte | 47.813 | 33.404 | 1.431× |
| opt | early-reject | 2.339 | 2.228 | 1.050× |

The optimized300-byte case improves about16.5% elapsed time; maximum padding about26.0%; malformed final byte about30.1%. The optimized minimum244-byte packet regresses about0.9%. This is parser throughput in repeated native process fixtures, not end-to-end DHCP/network throughput. CPU is shared with other local sprint work; this is not hardware-wide qualification, a universal speed claim, lower AI inference cost or a guest deployment.

## Acceptance and controls

- Unchanged independent dictionary/state oracle:2,078 payload/state cases and312 stream controls for each variant in each compiler mode. Exact reply bytes and full176-byte lease/clock snapshots compared.
- Additional55,611 cases per variant/mode: every admitted length244..576, and each possible single nonzero post-END byte position. All pass.
- Deliberately incorrect native candidate that skips nonzero padding validation returns OFFER where oracle requires malformed; detected in both modes.
- First eight-byte checked-array unroll improved plain builds but regressed optimized maximum padding44.29→52.16ms; it was rejected. Source, raw timings and controls remain under `candidate-unroll-rejected.flow`, `UNROLL-RESULTS.json`, `UNROLL-PADDING-CONTROLS.json`.
- Original source hashes were rechecked after execution; no active worktree files changed.

## Evidence / reproduction

`artifacts/evolution-20261117/net/tail-scan/RESULTS.json` contains all150 paired timings, packet hashes, order, platform and compiler identity. The baseline/candidate acceptance subfolders contain native executables, captured outputs and oracle receipts. `PADDING-CONTROLS.json` and `mutation/RESULTS.json` retain boundary and mutation evidence.

`run-tail.py` generated the final baseline/candidate acceptance campaign and timings; `padding-tail.py` generated exhaustive padding checks; `mutation_control.py` generated negative-control evidence. For reproduction: `python3 experiments/evolution-20261117/net/run-tail.py artifacts/evolution-20261117/net/reproduction`, then `python3 experiments/evolution-20261117/net/padding-tail.py artifacts/evolution-20261117/net/reproduction`. Use a fresh output path; existing acceptance directories are intentionally not overwritten. `run.py` is the first historical campaign harness; it explicitly reads the preserved rejected source to reproduce those historical cases.

## Next gate

Review the small `baseline.flow`→`candidate.flow` diff with the RF2Net owner, then integrate into that branch only after its other concurrent changes are reconciled. Run its actual adapter workload before claiming an end-to-end win. Current VM102 image, live network, stable release and active DHCP source remain untouched.
