# R5 serializer refinement

Isolated source candidate for large disjoint JSON values. Default SDK and stable packages are unchanged. The <=256-byte scalar body and alias fallback remain R3's source; emitted function maps confirm unchanged small-writer token identities. A direct checked leaf emitter replaces repeated string sizing/copy calls for dense values and span escapes. See DESIGN.md for bounds and partial-write semantics.

Correctness evidence lives under `artifacts/refinement-20261117/serializer`:

- `correctness/RESULTS.json`: all 8,040 original oracle/refusal controls pass.
- `integration/INTEGRATION.json`: original 73,728 alias states per mode, overlapping 172,032 boundary states per mode, and unchanged Passage Desk 80 controls per mode pass.
- `extra-r2/RESULTS.json`: 6,384 additional dense/C0 oracle invocations pass; two native runs each compare 16 unsigned used/capacity/sticky-error states against the unchanged scalar writer.
- `maps/RESULTS.json`: direct emitter has no function calls or A64 BL instructions in either mode. R3 and R5 small-writer source-token hashes match.

`extra/` preserves an unsuccessful harness run: it passed an initial value outside the unchanged task parser's limit. The corrected harness caps that ordinary argument at16; a separate native fixture covers full unsigned values. No candidate code changed in response. A concurrent cache-run preparation request was safely refused; `benchmark.prepare-held.*` preserves the guard receipt and no native comparison occurred there.

`benchmark.py` is the previously qualified monotonic paired controller, adapted only for source/package paths. All variants use the same timer and iteration count. `benchmark/FROZEN.json` and `PROMOTION-PROTOCOL.json` are bound before comparison. The campaign contains 26 nonduplicate profiles, baseline-only calibration, 31 shuffled paired trials, exact output/consumption checks and all-case confidence intervals. It may run only once after the coordinator grants an exclusive slot. Reproduce preparation first without `--measure`; no native cache binary is the sole source/evidence copy.

The once-only frozen campaign is complete: 26/26 rows, 31 shuffled paired triplets per row and 2,418 comparative native invocations. Every recorded exit/output hash, per-trial checksum and independently recomputed paired median agrees. No failed sample was retried, trimmed or recalibrated after comparison.

All six escape-heavy targets (1KiB, 16KiB and 256KiB, plain/optimized) beat both the unchanged scalar writer and accepted opt-in R3 with upper95 ratios below1. Their scalar-relative speedups are1.55–2.00×. This resolves the targeted large escape-heavy slowdown in the tested native loops, rather than merely rearranging call frames.

**R5 is not eligible for promotion under the preregistered protocol.** Seven of eight small gates pass. The32-byte escaped/plain row has ratio0.99410 and95%CI0.99096–0.99702, but one measured native interval is42.602ms, below the fixed50ms minimum. That is an under-duration measurement refusal, not a measured slowdown; it nevertheless prevents promotion. The exact same protocol is retained, and the campaign is not repeated to obtain a pass. Default SDK and stable packages remain unchanged.

`analyze.py --benchmark PATH --out NEW_DIRECTORY` audits the saved evidence without running native samples. It checks all eight small gates and all six dense gates against both scalar and R3, verifies raw invocation counts/output hashes/checksums and independently recomputes every paired point. `EVIDENCE.json` publishes those aggregates; complete raw trials, confidence intervals and build receipts remain under the ignored artifact root. Startup-inclusive process ratios are secondary and do not substitute for failed native-duration gates. Unrelated Mac background load was not controlled; no universal throughput or dedicated-host claim follows. No Memory, KHC, network or GitHub access is required by these controls.
