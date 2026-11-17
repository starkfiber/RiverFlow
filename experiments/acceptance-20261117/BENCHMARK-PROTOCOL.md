# Paired component performance acceptance, frozen before new timing

Use the same compiler, options, useful work/input and native ABI for each pair.
Pin source/compiler/image hashes; retain every variant and failed control. New
performance work runs after the correctness suites stop, one timed job at a time.
Host metadata/load observations are recorded; local isolation is not a dedicated
hardware or electrical measurement. Do not claim whole firewall throughput.

Minimum31 seeded-random AB/BA pairs per profile; warm-ups retained separately.
Amortize startup with at least approximately50ms repeated useful work per process
where feasible. Report complete-process wall time and native measured region
separately, never subtract startup estimates to invent a kernel number. Verify
outputs/checksums and refusal state on every execution. Include empty/tiny/dense,
normal/large and malformed/early-reject distributions, not only successful large
inputs. Preserve known small-case losses and the exact previous source baseline.

Bootstrap95% paired confidence intervals with fixed seed, from matched log time
ratios (candidate/baseline); keep raw trial order and samples. This is an engineering
uncertainty summary over one host, not an independent population/general speed
proof. No post-hoc removal of slow trials. Record interruptions or clock anomalies;
do not silently retry/select the best. A native gettimeofday interval is wall time;
cross-check with the controller's monotonic envelope and refuse negative or
impossible/jumped intervals. It is not a verified constant-time clock experiment.

Small-case promotion gate: median paired candidate/baseline≤1.03 and upper95%
bound≤1.05. Gains need exact correctness and the retained large-case advantage.
A result outside that gate requires fixing/keeping the old route or explicitly
declaring it inconclusive; it cannot be advertised as zero overhead. These fixed
noise/engineering bounds do not convert a tiny nonzero slowdown into a speedup.
No unconditional benchmark reliability is promised from a finite local campaign.

AI productivity is separate: count all provider tokens/time/retries until the
independent complete-task oracle passes, including unsuccessful generation. The
frozen AI protocol specifies task order, model, call cap and source admission.
