# Typed results and immutable byte views, 0.13

RF2 now has nominal two-variant function results and a compiler-enforced handling statement. It also provides nonescaping, zero-copy read-only byte views for text processing. The language contract is intentionally narrower than generic result types or a general borrow checker.

## Typed scalar result functions

```rf2
result Number(u64, u64)
fn checked(n): Number
 if n == 0
  return err(1)
 end
 return ok(n)
end
```

Both payloads are machine-word scalars in this first result form. The declaration is nominal and must precede uses. A result-returning function returns only `ok(expression)` or `err(expression)` and must have a final root-level explicit return. A function whose branches all return still needs that final return under the initial conservative rule. Main must return an ordinary scalar.

Result calls must be consumed by a complete handler:

```rf2
handle checked(42)
ok value
 set answer = value
err cause
 set answer = 0
end
```

Both arms are required, in that order, with unique local payload names. Missing, duplicate, reordered and wildcard arms refuse. Arm bindings are immutable and visible only inside their own arm; nested handlers preserve their outer bindings while hiding inner ones after the nested handler. Scalar payload values may deliberately be copied or returned from inside their arm.

Result calls cannot be silently discarded, assigned to a scalar, indexed, accessed through a property or passed as an ordinary argument. This stage has no result locals, result parameters, arbitrary structured payloads, automatic propagation or exceptions. Exhaustiveness covers the two variants, not every numeric error code carried by err. A programmer can still write an inappropriate or empty error branch; the compiler does not prove business recovery.

The native RF2 internal call protocol uses a tag and scalar payload in two registers, then stores the selected payload before compiling arm calls. This is an RF2 protocol, not qualification of a general foreign-function interface.

## Initialization and scope correction

The 0.12 compiler admitted some reads of uninitialized scalar locals. Independent retained tests showed forward-use and false-branch declarations producing different default/optimized outputs. Those observations establish an admission gap, not a defined-output speed or correctness result.

The new compiler checks readiness at local lookup, including optimized paths. Scalar declarations in an if/while/handling block no longer become readable outside that block. Initialize an outer local explicitly before assigning to it inside a branch. Assignment before initialization also refuses.

A further optimizer path initially admitted `let x = x + 1` through in-place lowering. Its readiness guard was corrected and tested through constant, register and coalesced expression cases. Previous candidates and failures remain in local engineering records. Existing historical benchmark receipts are not rewritten.

This tightens source admission. Old programs relying on uninitialized values or block-local names escaping their block require correction; there is no implicit zero-initialization rule for scalars.

## Immutable byte views for text

```rf2
array Bytes(u8, 128)
view Window(Bytes)
```

Inside a function, `let text = Window(data, start, count)` constructs a pointer/count descriptor over the declared nominal byte-array type. It copies no source bytes. The descriptor occupies three local slots including its pointer; backing storage remains owned by the array's live caller/current frame. Creation is function-level only. Views cannot be returned, passed, copied, rebound, assigned fields, indexed for writes or sent to a raw intrinsic.

Admission checks start <= capacity followed by count <= capacity-start, avoiding unsigned-addition overflow. A zero-length view at capacity is valid. Indexing checks against view count, not backing capacity. `.length` is that chosen count. Invalid ranges/accesses use the ordinary status-2 bounds trap; callers wanting a recoverable error must check before construction, as the app does.

Multiple disjoint, overlapping or derived-range views may coexist. After the first is created, all calls and all array element updates are forbidden for the rest of that function. This includes updates or I/O through potentially aliased array parameters and even apparently harmless helper calls. Constructors may read existing views but cannot hide a call in an offset/count expression. The freeze ends only when the function returns. Record/scalar updates and ordinary read expressions remain available.

Fresh owned-array initialization remains permitted because it allocates distinct frame storage; later element updates remain refused.

This conservative rule closes ordinary alias invalidation without effect inference or early borrow release. It is not a flexible lexical borrowing system. Raw systems code and external/concurrent memory mutation remain outside the safety claim.

A view is byte-indexed. It does not establish UTF-8 validity, character-boundary alignment, normalization, grapheme segmentation or logical populated length. The chosen range is checked against capacity. Validate encoding/content separately; the numeric app intentionally accepts only ASCII digits after trimming ASCII space, tab and CR.

## Working application

The package's rf2-number-audit reads stdin or an explicit file, processes newline-separated unsigned numbers, reports malformed/overflowing lines and continues with later valid rows. Its parser uses a read-only view; opening and reading use typed result functions with exhaustive handlers. Owned files close after successful or failed processing; stdin is borrowed. This is explicit cleanup, not automatic resource ownership.

```sh
printf '12\nbad\n30\n' | ./rf2-number-audit
```

It reports two accepted rows, one rejected row, sum 42 and the first error at line two. The populated-line limit is 128 bytes, and the total processed-input limit is 1 MiB. Sum overflow rejects that row rather than wrapping. I/O/limit failures mean partial statistics. [Exact app contract](../examples/number-audit/README.md).

## Independent review and evidence

Two actual agent tasks authored adversarial programs and reviewed the design/source. The parent reran the 158-mode-case agent-authored matrix against the final compiler. A separate 44-case reviewed fixture set is also replayable. The app suite adds 266 checks, and 18 further checks cover multiple views. These counts are finite cases across default and optimized builds, not human peer review, security certification or a whole-compiler proof.

WhatIF's available source heuristic skipped .rf2 files and inspected zero compiler source files. That is recorded as unsupported coverage, not a pass. The actual semantic work ran separately as local native programs, without HTTP traffic, accounts, production mutation or shared compute. [Adversarial receipt](RESULTS-VIEWS-ADVERSARIAL.json), [critic fixtures](RESULTS-VIEWS-CRITIC-VERIFICATION.json), [app receipt](RESULTS-VIEWS-APP-VERIFICATION.json), [multiple views](MULTIPLE-VIEWS-VERIFICATION.json).

Reproduction uses RF2_TEST_COMPILER with tests/standalone/results_views_redteam.py, results_views_critic.py, results_views_app_verify.py and multiple_views_verify.py. Negative-admission cases are not executed. Retain source/binary hashes and original failures. No new speed, token-saving, energy, platform or physical-hardware result is claimed.

## Next gates

Structured/generic result payloads and propagation; validated UTF-8 views with a content-boundary contract; composable read-only calls and shorter view lifetimes; explicit resource ownership; growable storage; and tasks/cancellation remain further implementation work. Each needs its own real app, meaningful failures and independent expectations. One readable language remains the direction; authority and target contracts remain explicit.
