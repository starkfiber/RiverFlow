# Text, bytes and recoverable library errors, 0.12

## Six delivered pieces

1. Packed, nominal fixed `u8` arrays with zero initialization and range-checked indexing.
2. Typed `read_bytes` and `write_bytes` intrinsics with capacity checks and explicit file descriptors.
3. Recoverable byte-access and I/O operations using an `Outcome` record.
4. Streaming UTF-8 validity checks that retain incomplete sequences across reads.
5. Checked decimal-to-u64 parsing with exact overflow detection and error offsets.
6. A complete bounded file/stdin audit app, including closure of its owned descriptor on normal/error return paths.

These are executed native capabilities. They do not establish a general exception system, heap ownership, Unicode normalization, concurrent safety or additional machine targets.

## Bytes and authority

```rf2
array Packet(u8, 128)
```

The capacity is a canonical decimal integer from 1 to 255. Byte storage is packed into ceil(capacity/8) zeroed stack slots, plus the local pointer slot. Scalar indexing is unsigned and checked. Reading yields a scalar from 0 through 255. Ordinary writes outside that value range or outside capacity use the existing status-2 trap. The frame and nominal lifetime restrictions of fixed u64 arrays still apply. Zero-sized logical content is represented by a separate count of zero.

`read_bytes(fd, data, count)` and `write_bytes(fd, data, count)` accept only a typed u8 array and scalar descriptor/count. No raw array pointer is exposed. Requests beyond capacity return -22 in the wrapping u64 representation before the OS operation. OS failures return negative errno; successful operations return the actual byte count, including short reads/writes. Callers must handle short writes. The Darwin error value is documented in [Apple's errno definitions](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/errno.h).

These are trusted systems-profile OS operations, CLI compiler only. They are not accepted by bounded Core or exposed as filesystem/network effects over MCP. The intrinsic names are reserved. No implicit file selection, network connection or source execution occurs.

## Recoverable status API

The example's reusable byte module defines `Outcome(code, value, offset)` as a nominal record passed by reference. Operations fill every field on success or failure, preventing a stale successful value from surviving a later error. The caller explicitly inspects code before relying on value. The language does not yet enforce that inspection.

| Code | Meaning | Detail |
| --- | --- | --- |
| 0 | Success | value contains the byte/count/integer |
| 1 | Range failure | offset identifies the invalid index/request |
| 2 | Byte value out of range | offset is the attempted index |
| 3 | Invalid or empty decimal | offset identifies the bad byte |
| 4 | Decimal u64 overflow | offset identifies the overflowing digit |
| 5 | I/O failure | offset contains positive errno |
| 6 | App input limit | offset is the processed-byte limit |

`bytes_get`, `bytes_set`, `bytes_read`, `bytes_write` and `bytes_parse_u64` implement these contracts. Recovery means the program can inspect failure and call a valid operation afterwards without exiting or retaining stale result fields. These are explicit library result records, not algebraic return types, exceptions, automatic propagation, a mandatory match construct or generic collections.

Decimal parsing accepts ASCII digits and leading zeros within the supplied logical range. Empty input, signs, fractional values and other bytes return a recoverable error. Before multiplying by ten, the parser checks the maximum quotient and last digit for u64. It does not wrap an overflowing value into a successful result.

## UTF-8 and text audit

The streaming state rejects overlong sequences, surrogate encodings, isolated continuation bytes, incomplete trailing sequences and values above U+10FFFF. It accepts well-formed scalar encodings, including unassigned code points, embedded NUL and sequences crossing the 128-byte read boundary. The encoding rules are referenced to [Unicode 17, section 3.9, table 3-7](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/).

The audit groups an invalid started sequence as one event, reprocesses a non-continuation byte as a possible new start, and counts isolated invalid lead bytes separately. This is an explicit diagnostic policy, not a claim of Unicode maximal-subpart replacement or a transcoder. No replacement text is written. The first-error field is the zero-based start of the earliest invalid sequence. Later valid text is still processed. Tests compare validity and first-error start with Python's independent strict UTF-8 decoder, while selected grouping cases follow the documented policy.

Counts are Unicode scalars, not grapheme clusters or user-perceived characters. Word separation uses ASCII whitespace plus NUL; invalid groups break a word. LF newlines are counted literally. There is no normalization, casing, locale word segmentation or removal of a byte-order mark.

The app processes at most 1,048,576 bytes. It reads an additional bounded chunk when necessary to discover the limit. Limit failure is an incomplete audit, not proof that a pending sequence at that boundary is malformed. Explicit files are opened read-only and closed after audit success, read failure or limit failure; stdin is borrowed and never closed by the audit routine. This is ordinary scoped control flow, not a general RAII/defer facility. An explicit caller-selected special file can still block; no universal wall-time bound is claimed.

## Reproduce

```sh
./tools/build-program.sh ./rf2c examples/text-audit/main.rf2 new-audit-build --opt
printf 'Hello RF2\n' | ./new-audit-build/program
./new-audit-build/program document.txt
```

App status is 0 for a complete valid audit, 1 for usage/I/O/limit errors, and 2 for a completed audit containing invalid UTF-8. A JSON summary is emitted after audit processing; usage errors print usage text. Input is not modified and no report file is created implicitly.

Developer verification: tests/standalone/text_verify.py with RF2_TEST_COMPILER. [Executed receipt](TEXT-BYTES-VERIFICATION.json). The experiment makes no speed, energy, token-saving, participant or phone claim.

## The next six gates

| Next capability | Completion evidence |
| --- | --- |
| General typed result values and exhaustive handling | Compile refusals for missing cases, propagation and nested-call tests |
| Reusable byte spans and text views | Lifetime/alias rules, sliced-boundary tests, no raw-pointer escape |
| Explicit owned-resource cleanup | Defined transfer/close semantics and failure-path tests |
| Growable collections | Allocation failure, growth, aliasing and memory-budget tests |
| Tasks and cancellation | Defined shared-memory rules, races/refusals, cancellation and cleanup tests |
| One shared core on a second platform | Actual target build and exercised application artifact with equivalent outputs |

These remain future gates, not six completed platform claims. AI-assisted tooling can generate and challenge programs against the contracts; it is not an embedded model or automatic proof of an arbitrary program.
