# Native compiler diagnostics and integer literal bounds, development 0.31

A failed compile now reports a nearby source position after its existing error message. This helps a person or an AI editor locate a mistake without changing valid program semantics or granting new MCP authority.

```text
integer literal exceeds u64
near source 3:9 (line:byte-column; entry program.rf2)
```

For example, this is refused before an executable is created:

```rf2
profile RF2_SYSTEM_A64_V1
fn main(argc,argv)
 return 18446744073709551616
end
```

Change the value to a representable unsigned integer. The largest accepted positive literal is `18446744073709551615`, equivalently `0xffffffffffffffff`. The maximum is not a platform-dependent signed integer limit. Negative expressions such as `-9223372036854775808` remain representable, and ordinary runtime unsigned arithmetic retains its existing wrapping rules.

## What changed

Decimal and hexadecimal literal parsing previously accumulated directly into a u64, silently wrapping an out-of-range source literal. It now checks `value <= (U64_MAX - digit) // radix` before each multiply-add. Values beyond u64 are rejected rather than silently converted to a different value. This is a correctness fix, not a performance optimization or a new arbitrary-precision number type.

The compiler records a bounded raw source offset for each token, including strings whose contents are decoded into another buffer. It computes the line and column only on a failure. There is no repeated whole-source line scan on successful tokenization. Synthetic end-of-file tokens point to the end of the source rather than a string-arena address.

## Read the position accurately

- Lines and columns start at 1. Columns count source bytes, not terminal width, Unicode scalars or grapheme clusters.
- A lexical error points near the start of the token being read. A parse or checking error points near the current parser cursor. That cursor can be after a consumed invalid identifier; it is not always the exact offending character.
- Imported programs report `near expanded-source` and the entry path. The line is in the compiler's expanded input. It is not presented as a line in the original imported file. Original per-module provenance remains further work.
- File-open, module-resolution, cache and output errors do not receive an unrelated stale parser position. A failed import header can therefore still have no source position.
- The additional location line emits no source excerpt. Its entry path is limited to 256 bytes and nonprintable or non-ASCII path bytes are shown as `?`. The `expected ... got ...` message includes at most 80 bytes of printable ASCII token preview, replaces other bytes with `?` and adds an ellipsis when truncated. It remains a source preview, so the diagnostic stream is not a secret-redaction interface. This corrects the previous unbounded raw-token echo, including terminal control sequences.

The position table reserves 256 KiB for at most 65,536 tokens, within the existing token/source bounds. This is not a measured physical-memory or energy improvement.

## Verification

Run the developer controller with an explicitly supplied signed native compiler and preserved 0.30 baseline:

```sh
RF2_TEST_COMPILER=/absolute/path/to/current-rf2c \
RF2_OLD_COMPILER=/absolute/path/to/previous-rf2c \
python3 tests/standalone/diagnostics_verify.py
```

Python is the development controller, not a dependency of the native compiler or compiled applications. The controller requires a new artifact directory, verifies actual refusal messages and positions, compares valid unsigned images against the previous compiler, signs native outputs and checks process exits.

The executed campaign passed 41 checks: local/function errors, missing end, EOF without newline, parameter syntax, string controls and escapes, empty hex literals, duplicate locals, non-ASCII invalid source, six out-of-range integer inputs, I/O/cache errors without fake locations, an imported error labelled as expanded source, fifteen valid constant/runtime-wrap checks across compiler modes, imported valid code CRLF source, a 100,000-byte token, ESC, NUL and another control byte. See [the source controller](../tests/standalone/diagnostics_verify.py) and [the retained verification receipt](DIAGNOSTICS-0.31-VERIFICATION.json).

The maintained reference encoder and three native compiler generations also matched unsigned images; the freshly compiled runtime passed the runtime corpus and official MCP SDK checks. These finite checks do not establish complete language coverage, independent institutional approval or universal security.

## Check before building

```sh
./rf2c --check program.rf2
```

A successful check prints `RF2 source checked; no executable written.` and exits 0. It checks the complete trusted systems source through code generation, object layout and relocation. This catches checks that occur after parsing, rather than merely recognizing valid syntax. It creates no executable, map or function cache. It never runs the supplied program.

The first edition accepts exactly one source path and no additional options. `--opt`, `--compact`, `--functions` and either cache option reject when combined with `--check`. Check-only uses the default backend settings; it does not qualify another target or prove runtime correctness. Normal source/output compilation and its options remain available separately. Source-local imports retain their trusted filesystem contract. This command is not a sandbox or a new raw-systems MCP capability.

[The check-only controller](../tests/standalone/check_only_verify.py) verifies valid and invalid inputs against normal clean compilation, exact workspace manifests before/after each check, imports, argument refusals and missing files. A supplied writer program creates its expected marker only when separately compiled and deliberately executed as a positive control. The controller also compares valid normal-build bytes against the preserved compiler across default/optimized/compact modes and checks the independent maintained encoder/native default fixed point. [Retained receipt](CHECK-ONLY-0.31-VERIFICATION.json).

The existing source reader may block on a FIFO or device path; those paths were deliberately excluded from this finite regular-file campaign. Check-only does not promise nonblocking arbitrary filesystem input. Improved original-module provenance and more precise offending-token spans remain further work.
