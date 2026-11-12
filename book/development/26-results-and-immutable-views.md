# 26. A result that must be handled

RF2 began with a practical aim: one readable language connecting human or AI intent to inspectable native execution. A program's failure path belongs in that agreement. Release 0.13 makes two parts more explicit: how a function reports a result, and how a helper reads a window of bytes without changing its owner.

## Declare the alternatives

```rf2
result Number(u64, u64)
fn checked(n): Number
 if n == 0
  return err(1)
 end
 return ok(n)
end
```

This is a nominal type with two variants. The initial payloads are unsigned machine words. The function must explicitly return ok or err and end with a root-level return. It cannot silently fall through and manufacture a successful zero. This is a conservative syntactic rule, not complete control-flow analysis.

At the call site, handle requires both arms in fixed order. Each arm has an immutable payload name, scoped to that arm. An ordinary scalar assignment or discarded do statement cannot hide the result. Indexing or reading a property cannot turn its tag into a value.

Exhaustiveness means both variants appear. It does not prove that an error branch does useful recovery or distinguish every numeric error carried by err. Structured payloads, generic result values and automatic propagation remain further work. The current facility is a checked native function protocol, not an exception system.

## Close an old admission gap

Independent programs found that the earlier compiler admitted scalar reads before initialization, including names declared only in a false branch. Default and optimized executions could then produce different outputs. Those values were not a meaningful benchmark result.

The correction checks readiness and scope through the ordinary and optimized paths. One in-place path initially escaped the new check: a self-referential declaration could update an uninitialized register. That case was retained, corrected and tested again. A block-local declaration is now unavailable after its block; initialize an outer local before assigning to it conditionally.

This matters for result handling too. A success payload must not become readable from the error arm, or survive by name after the handler. A compiler feature is incomplete if its fast path ignores the same rule its ordinary path enforces.

## Read through an immutable window

A view declares which byte-array type it can borrow. Its constructor selects a start and count without copying the underlying bytes. Admission uses subtraction after checking the start, avoiding unsigned addition overflow. Reads check the view length rather than the owner's full capacity. An empty window at the end is valid.

Descriptors remain in the current function's frame. They cannot be returned, passed, copied or rebound. Several overlapping windows can coexist, but after the first view is created the function may perform no calls or array element updates. That includes mutation through another parameter that might alias the owner. The freeze ends when the function returns.

This deliberately conservative rule avoids pretending that a general borrow checker already exists. The caller can perform I/O, call the read-only parser, then resume mutation after that parser returns. More composable read-only calls and shorter borrow lifetimes need additional analysis.

Byte safety is not a Unicode promise. A chosen window may split an encoded character or include unused initialized capacity. Encoding, logical content length and character boundaries need their own validation. These views are suitable for byte-based text parsers; they are not normalized strings.

## Use both in a real document task

The number-audit application reads rows of unsigned decimal numbers. Its parser creates an immutable byte view and returns a typed success or error. Its caller must handle both. A malformed row is recorded, and later valid rows still contribute to a checked sum. Oversized rows, numeric overflow and accumulated-sum overflow have stated outcomes.

File opening and input processing also use result-returning functions. The app closes an owned descriptor after processing and leaves borrowed stdin open. Input limits and I/O failures identify partial statistics. None of this makes cleanup automatic across arbitrary programs.

The example input 12, bad, 30 on separate lines yields two accepted rows, one rejection and sum 42. These are programming fixtures, not a workplace or participant study. Randomized tests compare the complete output with independent integer calculations, including later recovery after errors.

## Preserve the uncomfortable evidence

Two actual agent tasks authored programs and reviewed the source. The parent reran their cases against the final binary. Separate suites check missing arms, result coercion, binding scope, aliases, view overflow and frame exhaustion. The original initialization admissions and the later optimizer mistake remain in the engineering record.

WhatIF's source heuristic did not support RF2 files and inspected none. That is an unsupported coverage result. Native program checks supplied separate executed evidence; no HTTP campaign or universal security pass is claimed. AI reviewers are not human peer reviewers.

The next work is structured result payloads, validated text views, composable immutable calls, owned resources, growable storage and task semantics. Each must reach the same standard: a clear contract, working programs, independent expected results and preserved failures. No new speed or token-saving conclusion follows from this release.

Specification and reproduction: docs/RESULTS-VIEWS.md. Application: examples/number-audit. Verification receipts and reviewed fixtures are linked from that contract.
