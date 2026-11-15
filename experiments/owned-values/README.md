# Owned text and collection fields: isolated native candidate

Source sprint 0.42. This extends the hash-pinned borrowed-record candidate without replacing `native/compiler/compiler.rf2` or published packages. `prepare.py` checks each patch exactly once, then exclusively writes a new compiler source after all checks succeed. The resulting compiler is RF2 source compiled directly to an ARM64 Mac executable; Python is development preparation/verification tooling, not an application runtime.

## Supported syntax

```text
result IO(u64,u64)
text Label(IO,256)
collection Readings(IO,65536)
record Batch(label:own Label,readings:own Readings,revision:u64)
```

Inside a function returning the same nominal `IO`, `own batch=Batch(Label(),Readings(),1)` creates empty owned children and a scalar revision. Alternatively, construct with `move(existing_label)` and `move(existing_readings)`. `own report=move(batch)` transfers the aggregate; `own extracted=move(report.label)` transfers one field. Typed uses of consumed roots/fields refuse. An aggregate with an extracted field cannot subsequently be moved whole.

The complete [labelled-batch application](examples/owned-batch.flow) and [shared library](examples/lib/batch.flow) decode a supplied UTF-8 label, parse numeric stdin, transfer both owners into a batch and move the batch before emitting JSON. Empty numeric input is valid. Its `characters` value counts Unicode scalars, not grapheme clusters or screen glyphs. The library can leave a decoded prefix on an error; the caller destroys it through ordinary cleanup and does not publish a success result.

## Build and run explicitly

From the repository root, choose an existing qualified Mac compiler. Use fresh output paths:

```sh
python3 experiments/owned-values/prepare.py artifacts/owned-demo/source
sh tools/build-program.sh /absolute/qualified/rf2c artifacts/owned-demo/source/compiler.flow artifacts/owned-demo/compiler --opt
mkdir -p artifacts/owned-demo/app/lib
cp experiments/owned-values/examples/owned-batch.flow artifacts/owned-demo/app/main.flow
cp experiments/owned-values/examples/lib/batch.flow artifacts/owned-demo/app/lib/batch.flow
cp examples/collection-tools/lib/numbers.rf2 examples/collection-tools/lib/output.rf2 artifacts/owned-demo/app/lib/
sh tools/build-program.sh artifacts/owned-demo/compiler/program artifacts/owned-demo/app/main.flow artifacts/owned-demo/app-build --opt
printf '9,1,9,3,2' | ./artifacts/owned-demo/app-build/program 'தமிழ் test 😀'
```

Expected JSON: `{"label":"தமிழ் test 😀","characters":12,"count":5,"sum":24,"revision":1}`. The app refuses invalid UTF-8, more than 256 scalars/1024 input bytes, malformed or overflowing readings and failed output with exit 2. Numeric results are checked u64 decimal integers; JSON consumers need lossless integer handling above 2^53-1. Output errors can follow partial stdout; do not treat that as a complete JSON result. Compilation and execution are separate steps. Nothing downloads or flashes a device.

## API and representation

| Operation | Behavior |
| --- | --- |
| `text_append(owner,scalar)` | Exhaustive typed result; validates 0..0x10FFFF excluding 0xD800..0xDFFF before mutation |
| `text_get(owner,index)` | Exhaustive typed result; err34 outside logical length |
| `text_reserve(owner,n)` | Recoverable capacity growth within the nominal scalar limit |
| `text_clear(owner)` | Clears logical content, retains capacity |
| `.length`, `.capacity`, `.limit` | Scalar counts; released owners cause a controlled bounds trap on property reads |
| `collection_*` | Existing u64 collection operations; a text type cannot be passed to them |
| `release(owner)` | Releases a child/local owner; failures retain the existing heap retirement/retry semantics |

Text stores validated scalars in u64 heap cells. It is not a compact UTF-8 string, normalization/collation engine or grapheme model. Text and collections remain distinct nominal types even though they share descriptor/allocator machinery. Limits are 1..65536 elements/scalars; aggregate fields are scalar u64 or explicitly owned text/u64 collections with one shared result type. No file/vector/borrowed/nested-aggregate children are admitted in this version. The four new text operation names are reserved in this candidate.

An aggregate uses a liveness word, scalar/descriptor-reference field table and inline child descriptors in its stack frame. Each child retains its own cleanup registration. Moves copy all six descriptor words, including pending retirement ownership, and disarm the source. Scalar fields may be assigned; child rebinding, raw descriptor extraction and owner copying refuse. Source field access is checked after an extraction. Runtime armed guards also cover closed states that cannot be decided statically.

Construction evaluates fields left to right. Earlier moved children belong to the partial destination if a later child fails; they are retired through the function's error cleanup. This is not rollback that restores earlier source bindings. A root is usable only after complete construction. Ordinary returns clean up child registrations in reverse order, preserving a primary error or reporting `65536+errno` for a cleanup-only failure. Cleanup continues for peers after a child fails. Persistent OS retirement refusal can leave memory until process exit; neither release errors nor aggregate cleanup promise infallible rollback.

The existing 16 cleanup registrations and 256 local-slot limits remain. Both live and moved-from owners occupy static registrations; eight owned children plus one whole move use all sixteen. Hidden descriptor slots count against the frame/local budgets. Whole aggregates cannot be function parameters or result payloads. Text/collection parameters are temporary typed mutable borrows; they cannot move or release ownership.

## Qualification and remaining gates

```sh
RF2_OWNED_COMPILER=/absolute/candidate/program python3 tests/standalone/owned_values_verify.py
```

Read [the qualification report](../../docs/OWNED-VALUES-0.42.md). Fault tests patch only disposable owned images and explicitly identify their offsets and hashes. Pointer observation is test instrumentation, never a source API. Actual kernel OOM, physical hardware, general raw-pointer safety, asynchronous cancellation, cross-function owner return, concurrency and performance/token advantages are not established.

This candidate advances a bounded part of G1. It does not complete G1 or authorize silently replacing installed native compilers. [Application-value requirements](../../docs/APPLICATION-VALUES.md) and [progress](../../docs/PROGRESS.md) retain the remaining promotion gates.
