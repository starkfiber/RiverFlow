# Build and measurement tools

These are explicit developer operations. They are not native user runtime dependencies.

## Build

- `build-program.sh`: compile one trusted source into a new directory and apply macOS signing.
- `build-runtime.sh`: concatenate the documented runtime modules, compile and sign into a new directory.
- `build-core.sh`: compose a trusted harness for checked Core lowering.
- `build-trust.py`, `build-auth-vm.py`, `build-wasm.py`: development applications with their own contracts.

Builds never silently replace an existing output. Execution is a separate action.

- `build-incremental.py`: explicitly compose and compile the native dependency-aware target-cache driver into a new directory. Native runtime use needs no Python.

## Measure

- `benchmark-incremental.py`: direct clean, forced clean and warm reuse tasks with complete output equality and rotated process-inclusive trials.
- `benchmark-compiler-dispatch.py`: identical source/default and optimized compile tasks, byte equality and rotated process-inclusive trials. RF2_BASELINE_COMPILER and RF2_TEST_COMPILER select explicit binaries.
- `benchmark-sha-steady.py`: repeated complete hash API calls after warmup; excludes startup and I/O.
- `benchmark-checksum-files.py`: complete file checksum CLI tasks with actual project snapshots.
- `benchmark-mcp.py` and versioned measurement controllers: protocol/application-specific tasks.

Read a controller and its input manifest before running it. Preserve the previous compiler and input hashes. Run correctness checks before timings; never reuse numbers from another target as a current benchmark. Historical defaults and raw receipts remain unchanged.

## Documentation and packaging

`source-inventory.py` records source bytes without pretending GitHub Linguist recognizes RF2. `build-book.py` generates the book and website mirror when requested. `package-trust-candidate.py` and qualification tools apply only to their explicitly versioned package. They do not publish a stable release automatically.

## Compact image and function-change work

benchmark-compact-builds.py compares retained legacy and compact complete build paths. function-impact.py reads compiler-emitted .functions sidecars and reports changed functions plus affected callers; it never reuses machine code. See examples/function-changes and docs/DEVELOPER-EXAMPLES.md. CPU-time counters and smaller files are not energy measurements.

0.28 developer measurements: `benchmark-function-reuse.py` includes identity, validation, unit I/O and output creation in clean/empty/retained function-cache routes. `benchmark-compiler-store.py` compares empty project caches with one explicitly retained compiler store and reports its initial setup separately. Run sequentially on frozen compiler/builder inputs; publish regressions as well as improvements.
