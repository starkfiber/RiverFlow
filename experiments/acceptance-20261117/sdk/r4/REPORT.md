# R4 direct fallback: correct corpus, rejected promotion

R4 is **unpromoted**. The single frozen campaign completed all 26 profiles with 31 shuffled paired trials each (806 trials, 2,418 comparative processes), preserving every measurement. All output, consumption and monotonic-envelope checks passed. The six preparation/measurement binary identities match. Runtime: 484.058 seconds, exit 0. Small confidence gates and the affected optimized 16 KiB escape-heavy improvement gate failed. No comparative campaign was repeated. R3 remains the separately qualified small-input candidate; its known optimized 16 KiB dense loss remains explicit.

R4 passes the same 8,040 original oracle controls, original 73,728 alias states per mode, overlapping 172,032 boundary alias states per mode and unchanged Passage Desk 80 checks per mode. The emitted eligibility predicate has zero calls/BL instructions. Removing the intermediate scalar dispatch did not establish a performance repair; code layout and transient platform behavior remain possible contributors, without causal proof.

The benchmark itself improves reliability: all variants use identical Mach monotonic ticks, checked timebase scaling after subtraction, controller monotonic envelope validation, frozen baseline-only calibration toward 100 ms, and nonduplicate input profiles. Eleven arithmetic/error controls plus live clock checks pass both modes. This does not prove universal timing stability or CPU-cycle performance. R3's historical gettimeofday campaign remains separately labelled.

Ratios below are candidate/baseline and candidate/R3; lower is faster. Brackets are paired bootstrap 95% intervals. A failed confidence gate can be inconclusive rather than proof of a persistent regression. No all-cases-faster claim is justified.

| Bytes | Shape | Mode | R4 / scalar [95%] | R4 / R3 [95%] | Required gate |
| --- | --- | --- | --- | --- | --- |
| 0 | plain | plain | 0.986247 [0.948327, 1.010832] | 0.995762 [0.973020, 1.016900] | True |
| 0 | plain | opt | 0.987253 [0.952652, 0.999219] | 1.002889 [0.992714, 1.027090] | True |
| 32 | plain | plain | 0.996054 [0.976227, 1.019595] | 1.007975 [0.972122, 1.037490] | True |
| 32 | plain | opt | 1.004046 [0.965874, 1.054262] | 0.986492 [0.952694, 1.042102] | False |
| 32 | mixed | plain | 0.996352 [0.961788, 1.035987] | 1.007786 [0.927908, 1.036218] | True |
| 32 | mixed | opt | 1.019279 [0.984220, 1.066675] | 1.025960 [0.938643, 1.064085] | False |
| 32 | escaped | plain | 1.031655 [0.941636, 1.078341] | 1.006770 [0.943731, 1.055552] | False |
| 32 | escaped | opt | 1.077436 [1.019327, 1.142553] | 1.040987 [0.969223, 1.113508] | False |
| 1024 | plain | plain | 0.702017 [0.695466, 0.718091] | 0.995177 [0.989799, 1.003549] | — |
| 1024 | plain | opt | 0.639128 [0.616193, 0.646583] | 0.990857 [0.956513, 1.027888] | — |
| 1024 | mixed | plain | 0.750393 [0.641775, 0.802170] | 0.971798 [0.924393, 1.101176] | — |
| 1024 | mixed | opt | 0.661653 [0.614701, 0.725571] | 0.998978 [0.883424, 1.045832] | — |
| 1024 | escaped | plain | 1.049440 [1.017807, 1.096608] | 1.038959 [0.986069, 1.087397] | — |
| 1024 | escaped | opt | 1.034888 [0.999420, 1.067294] | 0.992698 [0.982995, 1.046691] | — |
| 16384 | plain | plain | 0.617134 [0.585012, 0.647675] | 0.987961 [0.971705, 1.044059] | — |
| 16384 | plain | opt | 0.558706 [0.536009, 0.602985] | 0.993445 [0.974901, 1.034447] | — |
| 16384 | mixed | plain | 0.699030 [0.670912, 0.739403] | 1.000722 [0.980968, 1.029582] | — |
| 16384 | mixed | opt | 0.673176 [0.537481, 0.712060] | 0.981569 [0.887429, 1.034135] | — |
| 16384 | escaped | plain | 0.962938 [0.902449, 1.009508] | 0.988593 [0.906499, 1.042055] | — |
| 16384 | escaped | opt | 1.015246 [0.921081, 1.104485] | 1.044311 [0.992980, 1.119806] | False |
| 262144 | plain | plain | 0.610947 [0.562598, 0.649158] | 0.977981 [0.936761, 1.004821] | — |
| 262144 | plain | opt | 0.609600 [0.603481, 0.625815] | 1.002537 [0.935851, 1.011612] | — |
| 262144 | mixed | plain | 0.751324 [0.720979, 0.778367] | 1.026727 [0.983693, 1.091935] | — |
| 262144 | mixed | opt | 0.697306 [0.681855, 0.714617] | 0.975097 [0.943870, 1.015755] | — |
| 262144 | escaped | plain | 0.997084 [0.962864, 1.076898] | 0.991275 [0.937813, 1.067229] | — |
| 262144 | escaped | opt | 0.959318 [0.918431, 1.075722] | 0.950376 [0.880811, 0.998587] | — |

Preparation failures are retained: an initial map reader expected a nonexistent __text section in compact Mach-O, then a probe used an invalid constructor. Both were corrected before the frozen comparative campaign; see r4-clock-maps/INCOMPLETE.json and r4-clock-maps-r2/COMMANDS.json. No product source was changed to hide failures.

Default SDK, stable packages and unrelated worktrees remain untouched by this candidate. No Memory, KHC, network or GitHub operation was used.
