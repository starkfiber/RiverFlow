# Simple variables, input and reusable timer lifecycle

18 November 2026. Qualified local Apple Silicon macOS candidate, not an installed or published release. Root `./rf2` now selects the variable/input frontend. Full native grammar, existing releases and the bounded Core/MCP remain separate.

## A small vocabulary with precise meaning

```flow
ask number age "How old are you?"
show age + 1
```

Enter `12`; the program prints the question and then `13`. Six forms cover this lesson:

| Form | Behaviour |
|---|---|
| `say "text"` / `say name` | Display text or a named text/number value, then a newline |
| `show expression` | Calculate and display an exact nonnegative integer |
| `let name = value` | Introduce a number expression or quoted text value |
| `set name = value` | Change an existing value without changing its kind |
| `ask name "question"` | Display the question, read a text line and remember it |
| `ask number name "question"` | Display the question and read a checked whole number |

[The learner lesson](../academy/VARIABLES-INPUT.md) starts with messages and points before input. `./rf2 learn`, `./rf2 help variables` and `./rf2 help input` provide local help. Greeting, floor area and workshop-cost apps are under academy/examples/simple. These are small actual CLI apps; they do not represent an entire booking platform, child learning study or an operating system.

The approach is to introduce meaningful verbs while maintained libraries carry the implementation. Full native RF2 still offers explicit functions/modules, low-level operations and target contracts. A friendly word does not automatically implement a driver, model, operating system or a new target. The full app/device/OS direction remains in OWNER-VISION.md; this sprint advances its teaching and shared-capability layer.

## Variable and input contract

* At most 32 names and 64 instructions in a 64 KiB source. ASCII names start with a letter/underscore, continue with letters/digits/underscores, and have at most 31 bytes. Command words let/set/ask/say/show/number are reserved.
* A name must exist before use. let/ask cannot redeclare it; set requires a previous declaration. Values are text or nonnegative u64; kind changes reject. Text assignment currently requires a quoted literal; text-variable copying/concatenation and interpolation are not implemented. Braces inside strings retain their literal meaning.
* Numeric operators remain checked `+ - * / // % **`, including checked intermediate values, exact `/`, floor `//`, right-associative power and `0 ** 0 = 1`. Negative, floating/scientific values and Simple control-flow statements remain open. Full native has its own existing rules.
* The whole program's grammar, names and kinds are checked before any prompt/read. Expressions validate grammar without evaluating unknown runtime inputs. During build, the prefix before the first ask is evaluated without reading input, catching its deterministic arithmetic failures.
* Answers are at most 1,024 UTF-8 bytes. LF/CRLF terminate a line; the CR in CRLF is not counted. EOF after bytes accepts that final line; EOF before any byte fails. Empty text is accepted; empty numeric input rejects. Numeric answers use canonical digits, no leading zeros except 0, within u64. Tabs are allowed as text data; NUL, other C0 controls and lone/embedded carriage returns reject. No normalization/grapheme or secret-password-input claim.
* Input is data, never source. The reader does not read ahead/discard following answer lines. Prompts append a newline and are flushed before reading. Failed prompt output consumes no answer.
* Prior output is staged until a prompt or successful completion. A failure after input can leave earlier prompts/results already flushed before that input; it does not print the unfinished staged result. External partial writes cannot be rolled back. Interactive reads can wait for a human until EOF/cancellation; there is no hard wall-clock input deadline.

## Inspection and MCP

`./rf2 inspect FILE.flow` returns a JSON grammar/type plan without executing questions or reading answers. It reports profile, command/variable counts, stdin use, input names/kinds/prompts, no program file writes and no program network effects. It is a local CLI operation that reads the selected source, not a new registered MCP tool or proof that runtime input will be valid.

The existing nine Core MCP tools remain unchanged. Actual status is 0.17.0 and explicitly reports no embedded AI model. Raw Simple variables/input and Systems code still reject at that boundary. An AI host can inspect the plan and propose answers, but input-aware tool execution needs a separately bounded contract; stdin interaction must not be mixed into a JSON-RPC stream. No implicit device/file/network authority was added.

## Quick execution versus saved programs

Quick runs use the native Simple executor. Constant-only build requests retain the original specialized native output path. New variable/input builds embed validated source with the native Simple engine; there is no external Node/Python runtime dependency, but they currently retain runtime parsing/evaluation rather than direct specialized lowering for every new statement. This is a material implementation limit, not concealed compiler parity.

