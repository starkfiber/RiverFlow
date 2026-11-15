# Application effort: source candidate 0.47

**The corrected RF2 apps pass the task; Python still wins this construction comparison.** The work improves actual SDK correctness and reduces reported input against the first revised RF2 SDK. It does not establish faster application development, lower provider bills or universal language superiority.

[Machine-readable measurements](APP-EFFORT-0.47.json) · [Clean rebuild/replay receipts](APP-EFFORT-0.47-REPLAY.json) · [Developer kit](../experiments/app-effort/README.md) · [Source-only evidence archive](evidence/APP-EFFORT-0.47-SOURCES.tar.gz) · [Archive checksum](evidence/APP-EFFORT-0.47-SOURCES.tar.gz.sha256)

## What changed

- Same-contract scalar error propagation: `let n=try operation()`, `set n=try operation()`, `do try operation()`; direct `return operation()` forwards a matching scalar result. Both retain ordinary cleanup and primary-error rules. These are not exceptions, general owned-result forwarding or tail-call elimination.
- A reusable bounded legacy MCP dispatcher replaces repeated protocol code. It validates requests, retains IDs across callback parsing, refuses tool notifications, distinguishes protocol/tool failures and compacts valid callback JSON into one physical line. Application callbacks still require a separate read-only review. No new Core permissions.
- API contracts and 29 native lookup cards can be queried together instead of dumping libraries. Exact source signatures and locations are included; the records_read card explicitly describes an intrinsic.
- Journal budgets are explicit before first use: 1 MiB default, up to 16 MiB; the tested app selects4 MiB. Each process reading a larger journal needs a sufficient budget. Current rows remain capped256. This does not implement history compaction.
- Server lifetime policy is explicit: 4096 processed connections by default, or 0 for serve-until-terminated. Existing connection, framing and I/O deadlines remain.
- Fixed all-control-byte JSON escaping, the domain capacity code27, HTTP form rejection/status handling, hidden UI module dependencies and a response helper that incorrectly sent its old buffer instead of a supplied private Writer. The actual Booking GUI uses shared admission.

## Frozen complete-app construction

The task is the same local Study Rooms CLI, browser GUI and read-only MCP app, with persistence, overlaps, exact IDs/dates, failed input, eight simultaneous writer processes and denied requests. Domain/storage SDKs were supplied in both languages; no complete entry was provided. All runtime RF2 app logic compiled natively. Python used its standard library and SQLite.

Six v2 attempts compared the original0.44/0.45 SDK with initial0.47 candidate A and Python. Their failures exposed further SDK defects. Four v3 attempts used corrected candidate B, native targeted API lookup and the same bounded-source-inspection guidance for both languages. These are two separate exploratory studies, not one randomized ten-run experiment.

Requested model: **gpt-6.1-sol**, reasoning **low**; installed CLI 0.166.0-alpha.5.1, one Apple Silicon Mac/macOS 26.5.1,900-second maximum per attempt. Exact served identity was not inferred. JSONL events retain actual usage, commands, failures and timings. SDK/compiler development, external grading and later replays are excluded from timed authoring. No parent repairs occurred during attempts.

### Initial round v2

| SDK | Fully passing attempts | Median authoring seconds | Median total input | Median uncached input | Median output | Median commands |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original RF2 SDK | 0/2 | 475.7 | 1,420,069.5 | 49,189.5 | 17,345.0 | 27.5 |
| First revised RF2 SDK (A) | 0/2 | 424.0 | 1,551,345.5 | 47,537.5 | 15,994.5 | 28.5 |
| Python | 2/2 | 327.1 | 359,590.5 | 35,942.5 | 13,667.5 | 10.5 |

### Corrected round v3

| SDK | Fully passing attempts | Median authoring seconds | Median total input | Median uncached input | Median output | Median commands |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Corrected RF2 SDK (B) | 2/2 | 455.7 | 1,152,032.5 | 44,064.5 | 16,471.0 | 27.0 |
| Python | 2/2 | 284.9 | 396,200.0 | 28,968.0 | 11,713.0 | 10.0 |

Against the first revised RF2 SDK, corrected RF2 median total input fell **25.7%**, and uncached input fell **7.3%**. Median authoring time increased **7.5%** and output increased slightly. The two corrected RF2 apps passed 55/55, while the earlier revised apps failed three checks. This is a mixed result, not an overall speed win. Python remains faster and uses less reported input/output.

Cached input is a subset of total input, not an additional charge or an assumed free resource. Reasoning output is not added again to total output. These receipts do not establish a provider bill, inference speed, token savings on other tasks, or time-to-success for the failed attempts. Two trials per arm cannot establish a broad productivity ranking.

### Every original attempt remains visible

