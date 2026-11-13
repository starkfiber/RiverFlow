# Developer examples and retained controls

Keep acceptance probes and benchmark controls as executable references. Start with a complete example and its expected result, then inspect its failure cases. Test fixtures are programming inputs, not field data.

| Goal | Example | Verification or control |
| --- | --- | --- |
| Checked arithmetic in the bounded Core profile | examples/sum.flow, examples/compact/sum.rf2 | tests/standalone/core_verify.py and native MCP SDK |
| Typed bytes and file ownership | examples/hex, examples/buffer-audit | Matching ownership/vector controllers in tests/standalone |
| Real file hashing | examples/file-checksum.rf2 | SHA and incremental clean-build checks |
| Follow a function edit | examples/function-changes | compact_image_verify.py and function-impact.py |
| Compare rebuild paths | native/build/incremental.rf2 | incremental_verify.py and benchmark-compact-builds.py |
| Inspect target limitations | docs/CAPABILITY-MAP.md | Versioned receipts and explicit missing acceptance gates |

File extension is not an authority boundary or a performance guarantee. Existing .flow examples contain the bounded Core language; .rf2 files can contain compact Core or trusted systems source according to their declared profile. The native compiler accepts its systems profile. Native MCP accepts its checked profiles and defined application schemas. Renaming a file does not grant systems effects or turn bounded execution into a standalone compiled image.

Use the native compiler's --compact flag for the optional Mach-O file layout. It is distinct from compact source syntax and the MCP option that removes redundant reply text. Function maps are developer evidence, not an object cache. Every performance report needs the exact task, options, compiler, target and observed result.

The current target tests do not establish complete Python or Clang compatibility. Runtime performance needs matched algorithms and equivalent semantics; rebuild speed is a separate measurement. Reduced file bytes and observed CPU time can guide efficiency work, but neither measures electricity or proves lower energy consumption. Hardware power measurements, multiple hosts and a declared energy protocol remain future work.

For 0.28, follow [restricted function reuse](FUNCTION-REUSE-0.28.md) with the existing function-changes example. Its report records actual reused bodies; unsupported functions still compile normally. [Compiler stores](COMPILER-STORE-0.28.md) address repeat compiler startup across new project caches. Correctness and throughput are separate gates: opt-in function reuse currently adds measured overhead.

The [0.29 guide](FUNCTION-REUSE-0.29.md) adds memoized linear-scalar units, a [NumberLab CLI](../examples/number-lab/), [browser playground](../examples/number-lab-web/) and [SHA40](../examples/sha40/) workload. Keep their boundaries and complete-cost measurements visible; these are useful developer references, not ecosystem equivalence claims.
