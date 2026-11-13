# RF2 0.32 development candidate

Apple Silicon macOS only; ad-hoc signed, not notarized. Stable downloads unchanged.

Includes native compiler, runtime/MCP, text-search and log-scan executables, compiler source, both application sources and their single shared library, worked instructions and MIT licence. Native programs need no Node/npm/Python runtime. Runtime retains0.17 contract/nine bounded tools; compiler is development0.32.

Query budget4096bytes, stdin1MiB. New typed arrays have explicit per-type and aggregate-frame budgets; this is not an unbounded heap, concurrency or full-language safety guarantee. See [contracts and evidence](../../docs/STRUCTURED-STORAGE-0.32.md). Follow normal OS security review; no warning bypass is automated.
