# Private compiler stores: 0.28 source candidate

## What changed

`rf2-build` can retain its checked compiler snapshot separately from each project's target cache. This avoids creating and first executing another byte-identical compiler inode whenever a new project cache starts empty. The option is explicit:

```sh
mkdir -m 700 .rf2-cache .rf2-compilers
/path/to/rf2-build /path/to/rf2c examples/file-checksum.rf2 output/checksum-001 .rf2-cache --opt --compact --compiler-store .rf2-compilers
```

Create the directories first and use an unused output name. The selected compiler and builder must already be qualified for the requested mode. Application images still need normal macOS signing before execution. The compiler store does not hold target results or function bodies.

Omitting `--compiler-store` preserves the default route: compiler snapshots remain in the project's target-cache directory. An explicitly selected store can also name that same directory; the builder recognizes its device and inode and keeps the existing lock instead of attempting to lock itself again.

## Admission, locking and execution

Both directories must already exist, belong to the current user, exclude group and other POSIX permission bits, and have no final-component symlink. The existing nonblocking target-cache lock is retained. A separate store takes a nonblocking exclusive lock held through compiler execution and output publication. Contention refuses rather than waiting indefinitely; retry after the active builder exits. This is cooperative local serialization, not permission to trust a malicious writer with the same UID. ACL policy and ancestor-directory trust are not audited.

The supplied compiler is still read and hashed. Its SHA-256 names the stored compiler snapshot. Before reuse, the builder checks the stored bytes, file mode and link count; corruption, wrong permissions, symlinks or hardlinks cause private replacement before execution. Snapshot creation closes its private temporary file and renames it atomically. The snapshot is reconstructible and does not receive a forced disk flush. A power interruption can require repair on the next run.

For an explicit store, Darwin `F_GETPATH` resolves the already-open directory's absolute path before the child changes into its captured source workspace. The child still compiles captured dependency files. Source changes cannot silently substitute an uncaptured dependency. Compiler bytes, build options, builder identity and captured dependencies remain in the target key; the physical compiler-store location is not a semantic input.

Target cache entries and published outputs retain their existing durable writes and exclusive publication rules. Existing output destinations are never overwritten. No authenticated shared cache, power-loss transaction, cross-user execution service or new MCP effect is introduced.

## Why the first build needed investigation

An instrumented copy of the 0.27 driver separated compiler reading, hashing, dependency capture, snapshot creation, child execution and publication. Across five ordered cold/forced/hit probes on this Mac, the cold median was 234.762 ms and the forced median was 17.558 ms. The interval from the child's pre-exec marker to the parent's completed wait was 221.947 ms cold versus 6.434 ms forced. Compiler snapshot creation itself took 0.405 ms cold; compiler hashing took 0.176 ms and final publication took 0.688 ms.

A separate seven-trial rotated probe copied or APFS-cloned byte-identical compiler images. Copy first execution had a 104.799 ms median versus 5.053 ms for its second execution. Clone first execution had a 106.500 ms median versus 7.311 ms for its second. Cloning did not solve the observed problem and is not part of this implementation.

These instrumented and direct probes locate a first-execution cost; they do not identify a particular macOS security service as its proven cause. The operating-system validation explanation remains an inference. The observations are not directly interchangeable with the earlier uninstrumented end-to-end benchmark. Raw local receipts remain in `artifacts/cold-profile-028/profile.json` and `artifacts/cold-profile-028/clone-probe.json`.

## Executed controls and measurements

`tests/standalone/compiler_store_verify.py` checks separate project caches against fresh clean output bytes, retention of the same checked compiler inode, mode/byte/link repair, directory and lock refusals, ordinary execution and option handling. The test does not create a foreign-UID directory; that owner-check branch is present but is not an executed foreign-owner result.

The original 58-scenario cache suite passed in compact mode and in the legacy image route, first with the qualified 0.27 compiler and again with the final 0.28 compiler/driver. These runs verify the default compatibility route separately from the explicit shared-store controls.

`tools/benchmark-compiler-store.py` compares previous and new empty-project-cache routes with a third route using an already-retained compiler store, across checksum, runtime and compiler targets. It records the one-time store initialization separately. Run it only after the exact release-candidate compiler and builder are frozen, with other timed work stopped:

```sh
RF2_OLD_BUILDER=/path/to/qualified-0.27-builder RF2_BUILD_BIN=/path/to/candidate-builder RF2_TEST_COMPILER=/path/to/candidate-compiler python3 tools/benchmark-compiler-store.py
```

Twenty-one rotated trials on the final compiler and builder produced these median complete-build milliseconds. Every timed target cache started empty.

| Target | Previous empty project | New empty project | New project with retained compiler |
| --- | ---: | ---: | ---: |
| Checksum | 114.273 | 113.697 | 12.297 |
| Runtime | 135.729 | 134.592 | 26.418 |
| Compiler | 139.958 | 140.690 | 30.325 |

The separately measured first compiler-store setup took 148.010 ms. The retained-store route improved the observed previous empty-project medians by 9.29x, 5.14x, 4.62x respectively. A newly empty compiler store has no comparable established improvement; the new default route remains close to the previous route.

[All trials](COMPILER-STORE-MEASUREMENTS.json) · [20 store controls](COMPILER-STORE-VERIFICATION.json) · [Retained profile and rejected clone probe](COLD-PROFILE-0.28.json). Even a successful retained-store result cannot establish a faster first-ever compiler launch. Deleting the compiler store, changing compiler bytes or repairing a corrupt snapshot can require another first execution. This is an explicit developer workflow optimization, not application-runtime acceleration, electrical-energy measurement, AI-token savings, general Python/C compatibility or cross-platform qualification.
