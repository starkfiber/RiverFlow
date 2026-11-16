# RF2 0.50: reusable packages, diagnostics and an honest construction test

RF2 applications can now share one explicit, versioned source SDK. Native compiler errors have an opt-in structured format with original source locations and repair hints. Four fresh AI authoring attempts built Passage Desk in RF2 and Python. All passed the original80-check oracle, but additional output-failure probes found gaps in three deliveries. Those failures led to a separate shared-library repair.

**Python still required less time and reported usage for this task.** Native compilation is already a small part of the measured RF2 effort. The next practical improvement is higher-level typed report/serialization composition and fewer repair steps, not an unsupported claim that faster machine code automatically makes AI authoring cheaper.

[Full receipt](SDK-PACKAGES-0.50.json) · [Source-only evidence archive](evidence/SDK-PACKAGES-0.50-SOURCES.tar.gz) · [Package](../sdk/README.md) · [Working repaired app](../examples/passage-desk/README.md)

## What is implemented

The native compiler accepts imports such as `use "@rf2/v1/text.flow"` with `--sdk-root /absolute/selected/package`. A bounded manifest fixes version, paths and SHA-256 identities. Missing, altered, duplicate, cyclic, shadowed, traversal and nonregular inputs have refusal controls. There is no network registry, install fallback or implicit search path. Existing local imports remain entry-rooted. The selected directory/parent paths are trusted; identity hashes are not publisher authentication or filesystem containment.

The ready-to-use [sdk/v1](../sdk/v1/) exports six source modules for IO/writers, text, JSON, bounded read-only MCP, collections and SHA-256. Two different source directories can compile against it without copied libraries. A separately named overlapping KMP search preserves the previous nonoverlap API. Query1..128 bytes, input1 MiB, code-point text validation and exact-byte offsets remain explicit.

`--diagnostic-json` produces one `rf2.diagnostic.v1` stderr object on compiler failure, with a narrow stable code, original message, useful hint and source location or honest null. Default human errors remain available. Source positions are byte cursors and may follow the offending token; generated origins are labelled. Path strings use reversible escaped bytes, not an assumed Unicode filesystem path. This is not source-secret redaction or automatic repair. [Diagnostic contract](../experiments/diagnostics-050/README.md).

The compiler was already at254 of256 functions. This edition expands18 explicitly inventoried function-indexed tables to512; local slots remain256, record types32, source files32, active import depth16 and aggregate source budget512 KiB. High-index arrays, owned returns/parameters, cleanup, reuse and function513 refusal were tested. This is a bounded expansion, not unlimited compilation or general memory-safety proof.

## Actual native qualification

| Evidence | Executed result |
| --- | --- |
| SDK import/package controls | 96 passed in the combined candidate; final SDK B repeated96 |
| Structured diagnostics and function tables | 169 controls passed |
| Prior request/ownership regression controls | 354 passed |
| Existing native suites | All15 passed, including unchanged nine Core tools |
| Exact self-generation | Signed bytes identical with matching `--compact --opt` |
| SDK B transport | 41 controls in each plain/optimized mode |
| Document Audit using external SDK B | Same53 controls passed per mode, including MCP/JavaScript |
| Repaired Passage Desk | Original80 controls and three additional output faults passed per mode |

Seven mocked builder controls and eight controller integrity controls are separate from native execution. The actual WhatIF source scan found no heuristic leads in five selected Python files; its extension filter did not cover `.flow`. Direct source review/native tests cover different questions. None is a security certification or human learner trial.

## Frozen Passage Desk construction results

The new task is a bounded, read-only text-review application with exact JSON metrics/search, an escaped static HTML report and one launch-selected read-only MCP tool. It is not Booking, the manifest-based Document Audit entry, an interactive GUI or a service deployment. Both languages received equivalent warm text/read/search helpers, a generic MCP helper and the same task. No complete app/report/renderer was supplied. Preparing those libraries/compiler was excluded from the authoring timer.

Four installed Codex CLI0.166.0-alpha.5.1 attempts ran in fixed order Python, RF2, RF2, Python, each with a600-second limit. Requested model `gpt-6.1-sol`, reasoning low; served identity was not inferred. The timer includes the author's reads/writes, compilation/signing, debugging and self-tests; external grading is excluded. No parent app repair or feedback entered these calls. Every supplied task/guide/helper/compiler remained unchanged.

| Attempt | Language | Authoring seconds | Total input | Cached subset | Uncached input | Output | Commands | Frozen grade | Extra output faults |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Python | 208.7 | 222,522 | 203,648 | 18,874 | 8,659 | 7 | 80/80 | 1/3 |
| 2 | RF2 | 397.9 | 637,262 | 616,192 | 21,070 | 14,252 | 21 | 80/80 | 3/3 |
| 3 | RF2 | 294.8 | 530,952 | 492,416 | 38,536 | 10,716 | 18 | 80/80 | 1/3 |
| 4 | Python | 162.9 | 195,061 | 165,888 | 29,173 | 7,146 | 12 | 80/80 | 1/3 |

