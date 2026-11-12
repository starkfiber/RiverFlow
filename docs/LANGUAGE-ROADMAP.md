# RF2 language direction

RF2 is being developed as a readable language spanning checked computation and explicit systems code. The invoice editor is an integration test of that foundation, not the limit of the language.

| Layer | Executed now | Next qualification gate |
| --- | --- | --- |
| Core | Checked/wrapping u32, helpers, loops, supplied-array reads | Broader structured values with exact semantics |
| Native compiler | Self-reproducing bounded ARM64 compiler | Modules/imports, diagnostics, source mapping |
| Systems | Buffers, memory, files, process and socket wrappers | Owned strings, structured errors and resource lifetimes |
| Platform | Darwin syscall and fork ABI | Explicit FFI and multi-register return contracts |
| Applications | CSV, checked plans, documents, PDF, local forms | Reusable UI/document libraries and richer schemas |
| AI interface | Nine effect-bounded MCP tools | Measured complete tasks, versioned capability discovery |
| Targets | macOS ARM64 | Another architecture with differential and ABI tests |

Each capability requires executable cases, refusals and reproducible receipts. Compare with simpler baselines and preserve failed trials. Compact source is not a token-saving result. Self-hosting does not replace code review, memory safety analysis or portability work. No claim is made that RF2 already replaces every Python/C/C++ library, executes every machine architecture or controls physical transistor design.
