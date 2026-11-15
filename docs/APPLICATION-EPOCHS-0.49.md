# RF2 0.49: test useful applications, then repair what failed

RF2 now has two additional working native applications and a reusable request adapter, built and challenged through separate AI tasks. This establishes useful behavior within their contracts. It does not prove that the world needs another language, that these ideas are unprecedented, or that AI builds applications with fewer tokens in RF2. Python can do both jobs; the current question is whether RF2 can earn a practical advantage worth switching for.

## What actually ran

Two application agents made fresh shallow public clones of `starkfiber/RiverFlow` at `20dcf1d`. One built Document Audit, the other Sensor Audit. A third read-only reviewer inspected all 17 files in the 0.48 change, surrounding compiler paths and subsequent app/SDK corrections. The lead implemented fixes, integrated source-only deliveries and independently rebuilt/replayed both apps. These were real AI tasks, not thousands of simulated developers, independent human peer reviewers or a blind randomized study. The agents share model/context lineage.

| Deliverable | Executed evidence | Important boundary |
| --- | --- | --- |
| [Document Audit](../examples/document-audit/README.md) | 53 controls per plain/optimized build; CLI/MCP share corpus identity; five cross-version identity checks | Bounded UTF-8 files, exact byte search, sequential capture; no PDF extraction, atomic filesystem snapshot or signature |
| [Sensor Audit](../examples/sensor-audit/README.md) | 149 cases per plain/optimized build and matching Python reference;16 library refusal controls | Recorded fixed-point CSV,32 IDs,4096 rows; no attached sensor, industrial safety qualification or floating-point stack |
| [Typed request SDK](../experiments/typed-requests/README.md) | 354 native controls, including 152 request cases per compiler mode and ownership refusal controls | Post-admission parsing into the existing Booking model; no new authentication system or generic schema compiler |
| Real Booking overlay | Same178 browser-protocol checks;60 additional bounded WhatIF GET requests at concurrency1/4/1 | Expected status/header checks; no capacity/security verdict or fault-injection recovery claim |
| Compiler integration | All15 existing native suites, unchanged nine Core MCP tools and exact signed compiler self-generation | Mac ARM64 source candidate; existing downloads unchanged |

The lead initially replayed Document Audit without its optional JavaScript oracle configured, recording52 checks per mode. Fresh replays with the actual working Node oracle recorded 53. Both sets remain. Node/Python here are development oracles, never native app runtime requirements.

## Failures drove the changes

**Owned destination consumed during its RHS.** Independent review identified `set row.id=try consume(move(row))`. Native 0.48 compilation and execution confirmed admission, violating the moved-owner assignment contract. Candidate 0.49 rechecks ownership readiness after evaluating the RHS and before emitting its field store. Destination and containing-ancestor consumption now refuse on both success/error call variants in plain and optimized modes. The fix preserves the primary error/ordinary cleanup route. It is a scoped correction, not a complete ownership proof. Earlier0.48 tests did not cover this interaction.

**Staging helper imported itself.** The new adapter's staging helper worked as a CLI but failed when imported normally as `stage`. The reviewer reproduced the partially initialized module error. An explicit uniquely named base-module import fixes reuse; normal import and native request/GUI tests pass.

**Valid document index exceeded the agent result budget.** A valid corpus with long escaped filenames produced a 66,985-byte CLI catalog. Returning it unchanged over the generic 65,536-byte MCP payload cap failed. The app now keeps the full index on the CLI and returns a small summary with the same corpus fingerprint through the launch-selected read-only tool. No generic MCP budget or authority was expanded. The original failed oracle is retained.

**Exact native integers were not exact JavaScript wire values.** A real JavaScript JSON roundtrip rounded large sensor timestamps. The explicit v2 sensor wire schema uses canonical decimal strings. The document v2 schema uses `null` for an absent search offset instead of an unnecessary u64-max numeric sentinel. Present offsets stay small integers. Original v1 sources, oracles and results remain historical; these are disclosed wire-contract changes, not retroactive passes under an unchanged v1 oracle. The sensor math oracle and document corpus hash framing are unchanged.

Other retained failures were test-controller defects: a document Python syntax error, a sensor placeholder substitution error and an invalid clone flag corrected before cloning. They were not native compiler/application passes. Evidence assembly also initially descended into deliberately long-path fixtures; the corrected source inventory prunes artifacts before filesystem inspection. No test data or binaries were copied into the source release.

