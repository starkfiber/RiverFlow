# RF2 text audit

Native byte/text processing with recoverable library errors. Build with the 0.12 compiler as described in [the contract](../../docs/TEXT-BYTES.md).

The program reads stdin or one explicit file path, validates UTF-8 in 128-byte chunks, and emits a JSON summary of processed bytes, Unicode scalars, LF newlines, ASCII-whitespace words, invalid groups, first error, NUL scalars and I/O status. Tamil and emoji are valid input. Scalar counts do not equal displayed-character counts.

Malformed sequences are reported while later text continues to be processed. Input is not repaired or changed. The audit caps processed input at 1 MiB. I/O/limit failures mean the audit is incomplete. Status 0 means complete and valid; 1 means usage/I/O/limit failure; 2 means complete with invalid encoding.

Library files cover typed bytes, an explicit Outcome record, checked decimal u64 parsing, UTF-8 state and owned-file cleanup. Ordinary checked indexing still traps; the recoverable wrappers check before indexing. Result inspection remains the caller's responsibility. This is not an exception system, arbitrary resource-ownership proof or full Unicode text library.
