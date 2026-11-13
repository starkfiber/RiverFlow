# RF2 foundation sprint, development 0.31

This sprint connects compiler reliability to a reusable native application. It does not establish general Python/C compatibility, universal speed, usability, AI productivity or security certification.

## Delivered mechanisms

1. Native `rf2c --check SOURCE` validates through code generation/relocation without executing the program or publishing artifacts. Nearby line/byte-column diagnostics, with honest expanded-source labels for imports. Out-of-range integer literals refuse. Error token previews are bounded and sanitize terminal control bytes. See [diagnostic contract and 41 controls](DIAGNOSTICS-0.31.md).
2. A caller-owned typed KMP prefix workspace and bounded exact-byte search module, used by a native stdin/JSON CLI. Query maximum 128 bytes and input 1 MiB. Its word skip reads only complete in-range eight-byte windows; ordinary matching remains the fallback. See [build, use and library contract](../examples/text-search/README.md).
3. Independent verification against native execution, guarded memory and Python byte oracles, plus compiler reproduction and existing MCP/cache checks.
4. [Product proof gates](PRODUCT-PROOF-GATES.md) and a [proposed controlled AI-task protocol](AI-TASK-BENCHMARK-PROTOCOL.md). These are evaluation designs, not measured adoption or model-usage results.

## Actual complete-application comparison

31 rotated trials per route on one Mac, including process launch, stdin transfer, computation and JSON output. All results matched an independent byte-search oracle. C calls the system memmem library; Python calls bytes.find. These are useful application comparators with different implementations, not equal instruction sequences. Startup dominates short tasks.

| Task | RF2 plain KMP baseline | RF2 guarded skip | C libc | Python bytes |
| --- | ---: | ---: | ---: | ---: |
| Short text | 1.676ms | 1.693ms | 1.848ms | 17.498ms |
| 64KiB document | 2.087ms | 2.047ms | 2.187ms | 18.397ms |
| 1MiB no match | 8.795ms | 7.520ms | 7.986ms | 24.410ms |
| 64KiB overlapping matches | 2.286ms | 2.248ms | 2.570ms | 33.559ms |
| 1MiB repetitive pattern | 12.465ms | 12.409ms | 9.262ms | 25.093ms |

The no-match task took about 14.5% less time than RF2's plain KMP baseline. C remained faster on the long repetitive-pattern task. The short case showed a small opposite difference. These observations do not demonstrate general library throughput, inference speed, energy savings, portability or lower AI development costs.

[Raw trials, inputs and executable hashes](TEXT-SEARCH-0.31-MEASUREMENTS.json) · [Paired exploratory intervals](TEXT-SEARCH-0.31-ANALYSIS.json) · [Exact prior KMP source](../tests/comparators/text_search_kmp.rf2) · [Comparison controller](../tools/benchmark-text-search.py) · [C comparator](../tests/comparators/text_search.c)

The final promoted executable was verified byte-identical to the measured candidate. KMP and zero-byte detection are established techniques; this sprint supplies an RF2 implementation and scoped execution evidence, not a new algorithm or reconfigured transistor hardware.

## Tests and independent review

- [101 independent adversarial controls](FOUNDATION-0.31-REDTEAM-VERIFICATION.json), including 119 successful app queries, 90 guard-page cases plus 3 invalid-budget cases in each compiler mode, arithmetic/malformed-source checks and 8 check-only boundary controls. Nested cases are not independent security guarantees.
- [24 check-only controls](CHECK-ONLY-0.31-VERIFICATION.json), including unchanged-workspace manifests and actual nonexecution canary.
- [688 text-search controls](TEXT-SEARCH-0.31-VERIFICATION.json): ordinary/optimized native modes, independent byte oracle, overlaps, empty inputs, binary needles, UTF-8 bytes, budgets, descriptor failures and guard pages.
- [Compiler reproduction and runtime](FOUNDATION-0.31-COMPILER-VERIFICATION.json): maintained independent encoder, three native fixed-point stages, runtime byte oracle, runtime corpus and official MCP SDK checks.
- [79 packed-cache controls](FOUNDATION-0.31-PACK-VERIFICATION.json) and [58 incremental-build controls](FOUNDATION-0.31-INCREMENTAL-VERIFICATION.json).
- [4288 memory comparisons, 648 literal-size comparisons and 12 refusals](FOUNDATION-0.31-MEMORY-VERIFICATION.json).

The compiler, library and independent adversarial reviews used three actual agent assignments. Agent review is not independent institutional approval. Finite successful controls do not prove absence of defects. Existing nine bounded MCP tools retain their authority; the trusted systems application is not newly executable over MCP.

## Check-only cost

A separate 31-trial comparison uses default code generation/layout throughout, without opt or compact. Median final compile/check costs were 3.970/3.838ms for the small example, 7.499/6.449ms for checksum and 73.155/72.330ms for SHA40. The preserved 0.30 compile medians were 4.001,7.541 and 75.822ms respectively. This compares complete default-mode operations; checking avoids publication but still performs code generation. It is not an application execution speedup or a comparison with optimized/compact compilation. [Raw measurements](CHECK-ONLY-0.31-MEASUREMENTS.json).

## Failures retained and limits discovered

Review reproduced two defects: silent source-literal overflow and unbounded/raw-control token echo. Both were fixed and retested. An early benchmark adapter expected -1 while the application correctly returned null; the adapter was corrected. Intermediate library prototypes encountered the existing array/local-slot limits. Earlier superseded tests are not aggregated into final coverage.

The Mac ran out of disk space while signing a randomized-case image. That run is an environment failure, not a passing stress campaign or a reproduced compiler-codegen defect. Reproducible compiler-stage outputs were losslessly compressed with SHA readback and a local recovery inventory. Sources, runtime binaries and user files were retained. Affected controls were rerun in fresh directories.

Fixed arrays currently share the 256-slot local metadata budget. Their 255-element declaration cap does not guarantee enough room to construct them alongside other locals. Increasing those numbers alone would also exceed the current single-instruction stack-frame encoding for larger payloads. The next coherent storage change needs a separate array arena, checked frame layout and larger-frame lowering with ABI/guard tests. The 128-element search workspace is an explicit current limit.

The search API borrows trusted readable memory ranges; supplied pointers and lifetimes remain caller obligations. It is not arbitrary-pointer validation, full memory safety, concurrent sharing or Unicode normalization. A complete document application still needs richer data/collections, error handling, persistence, search/index semantics and target qualification.
