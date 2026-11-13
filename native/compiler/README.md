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

## Optional image and change-evidence modes

--compact separates initialized file bytes from zero-filled VM reservations. Default output retains the prior format. --functions writes a bounded diagnostic sidecar with token fingerprints, code ranges, relocation records and direct-call edges. These are not relocatable objects or reusable function bodies. Read docs/COMPACT-IMAGES-0.27.md and use the clean-build and native loader gates.

## Opt-in scalar function reuse, 0.28

`--reuse-cache existing-private-directory` admits only single-return scalar arithmetic helpers and emits a reuse report. Templates are captured before resolution, current exit fixups are rebuilt, and keys bind compiler file identity, options, declaration context and body tokens. All other source uses normal generation; diagnostic map mode deliberately disables reuse. The measured route is currently slower than clean compilation. Read [the contract and limits](../../docs/FUNCTION-REUSE-0.28.md) before use.

0.29: guarded hardware hashing, one-pass context fingerprints and memoized linear-scalar eligibility reduce reuse overhead. RF2FN002 binds local count and metadata/code integrity; full validation remains required on misses. See [the current contract and mixed measurements](../../docs/FUNCTION-REUSE-0.29.md).

## Development0.33 heap lowering

[Owned u64 collections](../../docs/HEAP-COLLECTIONS-0.33.md) lower through compiler-owned RF2 helper text, with source-origin admission guards and no external runtime file dependency. Preserve local move/borrow restrictions, pending-map retirement, partial release and secondary-error semantics. The [readable helper snapshot](../../docs/HEAP-RUNTIME-0.33.md) is derived; compiler.rf2 remains authoritative. `.flow` imports do not add an embedded backend.
