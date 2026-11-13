# Native RF2 compiler

`compiler.rf2` is the canonical compiler source. It emits ARM64 Mach-O executables directly. This is trusted local compilation, not an MCP execution endpoint.

## Reading order

| Functions / area | Responsibility |
| --- | --- |
| `state`, `token`, `add_token`, `tmatch` | Bounded compiler state and token storage |
| `intrinsic_flags` | Shared intrinsic policy and length-filtered exact name matching |
| `scan_record`, function scanning, local type/readiness helpers | Declarations, nominal types, initialization and ownership rules |
| `mark_call`, `mapped_local`, `access_local` | Conservative call classification and register locals |
| `expression`, `invoke`, `arguments` | Checked expression/call lowering and private argument/result ABI |
| `emit_*`, labels and fixups | ARM64 instructions and control flow |
| final image writers / `main` | Explicit output admission and Mach-O assembly |

The catalogue flags have separate meanings: reserved arithmetic name, inline leaf operation and raw scalar argument ABI. Sharing a catalogue does not mean these properties are interchangeable. VM/platform calls, owned operations and live-view rules keep their existing dedicated checks.

## Rebuild acceptance

Compile this source with the prior qualified native compiler, sign the result, then compile it again. Fixed-point output and independent reference agreement are required. `tests/standalone/compiler_verify.py` also builds and checks the native runtime and official MCP tools. Run semantic ABI, memory and digest checks after intrinsic changes.

No broad argument-register lowering is enabled by the catalogue refactor. The failed earlier experiment stays excluded. Raw pointer operations retain caller obligations; an inline operation is not automatically memory-safe.
