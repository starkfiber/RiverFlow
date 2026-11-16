# Native diagnostics and function-table qualification, source candidate 0.50

This layer adds opt-in machine-readable compiler errors and repair guidance to the0.49 candidate. It does not expand bounded Core/MCP effects or automatically repair a program. A separate explicit inventory expands native Systems compiler function capacity from256 to512 so the growing compiler and SDK can be compiled. Local slots remain256 per function, record types32, module count32 and all other source/token/frame budgets retain their prior values.

## Native error interface

```
rf2c main.flow new-program --compact --diagnostic-json
rf2c --check main.flow --diagnostic-json
```

Compile-time `die` failures have exit1, no successful output and exactly one physical JSON line on stderr with schema `rf2.diagnostic.v1`. Successful builds retain ordinary success output and identical emitted program bytes with or without the flag. Signals, kernel termination and runtime errors in the compiled application are outside this error interface. The flag does not make successful compilation stdout JSON.

The object contains `severity`, stable `code`, original `message`, optional actionable `hint` (empty string if no precise hint applies), `stringEncoding` and `location`. Narrow codes currently cover unknown locals/functions/fields, function or builtin arity, nominal argument mismatch, signature types, lifetime readiness and missing source/import files. Other errors remain `RF2E_COMPILE`; they are not inferred into an inaccurate category. These categories do not promise a source-language migration or complete schema validator.

`location` is either null or a `path`, positive `line` and `byteColumn`, and `origin` label. Original module mappings use `source`; unmapped cursor locations distinguish `entry`, `expanded` or `generated`. The cursor can follow the offending token. Byte columns are not grapheme, Unicode scalar or display columns. Admission/option/import failures before source parsing return null instead of inventing a source position. Source excerpts are not emitted.

JSON strings use **escaped bytes**: printable ASCII except quotes/backslashes is written directly; all other source-path bytes are represented as `\u00xx`. Decode JSON and encode the resulting code points as Latin-1 to recover the original path bytes, then interpret those bytes as UTF-8 only when appropriate for the filesystem. This makes even unusual non-UTF-8/control-character filenames valid single-line JSON. Do not use the decoded string as a Unicode path without this byte recovery. Strings are bounded (messages/hints512bytes, each path component1024bytes). This is terminal/JSON safety, not secret redaction or an authentication mechanism.

Without the flag the original human error message and source cursor remain, followed by a targeted hint for the same supported categories. Unknown symbols are not replaced with guessed names or unchecked fixes.

## Reproduction

`prepare.py` layers `apply_bounds` and `apply` over the exact0.49 preparation. Its public functions also compose with the SDK layer; diagnostics must run after the SDK layer to use its package path mapping. No default library, current-directory discovery, network dependency or implicit source execution is introduced.

The previous0.49 compiler has254functions and cannot compile the larger diagnostics/SDK source under its256function limit. Build the bounded bridge from unchanged0.49 source plus the inventoried table expansion:

```
python3 experiments/diagnostics-050/bootstrap.py PATH-TO-049-NATIVE-COMPILER NEW-BRIDGE
python3 experiments/diagnostics-050/prepare.py NEW-CANDIDATE
NEW-BRIDGE/program NEW-CANDIDATE/compiler.flow NEW-CANDIDATE/program --opt --compact
codesign -s - NEW-CANDIDATE/program
RF2_DIAGNOSTIC_COMPILER=NEW-CANDIDATE/program \
RF2_DIAGNOSTIC_SOURCE=NEW-CANDIDATE/compiler.flow \
python3 tests/standalone/diagnostics_050_verify.py
```

Python is development source preparation/test tooling. The resulting compiler, its diagnostics and the compiled application run natively without it. Signing remains macOS ad-hoc signing, not publisher notarization.

The expansion changes18 specifically named per-function buffers, preserving their per-function strides, and the function-table guard. A global replacement of256 would incorrectly alter local slots and unrelated limits; no such replacement is used. Tests inspect every expanded table size; execute function index511 with scalar/record/4096-array/resource cleanup/result state, compile high-index function reuse, compare cold/warm images against clean emission, and reject function513 before writing an image in both modes. Total pack/source/token/code budgets still apply and can refuse a large program before it reaches512functions.

## Retained failures and boundaries

The initial diagnostics source failed against0.49 with `function bound`; this motivated explicit table qualification rather than bypassing its guard. An initial test controller compared unsigned cache images against an already signed clean image, producing a false failure. The corrected oracle saves clean emitted bytes before signing; the failed receipt is retained. A standalone optional-flag guard initially used eager Boolean operands and read a nonexistent argument during ordinary `--check`; a direct native reproduction exited with signal11. Sequential argument guards fix it, and both ordinary and JSON check forms are now explicit controls. A read-only reviewer caught a package JSON-path prefix mismatch during integration; the shared path helper corrects the actual native mapping. No prior failure was relabelled as a pass.

The parent qualification must compose this layer with SDK source, run the existing native regressions/MCP checks and verify exact signed self-generation before calling a combined candidate qualified. Standalone diagnostics results do not establish complete platform correctness, arbitrary memory safety, AI token savings or an independent human usability study. Stable/public downloads remain unchanged by source preparation.
