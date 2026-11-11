# SFE public research bridge

Historical JavaScript reference server only. Native0.6 has five different tools; see NATIVE-CORE.md. The catalog/batch/C-emission tools below are not automatically native capabilities.

RiverFlow 0.3 exposes ten MCP tools through one local server. All 20 inventoried public repositories have shared discovery and pinned-document access through that server. This does not install a separate executable adapter into every application. Asset repositories receive documentation access; forks keep their upstream attribution and licences.

The five approved history migrations change identity metadata only. No application code in those repositories is changed by this bridge.

| Tool | Executed behavior |
|---|---|
| rf2_status | Exact language capability boundary |
| rf2_check | Parse and type-check supplied source |
| rf2_run | Bounded evaluation over supplied arrays |
| rf2_run_batch | One parse/check followed by up to 20 bounded evaluations |
| rf2_emit_c | Emit checked C11 source without compiling or executing it |
| sfe_repositories | List pinned public portfolio snapshot |
| sfe_repository | Inspect one allowlisted repository |
| sfe_repository_document | Fetch its root README at the pinned commit, with timeout and size limit |
| sfe_research_map | Read proposed research-to-code relationships and limitations |
| sfe_compare_measurements | Ratios and change from caller-supplied matched measurements |

Example sequence: inspect `sfe_repository` with `name: "ThesisPro"`, retrieve its pinned README, inspect `sfe_research_map` with `topic: "Kernel 8"`, then check and run a supplied RF² program. A source README is data, not authorization to execute its installation commands. No remote command dispatch, infrastructure access, private thesis upload or automatic device operation exists here.

The public catalog records files with MCP-related names as observed paths. Such discovery can include documentation, third-party dependencies or proposals; it is not runtime verification. Native tool execution must use the actual installed service and its current permission checks. The bridge never invents a native tool result.

## Measured optimization

`tools/benchmark.mjs` compares repeated parsing, prepared RF² evaluation and a simple checked JavaScript loop using identical arrays. The one-process local run found prepared evaluation faster than reparsing by about 4.81× for 8 words, 1.21× for 256 words and 1.02× for 4096 words. The direct JavaScript loop remained much faster: prepared RF² cost about 96×, 155× and 166× as much per call in those cases. These are descriptive warm measurements on one host, not general speed claims. Parsing/setup is excluded only from the prepared variant. All raw trials and source hash are in BENCHMARK.json.

This supports avoiding repeated parsing for repeated small jobs. It does not support replacing optimized JavaScript/native code on performance grounds. Next experiments should repeat across processes and compare a versioned native backend at equal error and effect semantics. No hypothesis or publication status in the private thesis library is promoted by these measurements.

## Native emission in 0.3

The text-only rf2_emit_c tool adds C11 emission, bringing the server to ten tools. It does not invoke a compiler or run a binary. Native host differential tests and the selected sum optimization are described in the book, docs/SPEC.md and NATIVE-BENCHMARK-RUNS.json. The selected optimized sum approaches the manual baseline; broad superiority is not established.
