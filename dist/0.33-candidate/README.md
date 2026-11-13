# RF2 0.33 development candidate

Apple Silicon macOS only; ad-hoc signed, not notarized. Stable downloads unchanged.

Includes native compiler, runtime/MCP, telemetry-summary and value-frequency executables, compiler source, both .flow apps and their shared parser/heapsort/output modules, instructions and MIT licence. Native programs need no Node/npm/Python runtime. Runtime retains0.17 contract/nine bounded tools; compiler development0.33.

Input budget1MiB/65536 unsigned integer values. Summary uses checked u64 sum and lower median. Collections relocate heap allocation with checked local moves, mutable borrows and explicit cleanup retry/partial-release rules. No owner returns, concurrency, arbitrary raw-pointer safety, ESP32/Arduino firmware or new speed claim. See [contracts and final evidence](../../docs/HEAP-COLLECTIONS-0.33.md). Follow normal OS security review; no warning bypass is automated.
