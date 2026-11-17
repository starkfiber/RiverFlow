# SDK small-field acceptance and full benchmark

17 November2026. Candidate only; no default SDK, prior experiment or stable artifact changed.

## Change and correctness

The direct original scalar body handles0..256bytes with one size branch. Larger values retain alias/density/span dispatch. The256threshold was chosen before timing because a32byte input can produce192bytes of escapedHTML. No threshold was tuned from timing results.

8040original correctness controls pass. Original73728alias states per mode pass, plus a separate172032-state boundary corpus (overlapping old cases). Unchanged Passage Desk80checks per mode pass. Sources and unique evidence remain persistent; rebuildable binaries use the guarded cache.

## First frozen timing campaign

benchmark-r3 completed once in699.116seconds.31randomized paired trials per shape/mode;16untimed warmup iterations per process. Every trial has exact output/checksum checks. All six binary hashes match preparation. No retries, rejected samples, clock errors, or output failures.

Internal elapsed time is gettimeofday wall time in microseconds, checked against a controller monotonic envelope. It excludes startup/read/initialHTML conversion/warmup/output. The enclosing process clock is separately retained. These native-loop ratios are NOT directly comparable to the previous startup-inclusive1.27–1.42× results as a claim of additional code acceleration.

All12declared small-case gates pass: paired median candidate/baseline≤1.03, paired-bootstrap95%upper≤1.05, minimum useful native duration≥50ms. The largest small paired point ratio is1.006775 and largest upper95is1.026271. Three empty shape labels repeat the same input, not three unique workloads.

| Bytes | Shape | Mode | Baseline native µs | Candidate native µs | Paired ratio C/B [95%CI] | Native speedup | Enclosing process speedup* |
|---:|---|---|---:|---:|---|---:|---:|
| 0 | plain | plain | 383,510 | 384,832 | 1.002912 [0.997024,1.007450] | 0.9971× | 0.9979× |
| 0 | plain | opt | 164,518 | 163,572 | 0.997615 [0.992525,1.003113] | 1.0024× | 1.0039× |
| 0 | mixed | plain | 388,237 | 384,909 | 0.998048 [0.987548,1.004602] | 1.0020× | 1.0022× |
| 0 | mixed | opt | 174,739 | 176,053 | 0.990593 [0.977890,0.998400] | 1.0095× | 1.0054× |
| 0 | escaped | plain | 385,611 | 384,921 | 1.000104 [0.997253,1.007450] | 0.9999× | 0.9995× |
| 0 | escaped | opt | 177,392 | 175,691 | 0.996443 [0.988667,1.004956] | 1.0036× | 1.0052× |
| 32 | plain | plain | 311,332 | 311,838 | 0.999894 [0.991460,1.012476] | 1.0001× | 1.0010× |
| 32 | plain | opt | 128,784 | 129,187 | 0.999247 [0.990307,1.010215] | 1.0008× | 0.9994× |
| 32 | mixed | plain | 384,104 | 388,403 | 1.006775 [0.997056,1.023727] | 0.9933× | 0.9935× |
| 32 | mixed | opt | 161,367 | 161,189 | 1.002780 [0.991018,1.010322] | 0.9972× | 0.9969× |
| 32 | escaped | plain | 531,826 | 542,423 | 1.003036 [0.991939,1.026271] | 0.9970× | 0.9968× |
| 32 | escaped | opt | 236,427 | 235,276 | 0.988588 [0.974031,0.997250] | 1.0115× | 1.0095× |
| 1024 | plain | plain | 217,773 | 154,164 | 0.715733 [0.691505,0.718764] | 1.3972× | 1.4053× |
| 1024 | plain | opt | 191,321 | 117,035 | 0.564646 [0.543346,0.642658] | 1.7710× | 1.6328× |
| 1024 | mixed | plain | 286,426 | 220,004 | 0.780110 [0.767079,0.793673] | 1.2819× | 1.2792× |
| 1024 | mixed | opt | 117,336 | 84,372 | 0.719063 [0.708775,0.728192] | 1.3907× | 1.3758× |
| 1024 | escaped | plain | 436,858 | 432,923 | 0.997675 [0.984145,1.009428] | 1.0023× | 1.0021× |
| 1024 | escaped | opt | 197,358 | 200,192 | 1.018673 [0.988913,1.041853] | 0.9817× | 0.9811× |
| 16384 | plain | plain | 214,755 | 154,154 | 0.685779 [0.666306,0.694587] | 1.4582× | 1.4506× |
| 16384 | plain | opt | 87,046 | 55,410 | 0.642501 [0.633214,0.653635] | 1.5564× | 1.5312× |
| 16384 | mixed | plain | 313,852 | 236,167 | 0.770753 [0.745911,0.778197] | 1.2974× | 1.2934× |
| 16384 | mixed | opt | 113,921 | 80,252 | 0.714466 [0.701768,0.721326] | 1.3996× | 1.3877× |
| 16384 | escaped | plain | 491,258 | 497,648 | 0.980470 [0.964943,1.015097] | 1.0199× | 1.0193× |
| 16384 | escaped | opt | 196,520 | 200,680 | 1.027823 [1.013207,1.063678] | 0.9729× | 0.9723× |
| 262144 | plain | plain | 232,437 | 157,261 | 0.685079 [0.675671,0.698996] | 1.4597× | 1.4317× |
| 262144 | plain | opt | 84,629 | 53,335 | 0.632140 [0.627702,0.639633] | 1.5819× | 1.5500× |
| 262144 | mixed | plain | 292,017 | 220,737 | 0.756920 [0.744452,0.772317] | 1.3211× | 1.3082× |
| 262144 | mixed | opt | 116,026 | 83,957 | 0.711485 [0.697064,0.718935] | 1.4055× | 1.3851× |
| 262144 | escaped | plain | 518,908 | 531,265 | 1.011459 [0.940015,1.042509] | 0.9887× | 1.0167× |
| 262144 | escaped | opt | 235,921 | 219,233 | 0.953379 [0.902834,0.992305] | 1.0489× | 1.0441× |

