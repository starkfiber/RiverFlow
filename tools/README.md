# Build and measurement tools

These are explicit developer operations. They are not native user runtime dependencies.

## Build

- `build-program.sh`: compile one trusted source into a new directory and apply macOS signing.
- `build-runtime.sh`: concatenate the documented runtime modules, compile and sign into a new directory.
- `build-core.sh`: compose a trusted harness for checked Core lowering.
- `build-trust.py`, `build-auth-vm.py`, `build-wasm.py`: development applications with their own contracts.

Builds never silently replace an existing output. Execution is a separate action.

## Measure

- `benchmark-compiler-dispatch.py`: identical source/default and optimized compile tasks, byte equality and rotated process-inclusive trials. RF2_BASELINE_COMPILER and RF2_TEST_COMPILER select explicit binaries.
- `benchmark-sha-steady.py`: repeated complete hash API calls after warmup; excludes startup and I/O.
- `benchmark-checksum-files.py`: complete file checksum CLI tasks with actual project snapshots.
- `benchmark-mcp.py` and versioned measurement controllers: protocol/application-specific tasks.

Read a controller and its input manifest before running it. Preserve the previous compiler and input hashes. Run correctness checks before timings; never reuse numbers from another target as a current benchmark. Historical defaults and raw receipts remain unchanged.

## Documentation and packaging

`source-inventory.py` records source bytes without pretending GitHub Linguist recognizes RF2. `build-book.py` generates the book and website mirror when requested. `package-trust-candidate.py` and qualification tools apply only to their explicitly versioned package. They do not publish a stable release automatically.
