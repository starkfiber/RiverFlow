# RF2 0.48: remove repair work without hiding the Python gap

**Correction after independent review:** the owned-field `try` route admitted consumption of its own destination during the RHS. [Candidate 0.49](APPLICATION-EPOCHS-0.49.md) reproduces and corrects that ownership regression; use its corrected compiler for new field-propagation development. The historical0.48 evidence is retained, not treated as proof that this interaction was tested then.

The earlier app study measured minutes of authoring and repair, not minutes spent in the native compiler. This source candidate addresses the actual failures: repeated output-path refusal, indirect imported-source diagnostics, and temporary variables needed before assigning propagated scalar results to record fields.

The new RF2-native `rf2-dev` compiles, validates, signs and atomically publishes a replaceable program in an explicit private build directory. Compilation/signing failure preserves the previous exact signed image. Cooperating simultaneous builds refuse safely; an existing running process keeps its old image while a later launch sees the newly committed program. Existing outputs are not silently overwritten by the compiler itself.

Scalar `set record.field=try operation()` now handles its saved destination address before the ordinary error/cleanup return. Plain, nested and owned scalar-field cases are covered. Source-range mapping gives original import paths and byte-column locations. Actionable messages explain the current parameter, record-scope and root-return rules without pretending those restrictions were removed.

## Executed results

- **120 new native controls passed**, including failure preservation, actual concurrent build processes, active-image replacement, unsafe path/link refusal, malformed images, nominal errors, owned cleanup and source mapping across 29 modules with shared imports.
- **15 existing native suites passed**, including Booking CLI/browser/agent controls and the original nine Core MCP tools. Compiler self-generation reproduced its signed bytes exactly.
- The previous real Study Rooms app passed **55/55** after five temporary-variable pairs were mechanically replaced by direct field assignments. Source size changed from 11,200 to 11,029 bytes. This parent edit is not a fresh model-generated app, a token-usage experiment or a learner trial.

The first driver incorrectly relied on signing alone: macOS could sign ordinary data. A native failure fixture exposed that error. The corrected driver checks a bounded ARM64 Mach-O executable header before signing and again before publication. Separate invalid-data and malformed-image/signing controls now preserve the previous image. This remains a trusted local build tool, not a malicious-compiler sandbox.

The initial replay omitted the original README, so54/55 passed despite all behavioral checks passing. The omission and original score were retained; copying the original instructions and rerunning produced55/55. No grader expectation was weakened. Early driver drafts also exposed a duplicate local name and unsupported `%` spelling; both failures are recorded locally rather than described as successful builds.

## Native compile comparison

One warm Mac ARM64; two warmups then 15 rotated measured trials per arm. These are whole-process compile medians in milliseconds, with identical input sources and `--compact --opt`. Code signing, app execution, model authoring and provider usage are excluded.

| Workload | 0.47B | Initial byte-map candidate | Range-map candidate |
| --- | ---: | ---: | ---: |
| Small native program | 1.946 | 1.825 | 1.893 |
| Real Study Rooms app with SDK imports | 14.855 | 15.126 | 14.791 |
| Compiler source | 33.412 | 33.359 | 33.312 |

All unchanged-source outputs were byte-identical across all three arms. The initial byte map added a small median cost on the imported app; the coalesced range map avoided that observed cost in this run. Differences against 0.47 are small relative to observed variation, so **no meaningful general compile-speed improvement is established**. An earlier run, retained in the receipt, likewise gave Study Rooms medians 15.198/15.550/15.188ms. The controller was then made portable by reading the public source archive rather than a private trial directory; compilation inputs stayed identical and all second-run results are retained too.

A roughly 15ms native compile does not explain a 455.7-second authoring task. This comparison points toward API discovery, unfamiliar rules, application plumbing and repair iterations as the next priorities; it is not a precise attribution of every second in the earlier model trial. Making this compiler 100 times faster would not, on its own, remove the observed authoring gap.

## What remains

There were **no new model construction calls or provider-usage measurements** in this sprint. The earlier Python lead remains unchanged. Fewer temporary assignments, clearer diagnostics and one repeatable command are implemented improvements, not yet evidence of lower complete-task time or token usage.

Next: typed request/form adapters that remove manual slots, a stable reusable app SDK, then a preregistered second complete application comparison with every failure and actual usage retained. Do not repeat trials until a win appears. Continue treating runtime speed, compiler speed and human/AI development effort separately.

This is a Mac ARM64 source candidate. Public 0.46/stable 0.17 downloads and the nine-tool MCP boundary are unchanged. Broader targets, SDK readiness and Linguist remain separate; Linguist is pending and nonblocking. Native source and tests are in [the developer kit](../experiments/developer-loop/README.md); [the JSON receipt](DEVELOPER-LOOP-0.48.json) contains source hashes, all new controls, regression outcomes, original failures and both timing rounds.
