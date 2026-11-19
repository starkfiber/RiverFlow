# Simple V3: choose, repeat and reuse

19 November 2026. Local Apple Silicon macOS candidate. No Git commits, pushes, deployment, installed upgrade, live infrastructure, remote Memory or thesis/PDF work.

## Working language extension

```flow
fn double(n)
 return n * 2
end
let points = 0
repeat 3 times
 set points = points + 10
end
if points >= 30
 say "Level up!"
else
 say "Keep practising."
end
show double(points)
```

The program prints Level up! and 60. Root ./rf2 now selects the qualified V3 candidate. [The learner lesson](../guide.html#control) introduces one idea at a time before the games. The old native course and Core runtime are preserved separately.

* `if EXPR` / optional `else` / `end`, numeric zero=false and nonzero=true.
* `repeat EXPR times` / `end`, count calculated once per entry.
* `while EXPR` / `end`, condition recalculated before each iteration.
* `fn name(inputs)` / one `return numeric-expression` / `end`; forward calls allowed. Small functions use their own numeric inputs and other small functions; no global reads, IO, statement bodies, recursion or closures in this Simple subset.
* Comparisons `== != < <= > >=` normalize to 0/1. Unparenthesized comparison chains reject; explicit parentheses can compare computed 0/1 values. Arithmetic contracts remain checked u64, exact `/`, floor `//`, remainder and right-associative `**`. Negative/floating values, text comparisons and and/or/not expressions are not implemented here.

Let/new ask declarations belong at top level. Inside blocks, set or ask an existing same-kind name. Ask can update an existing name; let cannot redeclare it. Function names cannot collide with variables. Function `main` is reserved to avoid confusing a Simple function with a native entry point; variable/parameter main remains legal. Full native programs use ./rf2 native FILE.flow and retain their broader existing grammar.

Limits: 64 meaningful source lines including fn/return/end, 32 variables, 8 nested blocks, 8 functions, 4 parameters, 16 guarded call-depth (valid acyclic 8-function graphs cannot reach that defensive limit), repeat count<=1000. Dynamic/control execution shares a 4096-unit instruction/expression budget across loops and calls. Empty loop back edges still consume work. A larger body can exhaust work before 1000 iterations. Parsing, type validation and constant folding have separate finite source/expression limits; this logical execution counter is not wall-clock CPU, an input deadline or an OS sandbox.

## Programs actually exercised

| Program | Authored lines | Complete small journey |
|---|---:|---|
| Work Planner | 11 | Jobs/workers, guarded zero-worker branch, rounds via a reusable numeric function |
| Guessing Game | 21 | Fixed secret 7, at most three questions, higher/lower hints, win/loss |
| Double Quiz | 21 | Three rounds, function reuse, re-asked input and scoring; 2/4/6 scores 30 |

Sources are copied into academy/examples/simple; all three work through quick execution and saved CLI executables. These are small CLI apps, not graphical games, random-number proof, production scheduling, hardware tests or evidence of human learning outcomes.

## Failure-first evidence

The independent r2 campaign exposed three quiz failures: re-asking an even-indexed variable was incorrectly treated as a new declaration. The root cause was bitwise `asking & existing` on a one-based index. Using Boolean `all(asking,existing)` fixed it. A new 128-case matrix checks every one of 32 slots, both text/number kinds, inside/outside blocks.

A raw `fn main(argc,argv) return 0 end` declaration initially counted as a pure function rather than an executable entry. It never executed host code, but main is now explicitly reserved; the original cross-profile refusal oracle remains unchanged.

A reviewer found new function/arity/cycle/work errors fell through to an arithmetic hint. All four live user cases now have appropriate hints. The defensive call-depth branch has a native helper unit test, not a fabricated public-source trigger.

Saved, correctly signed single Mach-O files named .app sometimes died with SIGKILL. Same-byte plain/.bin copies ran; case, copy, rename and provenance observations are retained. Rename/cache observations mean the actual macOS execution cause is unresolved, not proven to be a simple extension policy or language error. The build command now rejects case-insensitive .app outputs before creating anything: it creates CLI executables, not real app bundles. No security attributes were removed and no OS safeguards disabled.

An additional failed suffix fixture reused case-only basenames on case-insensitive APFS. Unique basenames fixed the fixture while retaining the same absence/preservation oracle. Its failed report and exact old controller/corpus remain preserved. No behavioral oracle was relaxed to obtain a pass.

Two V2 same-kind duplicate-ask refusals intentionally migrate to update/re-ask behavior. The older declaration-only migration remains explicit. Native raw entry/effect refusals remain. Input/preflight/staging rules from V2 continue, with inspect marking questions as potential because control flow may skip or repeat them.

## Qualification

| Scope | Observed | Evidence |
|---|---|---|
| Independent frozen r4 | 622/622 controls, quick/build/saved coverage; 346 V3, 167 V2, 102 legacy, 4 IO and 3 packaging |artifacts/simple-control-apps-20261119/candidate-r4-fresh/results.json |
| Promoted exact root launcher | 75/75 fresh checks: eight app/game journeys, four lessons, preservation, IO, six original native lessons, MCP |artifacts/simple-control-root-20261119/RESULTS.json |
| New math comparisons/functions | 2104 assertions / 2048 native cases ordinary+optimized |artifacts/simple-control-math-20261119/INDEX.json |
| Math compatibility |Original 1749 variable and 1110 numeric checks passed unchanged |artifacts/simple-control-math-20261119/INDEX.json |
| Protected boundaries | 14 controls per compiler mode |artifacts/simple-control-math-20261119/guard-r1/RESULTS.json |
| Independent source/runtime review | 60 controls, jumps/counters/scope/dead branches/shared budget/forward calls and hints |artifacts/simple-control-review-20261119/r4/RESULTS.json |

Counts overlap between suites and are not a sum of unique human trials. Raw failures, reference-oracle grammar corrections, source/controller snapshots and all artifact identities remain indexed. Python AST's trailing-comma/numeric-underscore allowances were excluded to match this explicit grammar; no native bug was concealed by doing so.

The new executor remains native RF2. Saved control/variable programs include the native Simple engine plus embedded source, not direct specialized lowering for every statement. Constant-only builds retain the earlier specialized path. No C/assembly, AI-token, development-time, energy or universal speed advantage is established by this extension.

## MCP and platform direction

Actual ./rf2 mcp status was the first tool call and reported stable 0.17.0, exactly nine Core tools, bounded sum 6 and refusal of Simple if/repeat/fn/ask and raw native source. Core/compiler/old release archive hashes, Git HEAD and SFE push hold remain unchanged. CLI inspect reports V3 functions, configured work/repeat limits and potential typed questions; it is not a new registered MCP tool or an interactive JSON-RPC input channel.

The owner goal stays one RF2 creation system across applications, devices, networks and operating systems. These friendly constructs and reusable capabilities advance the teaching layer; target backends, drivers, OS services, AI hosts, packaging and acceptance tests remain explicit independent work. No claim that a short verb supplies an unimplemented device or model.

## Landing page and local kit

The matching SFE page is prepared at web/starkfiber-rf2 for intended https://starkfiber.my/rf2/. It is previewed on loopback, not published. Its browser walkthrough is explicitly illustrative; downloadable .flow files are actual tested sources. Public 0.17 downloads are not relabelled as V3. The relocatable RF2-Learn-V3-macos-arm64 kit is 214,221 bytes. A fresh extraction outside the checkout with PATH unavailable passed 58 checks: three apps quick/saved, six native course examples, a reviewed three-module SDK subset, help, signatures/permissions, MCP status-first/nine tools and output protections. It needs no repository, Node or Python user runtime. It is ad-hoc signed and not notarized. SHA256 c4264573195752681c08dd442700a0e4acd908f12a4c5713d298ca57324269bd. Kit evidence: artifacts/simple-control-package-20261119/INDEX.json.

An optional-helper quoting concern from static review was explicitly retracted after actual execution showed correct quoting; four extra helper checks passed. No fictional package bug/fix is claimed. Earlier r1 and final r2 ZIPs are byte-identical. Final browser/package evidence is indexed in the website handover and the combined final audit.

Next: smaller/directly lowered dynamic programs, broader beginner functions/control constructs, signed/floating semantics, a bounded supplied-answer agent interface and genuinely held-out authoring studies with actual usage. Keep platform/firewall gates and the fixed delivery ledger separate. No actual child/classroom trial, universal parity or automatic intelligence claim.


Website adaptation note: captured from the project-owned report on 19 November 2026. The learner link points to this offline guide. Evidence paths identify retained project-local receipts; they are not claimed to be public files included with this site.
