# Native incremental build driver

`incremental.rf2` implements an explicitly invoked local target cache. Build it with `tools/build-incremental.py`, a qualified native compiler and the canonical RF2 module-expansion and SHA sources. The generation receipt records every input and the final binary hash. Python is a developer build controller; the resulting executable runs with no Python, Node or npm runtime.

The driver snapshots each target's raw transitive source set, computes a content key, and either verifies a stored complete image or runs the selected compiler on private snapshots. A changed target is fully compiled. It does not reuse individual functions, object files, ASTs or semantic facts.

The cache key includes the builder-source identity, selected compiler image bytes, optimization option, entry path and length-delimited dependency paths, lengths and SHA-256 values. It never trusts file timestamps. The native compiler is unchanged. Cache and filesystem effects are CLI-only and are not added to bounded MCP.

Read [the full contract and tests](../../docs/INCREMENTAL-BUILDS.md) before use. Cache storage is private, serialized and trusted to its owner. There is no authenticated shared-cache or hostile same-UID writer guarantee.

With a qualified 0.27 compiler, --compact selects the smaller image layout and is bound into the cache key. Build the driver itself with the same optional flag through tools/build-incremental.py. Current default behavior remains compatible. Function-map sidecars are separate developer evidence and are not admitted to the target cache.
