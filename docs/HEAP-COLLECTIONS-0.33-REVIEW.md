# Heap collection independent review

The frozen v4 compiler passed 78 independent controls, split into 39 default and 39 optimized controls on this Mac. These are finite native ownership, data and failure checks. They do not establish whole-language memory safety, speed superiority or additional machine-target support.

## Exact evidence

- Controller: `tests/standalone/heap_ownership_redteam_verify.py`.
- Final report: `artifacts/sprint-033/heap-redteam-1794579344284614000/report.json`.
- Final log: `artifacts/sprint-033/heap-redteam-v4-final.log`.
- Frozen compiler: `output/rf2c-033-heap-v4`.
- Compiler SHA-256: `c1aa22e3303d849691467b3ba5dacfdc651570004afd2e70582ce5dac60e5e37`.
- Compiler source SHA-256 supplied by the implementation agent: `3d2e7d65cc545c116b9c75aaabb10b0906f5b3cb7cdf9a3c29fa5c3ab51665d7`.
- Controller SHA-256: `48a2af528c950d746cb984409338d36516ec08b2957a78cc45b270c7a747cd90`.

Reproduction from the repository root:

```sh
RF2_TEST_COMPILER=output/rf2c-033-heap-v4 python3 tests/standalone/heap_ownership_redteam_verify.py
```

The developer controller uses Python to generate and check native programs. The compiled programs execute with `PATH=/nonexistent`. Independent instruction oracles use the system assembler. This is native local testing using WhatIF boundary, invariant and replay discipline; built-in WhatIF web-engine coverage is not claimed. No external service, Git write, shared Memory/KHC, Prime or hardware action was performed by this review.

## What passed

The test campaign checks empty owners; populated and empty local moves; multiple actual growths through 128 elements; exact high u64 values after copying; reserve without shrink; maximum-capacity push refusal; maximum-u64 request and index refusal; and clear retaining capacity while resetting length. Invalid requests preserve the observed active length and data.

Typed helper borrows mutate the original descriptor. Two sequential mutable borrows may intentionally alias. Reentrant scalar arguments grow, clear and repopulate the same collection before the outer push or set completes; the outer operation must reload its descriptor and use the resulting state. The independent data checks pass in both modes.

Compiler refusals cover scalar owner copy, owner rebinding, duplicate move, source use after move, owner return through a scalar result, direct pointer extraction, raw pointer coercion, nested branch/loop owner declarations, borrowed-owner release and move, and attempts to define or call reserved collection runtime helpers. A released collection rejects subsequent operations; a property used on a later loop iteration reaches a controlled bounds trap rather than touching a retired mapping.

The campaign observes mapping lifetime while the process is still running. A test-only helper patch exposes the owned descriptor's active address solely inside owned test binaries. A same-protection `mprotect` probe distinguishes the live mapping from the old retired mapping after growth, and distinguishes the live mapping from the released mapping. Another test returns from a callee after moving its owner and confirms that its mapping is already retired before the caller exits. Unpatched controls deliberately return 201, proving that the instrumentation is required. Independent assembly confirms the patch bytes, and every patch records offsets, original/replacement bytes and file hashes.

Controlled failure checks inject an initial mapping failure, old-map retirement failure, explicit release failure, and consecutive old-map retirement plus pending-map cleanup failures. The tests check the handled error, unchanged active data/metadata for the growth failures, retention of cleanup responsibility, and successful retry. Permanent cleanup failure verifies `65536 + 12` after an otherwise successful return and preservation of a primary error 77. Each injected program has an unpatched control with the expected distinct outcome.

## Real defect found and corrected

The v3 automatic-cleanup path intended to copy errno from x1 to x0 but emitted instruction `0xaa000400`. Under the permanent injected unmap failure, the returned cause was 65539 instead of 65548. An independent assembler confirmed `MOV x0,x1` as `0xaa0103e0`. The implementation agent applied that single instruction correction in v4. Both default and optimized final tests now report 65548 and preserve primary error 77.

The original failing evidence remains in `artifacts/sprint-033/CLEANUP-ERROR-DEFECT.json`; its source, patched binary, injection offset and hashes are preserved. This was a compiler defect, not a benchmark or documentation-only correction.

## Test-oracle corrections retained

The first mapping-lifetime oracle used `mincore`, which returned success even after unmapping on this Mac. A separate C program reproduced that behavior. It was replaced with a same-protection `mprotect` query; a separate C oracle confirmed success for a live mapping and errno 12 after unmapping. The unsuccessful earlier probe is not counted as a compiler defect or successful lifetime test. Reference files are `artifacts/sprint-033/mincore-oracle.c` and `artifacts/sprint-033/mapping-presence-oracle.c`.

The initial fault locator assumed direct emitted syscall pairs. The actual runtime helpers use the generic syscall wrapper. The final injector scopes each site to a named runtime function, verifies the expected site count and errno-conversion instructions, then replaces the complete wrapper sequence. Injected calls are allowed only where the runtime frame saves the link register. Early locator failures remain historical test-controller failures, not product defects.

## Contract limits and unresolved work

This is a bounded relocating collection of u64 values with function-local owners and synchronous mutable borrows. It is not a general allocator or a Rust-style exclusive-borrow system. Owner return/transfer between functions, concurrent sharing, arbitrary element types, unrestricted pointer interactions and allocator stress across machines are outside this review.

Growth failure preserves the active collection, but explicit release can partially succeed: it attempts active and pending mappings separately. If the active mapping is released before pending cleanup fails, the prior contents are no longer promised to be available. The descriptor retains remaining owned maps for retry. Do not state that every failed release preserves all data. At function exit, persistent operating-system unmap failure can leave a mapping until process termination; the test checks the reported error, not a universal no-leaks guarantee.

Fault tests patch only owned generated binaries and model canonical negative errno wrapper results. They do not exhaust real memory, create genuine kernel OOM, or prove handling of arbitrary operating-system corruption. Raw pointer/syscall interference can bypass the collection contract and is explicitly excluded. The final receipt links each controlled fault to its original and patched binary identity.

Existing byte vectors, stack-frame limits, app behavior and the nine bounded MCP effects are separate regression contracts tested by the other agents. This independent review did not modify those implementations or claim its own full MCP qualification.