| Round / attempt | SDK | Seconds | Strict grade | Fully passed |
| --- | --- | ---: | ---: | --- |
| v2 / 1 | oldRF2 | 472.9 | 44/47 | no |
| v2 / 2 | newRF2 | 435.9 | 52/55 | no |
| v2 / 3 | python | 318.2 | 55/55 | yes |
| v2 / 4 | python | 336.0 | 55/55 | yes |
| v2 / 5 | newRF2 | 412.1 | 52/55 | no |
| v2 / 6 | oldRF2 | 478.4 | 45/47 | no |
| v3 / 1 | python | 283.9 | 55/55 | yes |
| v3 / 2 | newRF2 | 403.1 | 55/55 | yes |
| v3 / 3 | newRF2 | 508.2 | 55/55 | yes |
| v3 / 4 | python | 286.0 | 55/55 | yes |

Some failed legacy GUI sequences terminated early on connection resets, so fewer checks were reached. These are failures, not shorter successful solutions. v2 combined HTTP checks required 400/403, while its task text said no data mutation/visible errors without specifying those statuses. Diagnostic replays confirmed that both initial revised RF2 apps returned 200 but left data unchanged on all three rejected forms. Their original 52/55 grades remain. v3 made the same existing status requirement explicit for both languages; the grader itself was unchanged.

The original legacy final attempt passed 45 of 47 checks in its first failing sequence; its replay reached more before the remaining failure. Transport-dependent variation is retained in the replay receipt rather than replacing the original score. Read the exact original checks/counts in JSON.

## Native qualification and source binding

**15 native suites passed**, with explicit historical reference compilers and the already documented 0.46 owned-row extension mode. The compiler rebuilt itself to identical signed bytes. Existing public binaries remain untouched.

| Suite | Checks/cases |
| --- | ---: |
| try_verify.py | 102 |
| app_effort_verify.py | 274 |
| app_policy_verify.py | 9258 |
| structured_results_verify.py | 120 |
| multiple_views_verify.py | 18 |
| owned_rows_verify.py | 480 |
| nested_owned_verify.py | 452 |
| owned_functions_verify.py | 432 |
| owned_values_verify.py | 460 |
| application_values_verify.py | 687 |
| heap_collection_verify.py | 64 |
| typed_booking_verify.py | 1350 |
| booking_web_verify.py | 178 |
| booking_agent_verify.py | 794 |
| verify.py | see Core counts below |

The 9,258 policy assertions include repeated sequential HTTP requests, not 9,258 different real users or bugs. Each compiler mode actually saved 256 reservations into a 1,346,680-byte journal, refused the 257th current row, reopened from another process and independently checked schema, rows, SHA chain and commit markers. A finite three-request policy stopped correctly; serve-until-terminated survived 4,100 private-loopback requests per mode.

The unchanged nine-tool Core runtime passed 1,016 differential cases against its independent evaluator/numeric oracle, 42 refusals and 250 parser mutations. This is a separate runtime from the Systems compiler and the selected-journal agent.

All six RF2 construction apps were rebuilt from their final source with their original compiler and matched the actually graded signed executable byte for byte. All ten applications were replayed in fresh directories; every v3 app passed again. Python replays used fresh source without prior bytecode caches. No source was repaired during these replays. Original v2 failure scores remain the construction results.

Compiler B SHA-256: `88a7881433f3ca93ee6fac1702faef9bfaaa8a8563b665ad5a62f0a46978089b`. Prepared source SHA-256: `f09c6795beffe7084eb39b140ec33f52594cc1bddb0a52f77ddadd3ad138b80d`. The JSON receipts bind source/controller/report hashes and retain local evidence paths. The source-only archive contains 302 reviewed files including exact frozen setup snapshots, final apps/modified SDKs, original grades and generated compiler A/B sources. Private account/session traces, native images and databases are excluded.

## Remaining gaps and next gate

- Python still has a substantial complete-task advantage here. RF2 needed more tool commands and repair work. Do not market this as solved.
- Remaining friction includes the eight-parameter limit, function-scope record declarations, final root returns, exclusive output creation and manual form/transport state. The final guide adds reminders; those later documentation reminders are not retroactively credited to the frozen calls.
- Next: a safe repeat-build command preserving the last working executable, clearer source-local diagnostics, typed form/request adapters and a second application task. Test these against successful conventional SDKs rather than selecting only a favourable microbenchmark.
- This source candidate is Mac ARM64 trusted Systems work. No new x86/Linux/Windows/mobile/hardware, human learner, whole-language safety or universal performance qualification. Ordinary cleanup does not cover raw interference, fatal traps, exit or signals.
- Public 0.46/stable 0.17 packages remain unchanged. Systems code is not admitted through the original bounded Core tools. The new callback dispatcher is a strict legacy2025-11-25 one-tool subset, not a general modern MCP framework.
- Linguist stays pending and nonblocking at the owner’s direction. Do not manipulate language classification or invent independent adoption.

Method references: [Codex CLI evaluation workflow](https://developers.openai.com/blog/eval-skills), [MCP legacy lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle), [protocol versus tool errors](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling). These references describe methods/contracts; they do not certify RF2.
