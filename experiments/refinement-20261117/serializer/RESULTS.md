# R5 once-only campaign

Promotion eligible: **False**. Small gates: 7/8; dense targets against both scalar and R3: 6/6.

| Bytes | Density | Mode | Speedup vs scalar | Speedup vs R3 | Candidate/scalar 95% CI | Minimum native ms, all three | Gate refusal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | plain | plain | 0.996× | 1.002× | 0.99820–1.00804 | 93.987 | — |
| 0 | plain | opt | 1.000× | 1.000× | 0.94533–1.01919 | 96.658 | — |
| 32 | plain | plain | 1.015× | 1.007× | 0.97360–0.99682 | 109.600 | — |
| 32 | plain | opt | 0.995× | 0.999× | 0.99150–1.02127 | 105.879 | — |
| 32 | mixed | plain | 1.011× | 1.000× | 0.98169–0.99573 | 98.656 | — |
| 32 | mixed | opt | 0.999× | 1.002× | 0.98270–1.01275 | 97.881 | — |
| 32 | escaped | plain | 1.006× | 0.999× | 0.99096–0.99702 | 42.472 | small minimum native duration below 50ms |
| 32 | escaped | opt | 1.001× | 0.993× | 0.98939–1.01322 | 96.686 | — |
| 1024 | plain | plain | 1.403× | 0.994× | 0.68023–0.73038 | 72.472 | — |
| 1024 | plain | opt | 1.508× | 0.999× | 0.65889–0.67153 | 59.927 | — |
| 1024 | mixed | plain | 1.378× | 1.080× | 0.72047–0.72936 | 67.634 | — |
| 1024 | mixed | opt | 1.464× | 1.041× | 0.67449–0.70080 | 64.859 | — |
| 1024 | escaped | plain | 1.963× | 1.957× | 0.50725–0.51132 | 50.555 | — |
| 1024 | escaped | opt | 1.620× | 1.651× | 0.61308–0.62495 | 63.584 | — |
| 16384 | plain | plain | 1.450× | 1.002× | 0.68023–0.69778 | 71.311 | — |
| 16384 | plain | opt | 1.563× | 1.001× | 0.62893–0.64753 | 65.588 | — |
| 16384 | mixed | plain | 1.429× | 1.092× | 0.69266–0.70719 | 72.027 | — |
| 16384 | mixed | opt | 1.473× | 1.052× | 0.66270–0.68928 | 68.502 | — |
| 16384 | escaped | plain | 2.004× | 1.983× | 0.49549–0.50064 | 51.571 | — |
| 16384 | escaped | opt | 1.583× | 1.581× | 0.62026–0.64664 | 67.334 | — |
| 262144 | plain | plain | 1.461× | 1.004× | 0.66994–0.70078 | 65.101 | — |
| 262144 | plain | opt | 1.595× | 1.007× | 0.61204–0.63773 | 63.202 | — |
| 262144 | mixed | plain | 1.426× | 1.097× | 0.67921–0.70762 | 68.378 | — |
| 262144 | mixed | opt | 1.504× | 1.050× | 0.65606–0.67721 | 71.189 | — |
| 262144 | escaped | plain | 1.979× | 2.009× | 0.49095–0.52321 | 50.622 | — |
| 262144 | escaped | opt | 1.550× | 1.532× | 0.63906–0.66588 | 70.051 | — |

Isolated Darwin ARM64 source candidate. All rows retained; no retries or recalibration after comparison. Unrelated Mac load not controlled. Default SDK and stable release unchanged.

A duration gate refusal is not a measured slowdown. It still prevents promotion under the frozen protocol. Smaller native times are not replaced with startup-inclusive process timing. No stable/default replacement follows from these results.