Median authoring time: **RF2 346.3seconds, Python185.8seconds**. Median total input: RF2 584,107, Python208,791.5; uncached input29,803 versus24,023.5; output12,484 versus7,902.5. Cached input is a subset, never added again; reasoning output is also not added to total output. These are provider-reported usage counts, not invoices. Two attempts per language, one Mac, fixed order and warm SDKs cannot establish a general language productivity ranking. This is a new task, so the values are not a causal before/after improvement over the earlier Booking study.

The execution was **interrupted and explicitly amended** after attempt2: the source inventory incorrectly treated legitimate self-test FIFOs and a local symlink as fatal. Read-only review confirmed the fixtures stayed in the attempt. Original controller, stopped report, frozen inputs and both results remain. Only the original unexecuted slots3/4 continued, with unchanged model/task/grader/SDK/compiler and a separately bound amendment. No calls were replaced or rerun. The original controller was hash-bound retrospectively at the interruption; it was missing from the first frozen map. [Exact correction and limits](../experiments/sdk-task/AMENDMENT.md).

## What the extra probes revealed

The frozen oracle did not test every mandatory output-failure condition. Separate real child-process probes after all calls checked a closed pipe reader, absent stdout at startup and absent MCP stdout. Attempt2's own checked transport handled all three. Attempt3 received SIGPIPE on report output and exited1 inside the old MCP helper. Both Python apps correctly handled an ordinary broken pipe, but absent stdout produced an unhandled report failure and an MCP session that silently discarded responses. Original80/80 scores remain; do not translate them into complete task compliance.

SDK **B is a post-study repair**, with a different manifest from timed SDK A. It preserves the old protocol/parser/schema but returns transport errors through ordinary `IO`, stops after the first write error and restores the borrowed stdout descriptor's no-SIGPIPE flag. Explicit `io_write_no_sigpipe` gives CLI callers the same policy while retaining old `io_write_all` behavior. Primary errors survive restoration failure; restoration-only errors are tagged65536+errno. No global signal handler is changed.

Actual controls covered EPIPE, EBADF, EAGAIN, partial delivery before peer closure, initial flag states0/1, regular files/pipes, owned-resource/deferred cleanup and callback recovery. Restore-only failure precedence used labelled source hooks, not invented kernel failures. TTY, other platforms, concurrent descriptor mutation, fatal traps and cancellation cleanup remain unqualified. A failed write may already have delivered a prefix. One active process-local MCP session is supported; reconnect/reentry is not qualified.

The [published exemplar](../examples/passage-desk/) is a copy of attempt3 with one explicit IO import and two checked-writer substitutions, rebuilt against SDK B. It passes the unchanged80-check oracle plus the three extra faults in both compiler modes. This later repair receives **no retroactive authoring-time or token credit**. Original SDK A and all original source deliveries remain in the archive.

## Build time versus authoring time

Ten post-study clean rebuilds/signs reproduced both original RF2 app images exactly. Median native compilation was12.27ms; median compile-plus-ad-hoc-sign was35.40ms on this warm Mac. These are separately measured stages, not the hundreds of seconds spent constructing an app. Python did not require an ahead-of-time native build; its interpreter startup or syntax check is not an equivalent compiler comparison. No new runtime, energy or universal speed claim was measured here.

## Reproduction and retained failures

Use the exact [public0.46 development compiler](https://github.com/starkfiber/RiverFlow/releases/tag/v0.46.0-dev) with the hash-pinned [build helper](../experiments/sdk-packages/build.py). A fresh anonymous clone plus seven enumerated new source overlays reproduced candidate `4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c` and its signed self-generation. No hidden artifact source or download fallback is required. Python is development preparation tooling; the resulting compiler/apps are native. Signing is ad hoc, not notarization or publisher authentication.

Preserved failures include the initial256-function bound; a hanging FIFO manifest fixed with nonblocking regular-file admission; an eager argument guard crash fixed before qualification; unsigned/signed comparison mistakes; an unmatched compact/full-layout self-build; a basename-dependent ad-hoc signing comparison; the interrupted inventory and initial controller fixtures; a missing SDK path in a parent command; and builder timeout logs initially lost before correction. Old compiler outputs, receipts and controller failures were retained rather than relabelled. New timeout controls are explicitly mocked; the subsequent fresh-clone compiler rebuild was real.

Stable0.17 and public0.46 downloads remain unchanged by this source edition. Core MCP authority remains unchanged. Linguist is pending/nonblocking; the fixed delivery ledger is not reset or a claim of universal completion. No thesis/PDF, workplace/physical sensor result, human academic council, remote Memory or shared compute was changed.

Next: typed JSON/HTML serialization and report composition that removes manual writer/transport work, followed by a separately frozen comparison. SDK reuse and clearer errors are implemented; a complete-task AI advantage still needs to be earned.
