# Incremental target builds: 0.26 source candidate

The native `rf2-build` driver reuses a verified complete target image when its exact build inputs recur. It discovers the transitive module set with the canonical compiler's entry-relative expansion rules. Changes invalidate the affected target; a target with no dependency on the changed file remains reusable.

The reuse unit is a whole executable. The current compiler emits one monolithic Mach-O image, so an affected target still undergoes complete parsing, checking and code generation. Function-level reuse, a relocatable object format and a linker are not implemented by this change.

## Build the driver once

Use a qualified 0.25 native compiler, or rebuild the current canonical compiler from a qualified previous compiler as described in CODEBASE.md. Build into an unused directory:

```sh
python3 tools/build-incremental.py /absolute/path/to/rf2c output/incremental-build
mkdir -p output/programs
mkdir -m 700 .rf2-cache
./output/incremental-build/rf2-build /absolute/path/to/rf2c examples/workload/main.rf2 output/programs/workload-001 .rf2-cache --opt
./output/incremental-build/rf2-build /absolute/path/to/rf2c examples/workload/main.rf2 output/programs/workload-002 .rf2-cache --opt
```

The default `.rf2-cache/` and `output/` paths are ignored by Git; keep any custom cache path outside public source control too.

The second invocation should report a hit if its inputs are unchanged. Each output path must be new. Apply ordinary macOS signing before executing a produced image:

```sh
/usr/bin/codesign -s - output/programs/workload-002
```

Native usage is `rf2-build compiler source new-output private-cache [--opt] [--clean]`. `--clean` bypasses the target-image lookup and performs a complete target compilation; it can still use the verified compiler snapshot. It updates the cache after success. JSON on stdout reports hit/miss, key and dependency count. Compiler diagnostics remain on stderr. The driver does not sign or execute the produced application.

## Invalidation and snapshots

The key binds the builder's composed source identity, actual selected compiler file bytes, options, entry path and every discovered dependency's path, length and content hash. Length-delimited fields distinguish graph shapes. Raw comments and whitespace conservatively invalidate. A moved compiler with identical bytes is equivalent; a compiler byte change is not. No timestamp, file-size-only or historical approval shortcut is used.

Files are captured into bounded native buffers, then copied into a private work directory on a miss. The child compiler reads those copies, including the entry-relative import hierarchy. A controlled native wrapper test edits the original dependency after capture: the first output matches a clean build of the captured inputs, and the next invocation observes the edit. This is a consistent captured input set, not an atomic transaction across a concurrently edited filesystem tree.

The compiler snapshot is stored separately by its image hash and verified again before execution on a miss. A valid executable copy is reused rather than making a new executable inode for every build. Bad bytes, permissions, symlinks and hardlinks trigger replacement from the currently captured compiler bytes. This is qualified for the selected native RF2 compiler; arbitrary external compiler scripts, undeclared plugins or ambient toolchain dependencies are not a supported hermetic-build contract.

## Cache and output failure policy

- The caller supplies an existing cache directory owned by the current UID, with group/other POSIX permission bits excluded. Final-component directory symlinks refuse. ACL policy and ancestor trust are not audited.
- An advisory nonblocking directory lock serializes cooperating builders. A contending build refuses with a retry message. The OS releases the lock when the process closes it or exits; this is not a job queue.
- Entries contain a format tag, expected key, exact image length and image SHA-256. Missing, truncated, mismatched, FIFO or symlink entries rebuild. These hashes detect accidental corruption; an owner who forges both payload and metadata is outside the trust model.
- Cache publication writes an exclusive temporary file, flushes its data and renames it atomically. A partial sibling temporary file cannot become a hit. There is no signed shared-cache protocol or power-loss transaction guarantee.
- Output publication writes a new temporary file beside the requested destination and uses an exclusive hard link. An existing file, directory or symlink is never replaced. Signing an output cannot mutate the separate unsigned cached image.
- Temporary input snapshots do not require durability flushes. Completed build paths remove their work directories. Abrupt termination can leave staging files or work directories; these are never promoted automatically. There is no automatic pruning or unbounded retry loop.

