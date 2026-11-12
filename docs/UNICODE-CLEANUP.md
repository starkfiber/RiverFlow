# Unicode scalar views and deferred cleanup, 0.14

RF2 adds validated, immutable UTF-8 spans and automatic deferred close attempts in the trusted systems compiler. Both are native RF2 capabilities. The nine bounded MCP tools keep their existing effects and schemas; arbitrary systems source is still CLI-only.

## One text value, two units

```rf2
array Bytes(u8,255)
textview Text(Bytes)
fn inspect(data:Bytes,count)
 let text=Text(data,0,count)
 let scalars=text.length
 let bytes=text.byte_length
 return scalars
end
```

The constructor takes a byte start and byte count in its declared nominal owner type. It validates exactly that selected span as strict UTF-8, including overlong encodings, surrogates, continuation constraints, truncation and the U+10FFFF upper limit. NUL, BOM and noncharacters are valid scalar values. Bytes outside the selected span need not be valid. Empty spans at capacity are valid.

`.length` counts Unicode scalar values; `.byte_length` counts encoded bytes. `text[i]` returns the scalar value at zero-based scalar index i, with an upfront unsigned scalar-count bounds check. A Tamil letter, a combining mark and a zero-width joiner are each scalars. This is not grapheme segmentation, normalization, locale collation or display width. Index lookup scans from the start; no constant-time indexing or speed claim is made.

The view stores pointer, byte count and scalar count in the current frame. There is no source-byte copy. It cannot escape, be passed, copied, rebound or written through. Existing conservative view rules apply: after the first byte/text view, calls and array element updates are refused until the function returns. Multiple overlapping views may coexist, and fresh distinct owned-array initialization is allowed. Raw systems pointers, concurrent external mutation and malicious unsafe code remain outside this checked contract.

Invalid ranges/indexes print `RF2 bounds` and exit2. Invalid UTF-8 prints `RF2 UTF8` and exits2. These are fatal process traps, not typed errors. Untrusted input requiring recovery must be checked before construction. The real app does that explicitly.

## Automatic action on ordinary function exit

```rf2
fn read_file(path)
 let fd=open(path,0,0)
 if fd>>63
  return 1
 end
 defer close(fd)
 # Further ordinary returns automatically attempt close of captured fd.
 return 0
end
```

`defer close(expression)` is function-level only and evaluates its scalar expression exactly once, when reached. Its captured descriptor is armed only after evaluation completes. An early return before registration does not touch the uninitialized capture. A common native epilogue attempts armed closes in reverse registration order on explicit scalar/typed returns and implicit scalar fallthrough. Return tag/payload registers survive cleanup. At most16 registrations per function share the existing256 local-slot/frame budget; each uses two hidden slots.

A close failure does not overwrite the authored result. This is best-effort cleanup, not guaranteed successful release or a general resource ownership system. It supports close only, not arbitrary callbacks, block/loop registration, cancellation or destructors. Named descriptors need one registration; borrowed stdin must not be registered. The app follows that rule.

Raw descriptors remain copyable trusted integers. Manually closing a deferred descriptor, then opening another resource with that reused number, can cause the deferred action to close the replacement. This limitation is retained as a test and must not be described as linear ownership. Fatal bounds/UTF8 traps, explicit process exit and signals bypass ordinary epilogues; OS process reclamation is distinct from running language cleanup. Cleanup is not promised after those paths.

Registration after a live view is refused, although an earlier registered close can run at function exit once the view is dead. This keeps the existing source-level call freeze intact.

## Real application

`rf2-unicode-lines` processes UTF-8 documents from stdin or one explicit file. It recovers from malformed/oversized lines, reports valid/rejected lines, scalar counts, Tamil-block counts and a scalar fingerprint. It uses a separate strict byte prevalidator, then a text view for actual scalar processing, and typed result handlers for line/open/read outcomes. A named file is automatically closed after ordinary success or failure; stdin remains borrowed.

LF separates rows, CR remains a scalar, and a terminal LF adds no phantom empty row. NUL does not terminate text. The line cap is255 bytes and processed-input cap1MiB. File reads may read ahead one bounded chunk; statistics report processed bytes. Detailed statuses, partial statistics and output-write limits are in [the app contract](../examples/unicode-lines/README.md).

## Challenged, corrected, replayed

Two independent agent tasks authored tests and inspected source; a third implemented the app and its separate Python oracle. The first decoder candidate failed valid U+FEFF because the native left-shift opcode was wrong; its error string constant was also wrong. Both were corrected. A parent review then found that an index of unsigned maximum matched the helper's internal validation sentinel. The upfront scalar bounds check corrected that case. Retained failures are engineering evidence, not results to erase.

Independent strict Python UTF-8 decoding and scalar expectations cover Tamil, combining sequences, emoji, NUL, noncharacters, malformed encodings and selected-span isolation. Cleanup tests observe actual descriptor validity inside a live process, not merely process exit. LIFO emission is inspected; close-only runtime cases demonstrate multiple releases, not an observable ordering trace. Previous0.13 result/view tests, compiler self-generation, existing runtime regressions, official MCP SDK and clean package checks remain required for this release.

These are finite host checks, not human academic approval, formal compiler proof or security certification. No new speed, token-saving, energy or hardware result is claimed. The next foundations are typed ownership, cleanup error handling, composable immutable calls, structured results and growable text storage.

## Reproduce and inspect receipts

Set RF2_TEST_COMPILER to the qualified native compiler, then run tests/standalone/unicode_view_adversarial.py, cleanup_adversarial.py and unicode_lines_verify.py. These are development controllers; installed user binaries have no Python dependency.

Final qualification:686 Unicode-view probes,52 cleanup probes and332 real application checks passed across default and optimized builds. All24 existing regression/SDK qualification records passed, alongside the separate compiler fixed-point and prior158 adversarial result/view replay.

[Unicode receipt](UNICODE-VIEWS-0.14-VERIFICATION.json) · [Cleanup receipt](CLEANUP-0.14-VERIFICATION.json) · [Application receipt](UNICODE-LINES-0.14-VERIFICATION.json) · [Release qualification](RELEASE-0.14-VERIFICATION.json).
