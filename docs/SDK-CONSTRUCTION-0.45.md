# Complete-app SDK construction: RF2 and Python

Four fresh, counterbalanced AI coding attempts assembled the same Study Rooms application: durable multi-room CLI, a protected local browser GUI and read-only MCP. **This run did not establish RF2's proposed complete-development speed or token advantage.** It produced working applications and useful, reproducible defects to fix.

The experiment used one Apple Silicon Mac, Codex CLI0.166.0-alpha.5.1, the same CLI/default configuration and a900-second cap for each attempt. Exact served model/provider identity was not emitted in the retained JSONL; it is unknown, not inferred from an assistant's name. This is an exploratory construction comparison, not a controlled claim about a named model.

## Actual initial outcomes

The [task](../experiments/development-task/TASK.md), [protocol](../experiments/development-task/PROTOCOL.md), SDKs and original independent grader were frozen before attempts. Neither language received a complete application entry. RF2 received the qualified0.44 compiler and existing domain/storage/parser/HTTP/UI modules. Python received the conventional domain/store SDK over SQLite and the standard library. Setup was pre-existing and excluded from this **warm SDK reuse** task. Different helper surfaces/storage formats prevent a language-only causal interpretation.

| Attempt | Language | Task seconds | Original checks | Reviewed checks | Complete without parent repair |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | RF2 | 382.6 | 54/55 | 54/55 | No |
| 2 | Python | 232.1 | 53/55 | 54/55 | No |
| 3 | Python | 245.8 | 55/55 | 55/55 | Yes |
| 4 | RF2 | 407.5 | 54/55 | 54/55 | No |

Task time includes source discovery, generation, local commands, self-tests and repairs inside the fresh attempt. Outside grading is separate. Both languages were authored by AI; this is not a human-versus-AI contest. Two attempts per language do not establish a robust population advantage.

Actual CLI-reported usage, with cached input included in total input:

| Attempt | Input tokens | Cached input tokens | Output tokens | Completed local commands |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1,359,217 | 1,312,512 | 14,953 | 27 |
| 2 | 229,326 | 201,088 | 9,226 | 9 |
| 3 | 289,467 | 265,216 | 9,371 | 10 |
| 4 | 1,433,243 | 1,386,240 | 16,473 | 26 |

These are emitted usage receipts, not estimates from source length. Cached tokens represent reused context across requests; these totals are not unique source tokens or dollar-billing receipts. No RF2 original attempt completed every required check, and parent review/repair usage was not separately metered. **A successful end-to-end token-saving ratio is therefore not established.** No90-percent saving, runtime-speed, energy or universal stack claim follows.

## What failed and what was corrected

Three generated applications reported an **unknown tool** as an `isError` tool result instead of a JSON-RPC protocol error. They refused the request and preserved the selected file, but used the wrong protocol category. The [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling) distinguishes unknown-tool protocol errors from tool execution/validation errors. The separately qualified0.45 release already uses protocol errors for unknown tools; these generated samples did not replace it.

The original grader also rejected Python attempt2's useful “revision changed” feedback because its wording whitelist was too narrow. Its input-validation refusal check required a protocol error even where a tool validation error is permitted. After all four attempts finished, a separate reviewed grader corrected those two criteria for **every unchanged original**. The original sources, scores and grader remain available; unknown-tool protocol errors are still required. The reviewed scores are shown above. Python attempt2 advances from53 to54, retaining its genuine protocol failure.

A one-site protocol correction was then applied to copies of the three failing applications. Both RF2 copies rebuilt natively; all three repaired copies passed55/55 reviewed checks. The fourth, unmodified Python attempt already passed. These fixes do not retroactively turn original attempts into complete successes or supply missing repair-token accounting. [Source-bound receipt, exact fixes and raw report identities](SDK-CONSTRUCTION-0.45.json).

## What the tests actually exercised

The55 acceptance controls cover new/reopened files, exact u64 IDs, canonical dates/times, invalid inputs, overlap/adjacency, separate rooms/days, stale cancellation, eight simultaneous processes, real loopback HTTP, Host/Origin/token/form admission, unchanged data after refusal, retained input, GUI/CLI shared commits, read-only tool discovery, actual saved data, malformed/duplicate JSON and recovery. The original reference calibration passed55 controls; a controller name-shadowing bug was found and corrected **before** freezing attempts.

Agent execution denied loopback bind, so the agents used local socket-pair/in-memory HTTP self-tests and honestly reported that limit. The external grader subsequently exercised the delivered servers through real loopback requests. Browser visual/learner judgement is separate; this is not a human usability or accessibility certification.

The RF2 agents also found that a1MiB append-only snapshot history fills before256 consecutive reservation inserts. They explicitly enlarged their **private SDK copies** to16MiB/4MiB, mapped missing-file errors and removed the server's request-count stopping cap to meet the task. One adjusted UI layout. Those changes, source hashes and library diffs are retained; the public0.45 release was unchanged. Broader modified bounds do not automatically inherit its earlier fault/size qualification. The maintained application still has both a256-row type cap and a1MiB journal budget, which can stop new saves earlier as history grows.

## Inspect, rebuild and learn

All four [original application sources and SDK diffs](../experiments/development-task/samples/INDEX.json), the separate protocol repairs and reproducible [rebuild helper](../experiments/development-task/rebuild.py) are published. Fresh reconstruction reproduced both original RF2 signed application images byte for byte. A repaired reconstruction passed all55 controls. Raw model traces remain local because they contain internal execution metadata; their digests and actual usage fields are retained in the reviewed public receipt.

The next engineering opportunities are specific:

1. A reusable MCP dispatcher should enforce protocol error categories so each application does not recreate the same logic.
2. Compact, discoverable SDK signatures/examples should reduce full-source reading and repeated context. The observed RF2 attempts required more commands and generated more output here.
3. Typed-record declaration placement and unique handler-binding rules caused practical repair work; improve those contracts/diagnostics before claiming beginner ease.
4. Storage budgets should be explicit application policy with a tested history/compaction plan, rather than repeated edits to literal limits.
5. Repeat a stricter, explicitly model-pinned study and genuine learner trials before claiming general AI or human productivity gains.

These are next improvements, not completed features or new performance claims. The fixed delivery ledger credits an **executed comparison**, not a win. Actual upstream language adoption/recognition remains open.
