# RF2Net native-region measurement refinement

The existing padding-scan parser optimization is unchanged. This experiment improves the measurement so short cases are no longer judged only through process startup and packet framing. It does not change a shipped parser, default build, stable package, network configuration or live service.

## Result

The once-only frozen campaign completed all20 family/mode/profile rows:620paired comparisons,1,240 measured processes and80 separate warmup processes. Every output checksum, warmup consumption, repetition count and checked clock conversion passed. No samples were trimmed, retried or silently recalibrated.

The predeclared small-case gate requires a paired candidate/baseline median ratio no greater than1.03, upper95%bootstrap bound no greater than1.05, and every measured native interval at least50ms.

| Family | Mode | Small profile | C/B median | 95% interval | Gate |
| --- | --- | --- | ---: | --- | --- |
| Original | Plain | Short valid | 0.98634 | 0.97999–0.99474 | Pass |
| Original | Plain | Early reject | 0.99716 | 0.99552–0.99935 | Pass |
| Original | Optimized | Short valid | 0.99370 | 0.99019–0.99556 | Pass |
| Original | Optimized | Early reject | 0.99936 | 0.99842–1.00076 | Pass |
| Durable | Plain | Short valid | 0.99700 | 0.97188–1.01373 | Pass |
| Durable | Plain | Early reject | 1.01089 | 0.96952–1.11782 | Inconclusive |
| Durable | Optimized | Short valid | 1.00594 | 0.98487–1.02112 | Pass |
| Durable | Optimized | Early reject | 1.00100 | 0.97926–1.01586 | Pass |

Thus **all4 optimized small profiles pass;7of8 all-mode small profiles pass**. This supports the narrow optimized native-region comparison, not an all-mode promotion. The durable/plain early-reject interval remains too wide; its point estimate alone cannot qualify it. Do not rerun the same campaign to obtain a preferred answer.

Larger optimized padded/rejected-last-byte rows have paired ratios0.70197–0.73718 (approximately1.36–1.42× throughput on those fixed workloads). All20 rows, confidence intervals and launch-inclusive secondary measurements are retained in EVIDENCE.json. Original/optimized normal-300 measured0.80279 but included a47.850ms sample below the fixed50ms floor; that row is explicitly nonqualifying, despite its apparent gain. Do not combine these individual numbers into a global speed claim.

## What changed in the measurement

- `probe.flow` calls the identical checked Darwin monotonic helper around the parse/consume loop only. Input framing,32 initial warmup parses, process startup and output remain outside that region. Full-process elapsed remains a separate secondary series.
- Fixed counts, identical across baseline/candidate: short1.5million, normal750thousand, padded/max and bad-last-byte250thousand, early reject30million. Each row has2 separate warmup pairs and31 shuffled measured pairs.
- Primary estimator is **median of within-pair ratios**, with a10,000-resample whole-pair bootstrap. The historical campaign used a ratio of medians; `diagnose.py` preserves a separate exploratory recomputation rather than rewriting the old result or asserting startup was the cause.
- Native wall time still includes scheduling and background contention. This shared Mac is not a dedicated host. This test does not measure CPU cycles, energy, NIC latency or packet service throughput.

## Source and correctness

`PLAN.json` and prepared manifest were frozen before timing. Eight probes cover original/durable × baseline/candidate × plain/optimized, plus two clock-control binaries. The qualified0.50 compiler hash and parser/probe hashes are pinned in EVIDENCE.json. The candidate uses the prior reviewed opt-in padding transform; no new parser edit was made here.

Both clock modes passed11 arithmetic edge controls and one live monotonic control. Additional correctness passed80 valid whole/fragmented parser-clock cases and48 framing refusals. `logic_controls.py` passed12 invalid clock/output controls plus estimator controls that distinguish paired medians from ratios of medians. These are measurement checks, not another claim of complete network qualification.

Initial preparation failed because the clock-control fixture declared its IO result before an import (`imports must precede declarations`). That exact BUILD.json remains under `artifacts/refinement-20261117/net/prepared-1`. Prepared-2 moves that declaration into `io-result.flow` and imports it before `clock.flow`; parser hashes remain pinned. No comparative campaign ran from prepared-1.

## Evidence and reproduction

Persistent raw evidence is under `artifacts/refinement-20261117/net`: prepared-2, verify-2, logic-controls-1, historical-estimator-1, timing-1 and analysis-1. Unique sources, packet inputs and raw receipts remain in the project; only rebuildable native images were placed in the disposable cache.

`analyze.py` reads the once-only receipts, verifies frozen dependencies, every paired checksum/timebase, medians, gates, row count and1,320 sample lines. It launches no native process and performs no new comparative timing:

```sh
python3 experiments/refinement-20261117/net/analyze.py \
  --evidence artifacts/refinement-20261117/net \
  --out artifacts/refinement-20261117/net/NEW-ANALYSIS
```

The output directory must be new. Bootstrap bounds remain the frozen controller's recorded bounds; analysis does not select or recompute them. EVIDENCE.json includes source/receipt hashes and compact results so the qualified scope stays reviewable without committing ignored binary/raw artifacts. Running `controller.py measure` requires a separate explicit coordinator timing grant; none is granted by these instructions.

**Disposition:** optimized-only native small-case evidence improved; all-mode qualification remains incomplete. Default SDK/compiler, stable release and live network stay unchanged. No AI-token, embedded hardware, universal throughput or broad firewall-readiness claim follows.
