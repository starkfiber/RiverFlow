# 25. Bytes, text and a recoverable failure

Release 0.12 lets a program report a failed byte operation and continue processing later valid input.

## Give bytes a real type

```rf2
array Packet(u8, 128)
```

This is a packed byte array. Each indexed read produces a value from zero through 255. Every ordinary indexed write checks both the index and value. The array is zero-initialized and owned by the current function's frame. Typed helpers borrow it without receiving an untyped memory address.

The compiler now recognizes read_bytes and write_bytes for this type. The caller supplies a descriptor and count. A request larger than capacity fails before the OS operation. A successful result is the actual count, which may be short. A negative result represents failure. The compiler does not silently choose a file, connect to a service or turn an AI request into authority over a user's machine.

Byte I/O belongs to the trusted systems profile on Apple Silicon macOS. Bounded Core and MCP permissions do not expand.

## Make the result explicit

The byte module defines an Outcome record containing code, value and offset. A helper writes all three fields on every operation. The caller checks code before using value. That rule avoids treating yesterday's successful value as today's failed result.

The library covers byte get/set, I/O and decimal parsing. Range, value and I/O failures have distinct statuses. A later valid operation can still succeed.

This is recoverable library behavior. It is not a general exception system or a tagged return type. The compiler does not yet require callers to inspect the record. Those stronger language features need their own syntax, type rules, failure cases and implementation.

The decimal parser accepts ASCII digits within an explicitly supplied range. Before multiplying by ten, it checks whether the next digit can fit in u64. An overflowing number returns an error offset rather than wrapping into a plausible successful value. Empty, signed, fractional and malformed input have stated outcomes.

## Keep text across a read boundary

A file read is not a character boundary. A four-byte UTF-8 sequence may begin at the end of one chunk and finish in the next. The decoder keeps its pending state between calls. It rejects invalid starts, continuation errors, overlong encodings, surrogates and values above the scalar range. At actual EOF it also checks for an incomplete sequence.

The audit reports errors and continues. A non-continuation byte is reconsidered as a possible new start, so a malformed prefix does not swallow a following valid letter. Its diagnostic grouping is documented separately from Unicode replacement rules. The program writes no repaired version of the input.

Counts need definitions. Combining marks count as separate scalars. LF counts as a newline; ASCII whitespace and NUL separate words. Normalization and grapheme segmentation are not implemented.

The encoding reference is Unicode 17, section 3.9 and table 3-7. Native tests compare validity and first-error position with an independent strict decoder. Tamil and emoji are included, as are malformed sequences and characters crossing the byte-buffer boundary.

## Finish the resource path

The complete audit application accepts stdin or one explicit file path. A named file is opened read-only, processed, then closed on normal return, read failure or the one-megabyte limit. Stdin is borrowed and left open. A same-process test verifies that the owned descriptor is no longer usable after each tested return path.

This is explicit control flow, not a general resource-ownership system. A caller-selected special file may still block. A short output write still needs caller handling. These limits belong in the contract rather than being hidden behind the word secure.

## Six foundations, six next gates

This sprint delivers packed bytes, bounded byte I/O, recoverable status helpers, streaming UTF-8 validation, checked integer parsing and the audit application with cleanup. Each has executable tests. There is no new speed or token-saving result to report for this increment.

Next are typed results, byte/text views, owned resources, growable collections, tasks/cancellation and a second-platform proof. Each needs implementation and acceptance tests.

Sources, primary specifications and reproduction: docs/TEXT-BYTES.md. Executed cases: docs/TEXT-BYTES-VERIFICATION.json.