## A real, bounded runtime comparison

The sensor task was compared against a standalone Python stdlib batch implementation and a stronger single-pass aggregation implementation. All 149 functional cases pass for both references. The read-only reviewer found no artificial work or validation shortcuts and compared1640 in-memory oracle outcomes. That additional comparison is an AI review observation, not a source-bound standalone test receipt or a performance measurement.

The fixed benchmark used two warmups and 15 rotated measured trials per arm/workload after the application workers and native qualification finished. It measured a complete new process: startup, regular-file admission, bounded read, strict validation, exact statistics and complete v2 JSON output. Every valid result matched; refusals had exit2 and empty stdout; inputs stayed unchanged. Warm OS/file caches, one Mac ARM64. Median milliseconds:

| Input | Native RF2 | Python batch | Python single-pass |
| --- | ---: | ---: | ---: |
| Header only | 4.743 | 39.595 | 36.864 |
| 128 records | 4.122 | 35.256 | 36.074 |
| 4096 records | 5.243 | 46.979 | 46.269 |
| 4097-record refusal | 5.716 | 37.091 | 36.701 |

RF2 was about 8.8 times faster than the single-pass Python comparator on the 4096-record complete-process job. Startup contributes to this result; it is not an isolated parsing throughput comparison, persistent-service result, comparison with compiled C, energy measurement or language-wide claim. The raw label `late-refusal` refers to 4096 valid rows plus one invalid extra row; this exercises the row-cap refusal, not a carefully isolated last-record parsing benchmark. All timings, variation, hashes and warmups are retained in [the receipt](APPLICATION-EPOCHS-0.49.json). No new AI authoring/token comparison was run; the earlier Python authoring lead remains.

## What we learned from existing systems

Typed validation and explicit multi-value handling are established ideas. We inspected a pinned BSD-3-Clause [Werkzeug source revision](https://github.com/pallets/werkzeug/blob/0f43c6ebd426039e4b99ec22535c2c8a2ec2f69f/src/werkzeug/datastructures/structures.py#L228) and its [MultiDict contract](https://werkzeug.palletsprojects.com/en/stable/datastructures/#werkzeug.datastructures.MultiDict), alongside [Pydantic's documented model policies](https://pydantic.dev/docs/validation/latest/concepts/models/). That review supports separating repeated-field admission, schema conversion and effects. It does not establish RF2 novelty or an RF2-versus-framework performance result. No third-party source was vendored.

RF2's adapter leaves strict duplicate/token admission in the existing parser, normalizes typed fields once, and copies the complete request only after success. The application-local decoder moves from 82 lines to a three-line shared call, while the reusable domain/generic modules add 56 and 43 lines. This is reuse and a stronger failure contract, not a net code reduction or measured token saving.

## The value claim and its next falsification

| Hypothesis | Current result | Next decisive evidence |
| --- | --- | --- |
| RF2 can deliver useful native tools with bounded agent access | Supported for Document Audit and the tested Mac CLI/MCP contract | Independent user installation and a second platform |
| Reusable validation can preserve state after failures | Supported by canary-field, storage and browser checks in this adapter | General schema/composition tests beyond Booking |
| Existing ownership checks were sufficient for the new syntax | Refuted for 0.48; the reproduced path is corrected/tested in 0.49 | Broader expression/alias/ownership interactions |
| RF2 can reduce complete short-job runtime | Supported for this sensor CLI versus the two tested Python references | More workloads, persistent processing and equally optimized native competitors |
| RF2 reduces AI application-authoring time/tokens | Still unproven; prior study favors Python | Preregistered second matched app task, actual provider usage, all failures retained |
| RF2 is uniquely necessary or universally portable | Not established | Independent adoption and target-specific implementations/qualification |

The remaining engineering priorities are versioned SDK/package/import roots, broader reusable data/schema support, actionable diagnostics, qualified target adapters and real user learning evidence. Copying the internal SDK into each example exposed a packaging gap; pinned provenance limits drift but does not solve it. More generated agents or agreement alone cannot prove adoption, novelty or universal safety.

Linguist remains pending and nonblocking. This is 0.49 source-candidate work, not a new stable binary release or thesis approval. Reviewed evidence is recorded in the existing ThesisPro RF2 project; that notebook stores evidence and AI-assisted review, not an independent academic council. No PDF, MBA/Sabah manuscript, hardware device or shared Kanika Memory was changed by this software sprint.
