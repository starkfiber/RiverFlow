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

0.29 adds `generate-sha40.py`, `benchmark-reuse-edit.py` and bounded `stress-function-reuse.py`. The stress controller has a case cap and deadline, stops on failures and supports PAUSE between cases; no network traffic. Retain actual completed counts and source/controller identities.

## Packed reuse experiment, 0.30

`benchmark-packed-reuse.py` compares an explicitly supplied previous compiler (RF2_OLD_COMPILER) with RF2_TEST_COMPILER clean, retained loose units, empty pack and retained pack. It rotates complete process runs, checks every unsigned image against the previous compiler, and records raw observations. RF2_BENCH_TRIALS defaults to21. Use `tests/standalone/function_pack_verify.py` for adversarial cache controls and RF2_WEB_PACK_TEST=1 with `number_lab_web_verify.py` to execute the packed app through its full HTTP campaign. Do not replace a correctness run with timing.

## Native application comparison, 0.31

`benchmark-text-search.py` takes RF2_SEARCH_BINARY (baseline) and optional RF2_SEARCH_CANDIDATE (candidate). It compiles the retained C libc comparator and runs Python bytes.find as developer comparison routes, with matched supplied inputs and independent JSON oracles. All timings include startup and input/output. Run after correctness qualification, while other owned load jobs are paused. Keep source/build receipts, raw trials and losing cases; do not infer model-token usage or steady-state throughput. RF2_BENCH_TRIALS controls 5..101 rotated trials per route.

`package-heap.py` explicitly packages a qualified compiler, runtime and two collection-app binaries into a new0.33development directory. It verifies signatures, native smoke outputs and creates a file-hash manifest. It neither downloads binaries nor changes the stable release. Follow [the heap contract](../docs/HEAP-COLLECTIONS-0.33.md) and recheck fresh extraction.

`build-embedded.py` builds the native RF2-written ESP32-C3 cross-compiler from reviewed shared frontend/SHA helpers and the independent RV32 backend. `package-embedded.py` packages only supplied native compilers/runtime, project sources and generated firmware; no vendor emulator/toolchain is redistributed. See [ESP32-C3 contracts and hardware limits](../docs/ESP32C3-0.34.md).