*Process speedup is the reciprocal of the median paired process ratio; no separate process CI is asserted here. All raw enclosing measurements remain in TRIALS.jsonl/RESULTS.json. Native point ratios are paired estimators; ratio of marginal medians can differ under shared background drift.

## Retained losses and tradeoffs

- Optimized16KiBescaped: ratio1.027823,95%CI1.013207–1.063678, about2.8%slower. This was not removed or rerun to a win.
- Optimized1KiBescaped: ratio1.018673,CI0.988913–1.041853; uncertain1.9%slowdown.
- Plain256KiBescaped: ratio1.011459,CI0.940015–1.042509; uncertain1.1%slowdown.
- No every-workload or regression-free claim: large dense fallback still has dispatch overhead/code-layout effects. Native small no-regression gates do not close that broader question.
- Same-run previous32Bescaped candidate ratios were1.2315plain/1.1236optimized; new ratios1.0030/0.9886. The earlier escaped regression does reproduce in the retained comparator and is removed by this direct path. Some previous small ordinary optimized wins become neutral.
- Performance at intermediate64–256byte lengths was not in the frozen original-size matrix; correctness covers those boundaries. Span use is intentionally traded for predictable scalar small-field behavior.

## Reproduction

`python3 stage_complete.py NEW_DIR` produces a complete source package containing this writer and unchanged Report API, edition0.50D-small-fields-candidate. Root independently verifies the combined package before promotion. No such verification is inferred merely from packaging.

Run substantial checks via bank.py after status, stable labelrf2-sdk-accept. Source/input/evidence paths must stay persistent; binary paths explicitly use TMPDIR. To prepare a new campaign use benchmark.py --compiler PINNED --out NEW_DIR; only after an exclusive timing grant use the same command with --measure. Used campaigns refuse rerun. SDKROOT/default source hashes remain pinned.

Current complete source package: artifacts/acceptance-20261117/sdk/complete-r3. Frozen benchmark sources and compiler are in benchmark-r3/FROZEN.json. A host-native component comparison is not whole-application speed, CPUcycle/energy evidence, universal hardware support or AI-token reduction.