Bounds: 32 source files, import depth below 16, 512 KiB combined and expanded source, and 16 MiB compiler/image files. Current qualification is Apple Silicon macOS with Darwin system calls. Source inputs must be regular files; final-component source/module symlinks and FIFOs refuse. This is trusted local compilation, not a filesystem sandbox or a memory-safety proof. Normal module resolution is not a promise to contain symlinked ancestor directories.

## Verification and measurement

`tests/standalone/incremental_verify.py` uses fresh native processes, independent clean builds and exact unsigned image equality. It covers options and compiler identity, direct/transitive edits, preserved timestamps and sizes, graph changes, an unaffected second target, deletion, syntax errors, cycles, corruption, incomplete entries, symlinks, FIFOs, bounds, lock contention, existing destinations, stored compiler corruption and controlled editing after capture. A generated checksum application executes on UTF-8 input and matches an independent SHA-256 result.

### Measured rebuilds

Twenty-one rotated trials per target and variant, one Mac, warm OS filesystem. Times include process startup, file reading, hashing, compilation or validated reuse, and output publication. Signing and independent output comparisons are outside the timer. Every unsigned result was byte-identical to its direct clean build.

| Real target | Direct clean, ms | Forced target rebuild, ms | Warm reuse, ms | Clean / warm ratio |
| --- | ---: | ---: | ---: | ---: |
| Native compiler | 46.958 | 75.237 | 17.421 | 2.70 |
| Native runtime | 56.733 | 82.390 | 17.477 | 3.25 |
| Modular checksum app | 6.060 | 19.770 | 7.826 | 0.77 |

The checksum hit is slower than direct compilation. The forced-rebuild rows already have a stored compiler snapshot available; they are not first-use cache initialization timings. The builder adds source snapshots, image verification, data flushes and atomic publication that the direct compiler does not all provide. A miss remains a full target rebuild and is slower here. The paired warm-minus-clean intervals exclude zero in the improving direction for the compiler/runtime and in the worsening direction for the checksum app. There is no guarantee of twice the speed for every program.

Earlier local trials retained repeated per-build compiler copies and much higher forced-rebuild costs. Removing redundant snapshot flushes alone did not establish a useful improvement. The final path reuses the verified compiler copy across misses. Those exploratory versions and their failures remain in the local evidence, rather than being substituted for the final measurements. Use the direct compiler when caching overhead is unsuitable for a small target.

A runtime rebuilt through a warm cache passes its native corpus and independent official MCP SDK discovery, result, refusal and recovery checks. The existing nine stable tools and permission boundaries are unchanged. There is no new tool accepting cache paths or arbitrary systems source over MCP.

Set RF2_BUILD_BIN and RF2_TEST_COMPILER to explicit binaries, plus RF2_OLD_COMPILER for a changed-compiler control. Run `python3 tests/standalone/incremental_verify.py`. Use `tools/benchmark-incremental.py` for complete build tasks, with correctness comparisons outside the timer. Developer controllers require their existing local Python/Node installations; native execution does not inherit those requirements.

The WhatIF scenario matrix is executed by a host native-CLI controller. The plugin's HTTP campaign runner is not a native compiler test adapter. Reverse Lab case files retain hashes and failures. REA's attached binary-layout provider refused this ARM64 Mach-O target because its current profile supports Linux x64 only. macOS `otool` confirms ARM64 Mach-O and libSystem linkage; this fallback is not claimed as REA decompilation coverage.

[Verification](INCREMENTAL-VERIFICATION.json) · [complete build measurements](INCREMENTAL-MEASUREMENTS.json) · [build identity and MCP](INCREMENTAL-INTEGRATION.json).

The implementation uses content addressing, dependency invalidation and atomic file publication. It does not establish a new computing principle, Python/Clang feature parity, universal speed, billed model-token savings or measured energy savings. Target-level warm reuse and runtime execution performance answer different questions.

## Next implementation boundaries

A relocatable object format and stable dependency-aware symbol identities are prerequisites for finer compilation units. Semantic fact reuse must carry explicit invalidation rules and independent clean-build equality checks. A managed project command can later own artifact replacement and target scheduling; this driver deliberately retains the compiler's new-output contract.

Darwin ABI source reference: [Apple XNU syscall definitions](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/syscalls.master). Actual syscall behavior is qualified by the local native tests above, not by the table alone.
