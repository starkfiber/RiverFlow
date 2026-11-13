# Compiler policy cleanup and dispatch experiment

## What changed

One `intrinsic_flags` catalogue now describes 24 compiler-recognized operations. Declaration checks, leaf classification and raw argument lowering use the same policy instead of four repeated name lists. The three independent bits mean reserved arithmetic name, inline leaf operation and raw argument ABI. They do not grant ownership, memory safety or additional MCP permission.

A token's existing length filters out impossible names before exact comparisons. Unknown names return zero, preserving the ordinary function path. Dedicated platform, ownership and live-view checks remain unchanged. Generated code from the old and new generators is byte-identical for each matched task and compiler mode in the experiment.

## Hypotheses and outcomes

| Hypothesis | Test | Outcome |
| --- | --- | --- |
| Shared policy can preserve accepted programs and refusals | Independent 156-token oracle, exact names, prefixes, suffixes, case changes, reserved declarations and real lookalike calls | 624 classification comparisons, 28 refusals and eight generated executions passed across both modes |
| Per-token caching improves complete compilation | Matched cached versus uncached native compilers, 21 rotated trials for three source tasks in both modes | All paired uncertainty intervals crossed zero; the cache was removed, avoiding its extra 512 KiB table |
| Length-filtered policy improves every compile workload | Prior source versus final candidate, same native builder settings and identical inputs | Only one of six final task/mode paired intervals excluded zero; no general speed claim |

The first exploratory timing run mixed compiler build settings and is invalid as a performance control. It is retained locally. Subsequent matched controls built both compiler executables through the same prior generator with `--opt`. An exploratory run also overlapped correctness checks; the final report was rerun without concurrent RF2 test controllers. Other host activity remains uncontrolled.

## Final process-inclusive results

Twenty-one rotated trials per task and mode on one Apple Silicon Mac, after a warmup compilation. Medians in milliseconds include process startup, compilation and writing the unsigned output. Signing and executing the generated program are excluded from the measured interval. Every produced image was compared with the baseline bytes outside the timer.

| Identical source task | Output mode | Prior compiler | Candidate | Paired candidate-minus-prior 95% interval, ms |
| --- | --- | ---: | ---: | --- |
| Compiler source | Default | 31.767 | 30.697 | -0.970 to 0.079 |
| Compiler source | Optimized | 29.694 | 25.748 | -4.077 to -1.047 |
| Composed runtime | Default | 27.367 | 26.508 | -1.151 to 0.020 |
| Composed runtime | Optimized | 28.246 | 28.591 | -1.187 to 0.847 |
| File checksum source | Default | 3.646 | 3.542 | -0.124 to 0.017 |
| File checksum source | Optimized | 3.346 | 3.326 | -0.139 to 0.027 |

Marginal medians and the median of paired differences are different statistics. Do not derive a universal speed ratio from the table. Six exploratory comparisons and one host do not establish broad compiler superiority. The generated applications are unchanged, so this does not demonstrate faster application execution, lower model-token bills or energy savings.

[Raw final trials](COMPILER-DISPATCH-MEASUREMENTS.json) · [cache control](COMPILER-DISPATCH-CACHE-CONTROL.json) · [verification](COMPILER-DISPATCH-VERIFICATION.json).

## Verification

Compiler self-generation reached a fixed point and matched the independent historical seed encoder. The resulting runtime passed its corpus and official MCP SDK checks, with its unsigned image hash unchanged. Additional tests passed 5,120 ABI comparisons; 4,288 memory and 648 literal-size comparisons with 12 refusals; and 900 SHA cases, 192 arbitrary compression cases and six refusals. These are finite tests, not a proof of all programs or complete memory safety.

## Reproduce

Use an existing qualified native compiler, here shown as `$RF2_BUILDER`. These commands build into new paths; choose unused names. The previous source is retained in Git at `cfa8980`.

```sh
git show cfa8980:native/compiler/compiler.rf2 > /tmp/rf2-prior-source.rf2
"$RF2_BUILDER" /tmp/rf2-prior-source.rf2 /tmp/rf2-prior --opt
"$RF2_BUILDER" native/compiler/compiler.rf2 /tmp/rf2-candidate --opt
/usr/bin/codesign -s - /tmp/rf2-prior
/usr/bin/codesign -s - /tmp/rf2-candidate
RF2_BASELINE_COMPILER=/tmp/rf2-prior RF2_TEST_COMPILER=/tmp/rf2-candidate python3 tools/benchmark-compiler-dispatch.py
RF2_TEST_COMPILER=/tmp/rf2-candidate python3 tests/standalone/compiler_dispatch_verify.py
```

Python controls the development experiment; generated native programs do not require it. Raw inputs, outputs and failed approaches remain in the local `artifacts/codebase-refresh` directory. Public source and controller identities are recorded in the receipts.

## Originality boundary and next investigations

String dispatch and identifier interning are established compiler techniques. LLVM provides [StringSwitch](https://llvm.org/doxygen/StringSwitch_8h_source.html); Rust documents [symbol interning](https://doc.rust-lang.org/stable/nightly-rustc/rustc_span/symbol/index.html). This implementation was written in RF2; it does not establish a previously unknown computing principle. These references are a narrow prior-art check, not an exhaustive novelty search or a performance comparison against LLVM or Rust.

The next useful hypotheses are: deterministic reuse of semantic facts with explicit invalidation; optimizer decisions accompanied by independently checked equivalence witnesses; and target-specific cost selection using held-out workloads. Each needs a normal fallback, a counterexample that defeats an unsound candidate, and an end-to-end measurement before adoption. They are queued investigations, not implemented features or claims of historical uniqueness.
