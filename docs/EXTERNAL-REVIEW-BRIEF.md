# RF2 external review brief

## Implemented 0.17 update

The native 0.17 increment implements reservation-backed byte vectors and small record-valued success results. Its contract and precise limits are in [storage/results](STORAGE-RESULTS.md), with [release qualification](RELEASE-0.17-VERIFICATION.json). The retained loop reentry use-after-release case was corrected with runtime lifetime guards. Controlled native fault injections are not actual OS OOM measurements. This update does not rerun competitor builds or turn the original 0.16 source comparison into a new parity assessment. Earlier candidate proposals below remain explicitly historical/planning material.


This brief is ready to give another reviewer. It does not send repository contents to another provider. The owner should choose the destination and review any private paths or unpublished materials first. The public software repository is the starting scope; private thesis papers, participant records, credentials, devices and infrastructure are excluded.

The baseline studied for the accompanying [second opinion](SECOND-OPINION-ROADMAP.md) is RF2 0.16, commit `83bd22eb3e82f3e616354bd6f8cc5edbafd265b0`. If reviewing a later release, record its exact source and binary identity, then treat the new feature contracts and receipts as claims to reproduce. Do not silently combine commits or label working-tree candidates as released.

## Copyable reviewer prompt

```text
Act as an independent language/toolchain reviewer. Review the public repository
https://github.com/starkfiber/RiverFlow at an explicitly recorded commit/tag.
Start by recording the revision, dirty state, target host and native binary hashes.
Do not assume that README claims, prior AI reviews or test counts are correct.
Do not invent test runs or claim that your review establishes universal safety.

Goal: find the most consequential correctness, ownership, representation,
resource-lifetime, data-model, tool-boundary and usability gaps, then propose a
prioritized plan that can make RF2 useful for broader complete applications.

Scope:
- Read native/compiler/compiler.rf2, native/rf2.rf2 and referenced modules.
- Read docs/CAPABILITY-MAP.md, the current feature contracts and release receipts.
- Inspect tests/standalone and representative real app sources.
- Separate bounded Core/MCP from trusted systems compilation.
- Keep existing raw-memory, fatal-path and platform limits explicit.
- Do not attack external services, use devices, write disks, publish changes,
  install unknown software, send secrets or run unreviewed repository scripts.
- Use reviewed isolated local programming fixtures. No company data is needed.

Compare architectural responsibilities, not marketing labels:
1. CPython: parsing/compilation/interpreter, object and storage model, libraries.
2. OpenJDK: javac, VM/runtime, collections, error/resource model and tooling.
3. Clang/LLVM plus libc++: front end, typed representation, optimization, backend,
   runtime/library, ABI/linking and target/tooling responsibilities.
C++ is not one implementation repository. Pin the primary upstream revisions.
Do not infer user dependencies from a compiler's implementation language.

For each significant finding return:
- ID, severity and exact source locator.
- Classification: reproduced defect, unsupported feature, design limitation,
  unverified lead or inconclusive result.
- Contract/invariant and why it matters to an actual application.
- Minimal source/input and exact reproduction command with explicit outputs.
- Expected result derived independently, observed result and retained evidence.
- Scope: compiler mode, target, revision, and any unsafe/raw operation used.
- Smallest proposed correction, compatibility impact and regression test.
Do not weaken an oracle to get a pass. Do not call a requested feature an upstream
bug unless it contradicts the named contract.

Specific gates for growable storage and structured results:
- Allocation/growth overflow; empty/full/maximum inputs; forced allocation failure.
- Old data and metadata preserved after failure; no forgotten live allocations.
- Release, use after release, aliasing, view invalidation and repeated lifetimes.
- Record payload layout, field order, type identity and both result variants.
- Returned payload outlives callee; return registers or hidden result storage follow the declared ABI across calls/cleanup.
- Exhaustive handlers and payload scope; cleanup does not corrupt results.
- Default and optimized output equality, compiler self-reproduction and MCP limits.

Run supported tests only after inspecting their effects. A command must have
actually run before you report it. Record refusals and unsuccessful attempts.
Ask for missing access or evidence without fabricating a result. Private native
app installation, public publication, paid APIs and real workloads need separate
owner authorization.

Deliver:
A. A concise independent assessment and five highest-priority findings/gaps.
B. Reproducible findings with retained fixtures and exact evidence paths.
C. A capability matrix: implemented/limited/unsupported/unverified.
D. A dependency-ordered roadmap with acceptance gates and useful real apps.
E. A comparison experiment design; no speed/token/energy claim without measurements.
F. Outstanding unknowns and the next decisive test for each.
Do not give a single percentage implying parity with Python, Java or C++.
```