Both paths share the same engine. Explicit build refuses existing targets/symlinks and does not ask questions or consume input. Source/engine/artifact hashes are bound in artifacts/simple-input-20261118/promoted-r2/BUILD.json. Local user execution uses RF2 plus macOS tools. Development controllers use Python separately.

## Actual failures and corrections

Independent app tests found five real first-candidate errors: two maximum-length CRLF inputs were rejected and three lone/embedded/double-CR cases were accepted. The reader now reserves the extra CR slot and rejects remaining carriage returns after removing a terminating CRLF. A separate reviewer reproduced invalid UTF-8 on line 2 being reported on line 1; byte-based source line/column reporting is fixed.

The original corpus included a declaration-only refusal because the first edition had no variables. `let answer=42` is now deliberately valid with no output. That single explicit version migration is recorded; no unrelated oracle was weakened. Two optional future probes remain disabled and are not counted as passes. First-candidate failures, concurrent history and successful superseding receipts are retained locally.

The compiler limits function parameters to eight; MathEnv groups the environment rather than inventing a supported nine-argument API. No full-native compiler rewrite was necessary.

## Evidence

| Checked item | Observed result | Receipt |
|---|---|---|
| Independent promoted-root quick/build/standalone | 273 controls: 167 new cases, 102 legacy with one explicit migration, 4 IO/inspection controls |artifacts/simple-input-apps-20261118/root-r2/results.json |
| Variable math, ordinary/optimized and protected boundaries | 1,749 assertions, including 1,732 native environment corpus executions |artifacts/simple-math-20261118/qualification-r2/RESULTS.json |
| Original numeric math compatibility |Original 1,110-check suite passed unchanged |artifacts/simple-math-20261118/INDEX.json |
| Independent candidate-r2 source/IO review | 19 controls, correct source location, protected read buffer, escaped/Tamil input metadata |artifacts/simple-input-review-20261118/r2/RESULTS.json |
| Original lessons and actual root MCP | 27 checks; six lessons, status first, nine tools, sum 6 and rejected new source effects |artifacts/simple-input-final-regression-20261118/RESULTS.json |
| Two timer apps and lifecycle | 81 assertions; five original Focus differential journeys; flags/EOF/cancel/failure |artifacts/focus-lifecycle-20261118/run-r3/RESULTS.json |
| Source/image/startup measurements | 64 checks, raw 21 rotated Hello trials per edition, three apps/six input runs |artifacts/simple-input-measurements-20261118/RESULTS.json |

The actual agents had separate implementation, application/oracle and review assignments. WhatIF failure/invariant/replay discipline and Reverse Lab evidence/council practices were applied to native controllers. No unsupported native WhatIF automatic engine, broad REA decompilation, human student trial or independent academic approval is claimed.

## Cost, without a speed/token claim

* Greeting: 3 authored lines/52 bytes; Rectangle: 5/151; Workshop: 7/191. Their saved images are 83,904 bytes because they include the shared native engine.
* Hello stays 51,072 bytes and is byte-identical to the earlier saved Hello image. The shared frontend grows from 67,488 to 83,904 bytes, an added 16,416.
* Twenty-one rotated launch-inclusive direct-tool Hello trials gave old median 15.853ms (range 10.422..168.023) and new 14.677ms (11.576..48.300). Wide overlapping ranges do not establish a speed win or regression. This is one host/one task, not C/assembly parity, AI task productivity, energy or model-token evidence.
* Focus main source falls from 140 lines/3,182 bytes to 6/403. Stretch is 6/449. The common countdown helper adds 167 lines/4,068 bytes plus the unchanged 112-line/2,173-byte console. The first combined implementation grows; later apps reuse that plumbing. Both timer images remain 51,168 bytes.

The lifecycle helper centralizes duration parsing, checked clock/deadline conversion, progress, input readiness, cancellation/EOF, output and process entry. It does not create services, notifications, files or network requests. Output remains synchronous: a blocked pipe can delay cancellation. Pure clock contract tests are not injected failures of the actual system clock.

## Next bounded work

Direct lowering/size reduction for variable programs; reusable input/lifecycle abstractions beyond timers; signed/floating numeric rules; beginner functions/control flow with the same precise contracts; supplied-answer execution with explicit agent authority. Measure complete held-out app authoring and actual usage before claiming fewer AI tokens. Keep OS/hardware, SDK and firewall gates independent. All work stayed local with no commits, pushes, live changes, installed upgrades, remote Memory or thesis/PDF updates.
