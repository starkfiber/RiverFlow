# RiverFlow native compiler and self-reproduction

The 0.5 compiler milestone adds `rf2c`, written in RiverFlow systems source. It compiles the documented, bounded `RF2_SYSTEM_A64_V1` subset directly to ARM64 Mach-O. It does not invoke Python, Node, C/C++, an assembler or a linker. macOS signing remains a separate OS build step.

This is a **self-hosting milestone for the tested systems compiler subset**, not a claim that every RiverFlow dialect, application service, Core helper or hardware backend is complete. Compact V1 arithmetic remains compatible. Runtime 0.6 additionally implements general Core and the versioned attendance export capability.

## Rebuild without Python

Start from the native compiler in the 0.5 download. Use a new output path; existing files and symlinks are refused.

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
./next-runtime/rf2 run examples/compact/sum.rf2 '[1,2,3]'
```

The compiler emits an unsigned image. Do not execute it until the normal macOS signing step succeeds. The shipped compiler is ad-hoc signed, not notarized. This workflow does not alter macOS security policy. It still depends on the operating system, its loader/signing interfaces, the ARM64 ISA and an existing trusted compiler executable.

The old Python seed remains as a historical bootstrap and development comparison oracle. Removing it from the normal native rebuild path does not erase that history or establish a source-trust proof.

## What the fixed point establishes

The development verification constructs a first native compiler using the historical encoder. That native compiler compiles its own source to a second compiler; the second compiles the same source again. The resulting **unsigned executable images match byte for byte**, including their source-derived UUID. A third native generation matches too.

The native-generated compiler also reproduces the current runtime image exactly. Values, successful work counts, overflow refusals and recovery are then tested by executing that generated runtime. Native compilation stages run with `PATH=/nonexistent`; the controller explicitly invokes the OS signing utility between stages.

This demonstrates reproduction on the tested Apple Silicon Mac. It does not independently verify all source semantics, eliminate a shared compiler defect, qualify every macOS version, or constitute diverse double compilation. A matching fixed point is not a proof that a bootstrap contains no malicious logic.

## Explicit implementation contract

Source: `native/compiler/compiler.rf2`. Machine emission: direct AArch64 instruction words, branches, addresses, stack frames and Mach-O layout. The compiler includes its own bounded tokenizer, precedence parser, symbol/label tables, string storage, image writer and SHA-256 computation for the source UUID. The hash follows the SHA-256 design in NIST FIPS 180-4; testing is not NIST certification: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf.

The native compiler accepts named functions, up to eight scalar arguments, unique function-local variables, explicit `let`/`set`, `do`, `return`, `if`/`else`, `while`, arithmetic/bitwise operators, unsigned comparisons, raw memory primitives and the existing explicit OS calls. Arithmetic and shift/division semantics follow the systems profile, not u32 Core. Comparison chains reject.

The supported lexical subset uses ASCII identifiers, decimal integers or lowercase `0x` hex integers, double-quoted strings with `\\`, `\"`, `\n`, `\r`, `\t`, `\b` and `\f`. Alternate Python literal spellings and single-quoted strings are not promised compatible. Quotes are data, not operators. Full-line and trailing comments begin with `#` outside strings. Trusted source is responsible for raw pointer validity and program termination.

Bounds: source 512 KiB; 65,536 tokens; 128 functions; 256 locals/function; eight parameters/arguments; parser/block depth below 64; generated code 1 MiB; emitted data below 128 MiB; bounded label/object/fixup tables. Limits reject before opening the output file. Input/output errors can still leave a partial newly created file, which is not a successful build. The compiler will never overwrite an existing output, including a symlink target.

This is a trusted developer compiler. It is **not** exposed as a machine-source execution tool over MCP and is not a hostile-code sandbox. Compact user inputs retain their separate narrow effect boundary.

## Reproduce the verification

Developers can compare against the historical encoder and reference runtime using Python and Node as independent test controllers, not compiler runtime dependencies:

```sh
python3 bootstrap/seed.py native/compiler/compiler.rf2 \
  output/compiler-stage0/rf2c
python3 tests/standalone/compiler_verify.py
```

Read `NATIVE-COMPILER-VERIFICATION.json` for actual executed counts, source hashes and image identities. The test suite covers independent arithmetic/control-flow/memory expectations, native-versus-reference bytes, full SHA-256 outputs at padding boundaries, malformed source, resource limits and output protection. Existing runtime tests are also executed against the native-built image rather than only the published binary.

Release 0.5 added the separate compiler while retaining runtime 0.4. Runtime 0.6 now reports0.6 and is composed from five modules through tools/build-runtime.sh. New evidence is in NATIVE-COMPILER-0.6-VERIFICATION.json; the older report remains a historical checkpoint.

## Next gates

Review the instruction encoder and parser independently; add broader structured fuzzing and admission tests; migrate general Core source and helpers into the native toolchain; qualify another target; then add one real versioned service capability with explicit effects and acceptance tests. No speed, energy or token-saving result is established by self-reproduction.

Release 0.7 composes the invoice adapter and prefixed generated kernel as two additional modules. The complete runtime reaches the existing 128-function bound. The unchanged compiler reproduces the complete new runtime byte for byte with the historical encoder; see NATIVE-COMPILER-0.7-VERIFICATION.json. No compiler bound was silently relaxed.