## Quick evidence checklist

| Review area | Minimum decisive evidence |
| --- | --- |
| Compiler admission | Negative source refuses before output creation; malformed/type/arity/scope cases |
| Semantic correctness | Independent expected full output, not just an 8-bit process return; both compiler modes |
| Growable allocation | Multiple real growth events; exact contents; deterministic failure preserving state; cleanup of every allocation |
| Structured outcomes | Exercise declared scalar/record variants and reject unsupported payloads; nested calls/handlers; nominal-type and expired-lifetime refusals |
| Ownership | In-process resource validity/reuse, primary/cleanup error precedence, no copied/escaped owner |
| Source/build identity | Pinned commit, source/binary hashes, clean package, repeatable compiler bootstrap |
| MCP | Official client discovery/recovery, exact tool schemas/effects, no raw systems execution admitted |
| Target support | Built and exercised artifact on the actual target; host results are not phone/boot qualification |
| Performance | Same job/semantics, pinned toolchains, rotated trials, correctness and retained failures/slower results |
| AI assistance | Actual complete-task usage/cost and correctness receipts, not token estimates or assumed model intelligence |

The RF2 0.16 documentation records real fixed-bound native work, scalar results, owned files and a single qualified native target. Later growable storage or structured results must be evaluated from their own actual source and receipts. A comparison reviewer is free to recommend a different design; the required output is evidence and a testable decision, not praise or an assertion that all programming is solved.

## Additional prompt for the proposed 0.17 strategy

This is planning-only until a final candidate and receipts are supplied. Append the following to the reviewer prompt when those artifacts are ready:

```text
The proposed growable byte vector uses a fixed virtual reservation up to a
configured maximum of 1 MiB. It starts PROT_NONE; reserve grants a readable/writable
prefix and then commits logical capacity. Append may grow that capacity
geometrically. Ordinary cleanup unmaps the full reservation. Evaluate it as a
bounded growable vector, not as a relocating allocator or an unlimited heap.

Check page-size/granularity assumptions, logical length versus capacity, growth
arithmetic and commit order. Prove existing data/metadata survives an injected
reserve failure. A stable address does not waive alias/view mutation restrictions.
Check repeated lifetimes and cleanup of the full reservation.

The proposed structured ok payload is a nominal record with at most four scalar
fields, returned through private RF2 x0 tag/x1..x4 payload registers. Err remains
scalar. Typed ok handlers copy values into the caller frame and cannot pass the
payload as a mutable helper argument. Check field evaluation order, nested calls,
full-width values, cleanup preservation of every register, caller lifetime,
wrong-type/count/annotation refusals and arm scope. Do not call this a general C
ABI, nested/generic result model or full exception system.

The deterministic mmap/mprotect failure fixture patches an exact native syscall
sequence to return a selected errno with Darwin carry set. Verify original and
patched hashes, patch offsets, expected old words and match counts. State clearly
that this injects an error return rather than causing real kernel OOM or memory
pressure. Separate an executed error-handling branch from observed OS failure.
Do not claim a relocating-resize test passed when the chosen design does not
relocate at all.

Keep this overlay's architectural inference separate from actual test results.
If a supplied receipt cannot be reproduced, report the exact discrepancy and
next decisive test; do not silently update it to agree with the implementation.
```
