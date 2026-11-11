# Standalone RiverFlow 0.4

The experimental standalone executable is for **Apple Silicon macOS 14 or newer**. It runs without Node, npm, Python, C++ or a compiler installed by the user. It uses the normal macOS loader, libSystem load command, and OS read/write/open/close/exit interfaces. It is not independent of its operating system.

## Compact, explicit computation

Save this as `sum.rf2`:

```text
rf2 v1 checked
sum input
```

```sh
./rf2 run sum.rf2 '[1,2,3,4,5]'
./rf2 check sum.rf2
./rf2 expand sum.rf2
./rf2 status
./rf2 mcp
```

`run` accepts an optional final count to select a prefix. Input is JSON containing up to 65,536 unsigned 32-bit integers; integer decimal and exponent representations are accepted when their exact value is in range. `checked` rejects overflow. `wrap` uses modulo 2^32 arithmetic. Zero input returns zero.

The exact Compact V1 vocabulary is `rf2 v1 checked|wrap` followed by `sum|squares|bits|nonzero input`. Whitespace separates tokens. Extra words, effects, comments, unknown profiles and embedded zero bytes reject. This is controlled syntax, not unrestricted English or a complete application-generation service.

`expand` produces the full `RF2_U32_CORE_V0` source corresponding to the chosen computation. `check` produces a compact plan; it does not pretend to compile every Core program. The standalone refuses general Core source and machine-profile source at this boundary. The older JavaScript implementation retains helpers, arbitrary admitted statements, C emission, batch execution and the public repository catalog; those are not advertised as native features.

## Actual implementation chain

```text
native/rf2.rf2 (RF2_SYSTEM_A64_V1 systems implementation)
    -> bootstrap/seed.py (trusted build-time seed)
    -> directly encoded AArch64 instructions + Mach-O image
    -> macOS ad-hoc code signature
    -> standalone rf2 executable
    -> Compact V1 plan -> native reduction -> result or refusal
```

The runtime, compact front end, UTF-8/JSON handling, decimal conversion, bounds checks and MCP dispatch are written in RiverFlow's explicitly separate systems profile. The seed encodes the instructions and executable layout directly. It does not invoke a C/C++ compiler, assembler, linker, Node or npm. Python and the macOS code-signing utility are build-time requirements only.

**This is not self-hosting.** The seed compiler is Python, not RiverFlow. Machine-profile arithmetic is modular unsigned 64-bit; it exposes pointers and OS calls to trusted implementation source. It is not the u32 Core profile and is never available to MCP callers. Its source is trusted, not a sandbox for arbitrary uploaded code. Hardware instruction semantics and macOS remain external contracts.

The direct native routines currently implement four known reductions. There is no per-request model inference, general native optimizer or arbitrary Core-to-machine backend. Matching observable results does not mean all old toolchain capabilities have migrated.

## Rebuild and verify

On an Apple Silicon Mac with Python 3 and the macOS code-signing utility:

```sh
python3 bootstrap/seed.py native/rf2.rf2 output/bin/rf2
./output/bin/rf2 run examples/compact/sum.rf2 '[1,2,3]'
```

Development comparisons additionally use Node 22 to run the retained reference, never the executable itself:

```sh
python3 tests/standalone/verify.py
```

`docs/STANDALONE-VERIFICATION.json` records the actual results and source/binary fingerprints. The seed source and native source should be reviewed together. No speed, energy, phone or self-hosting result follows from removing a runtime dependency.

## Native MCP

Register the executable directly:

```sh
codex mcp add rf2-native -- /absolute/path/to/rf2 mcp
```

The plugin launcher now selects an explicit `RF2_BIN` or the project-owned `output/bin/rf2`. It refuses to fall back silently to Node or build code on startup. A downloaded source checkout must be built or supplied with a compatible executable first. Configure only one RF2 server per client.

Tools: `rf2_status`, `rf2_check`, `rf2_run`. stdio uses newline-delimited JSON-RPC. Protocol baseline is 2024-11-05. Output is structured JSON plus a readable text result. Request size is at most 1 MiB; parsing depth is at most 32, object fields at most 64 and tokens at most 70,000. Oversized requests are drained before accepting the next request. Duplicate object keys and malformed UTF-8 reject. The service has no network, arbitrary path, subprocess or deployment tools. Local CLI file reads are explicit and separate.

Reference: https://modelcontextprotocol.io/specification/2024-11-05/basic/transports and https://modelcontextprotocol.io/specification/2024-11-05/server/tools.

## Compatibility and next gates

This milestone replaces the runtime dependency for the **documented compact subset**, not the full historical stack. Next gates are independent machine-encoder review, broader platform backends, migration of general Core semantics, a native compiler for the systems profile, and a bootstrapped fixed-point reproduction. Application capabilities require their own versioned APIs, effects and tests.

A reduction named `bits` is not cryptographic authentication. Tests are evidence about the cases executed, not formal proof or a security audit. No phone, RU'OS recovery state, wireless interface or thesis hypothesis is changed by this release. No token-saving ratio has been measured. Count full task context and failures when testing the token-economy hypothesis.

The initial static Mach-O trial was refused by macOS policy; no policy was disabled. The working image uses the normal dyld load path, required UUID, and ad-hoc signature. No notarization or Developer ID signing is asserted.
