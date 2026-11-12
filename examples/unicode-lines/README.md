# Unicode line auditor

A native RiverFlow CLI for checking a UTF-8 document line by line. It reports valid and rejected lines, Unicode scalar counts, non-ASCII scalars and scalars in the Tamil Unicode block. The application uses typed results, validated text views and automatic deferred file cleanup. It reads supplied data; it does not infer language, author identity or text quality.

Run the packaged `rf2-unicode-lines` with standard input, or supply one read-only input filename:

```sh
printf 'Hello\nதமிழ்\n' | ./rf2-unicode-lines
./rf2-unicode-lines document.txt
```

To build from trusted source with the native compiler, use `tools/build-program.sh rf2c examples/unicode-lines/main.rf2 new-directory --opt`. The resulting executable is `new-directory/program`. Compiling source is an explicit CLI operation, not an additional MCP effect.

## Exact behavior

* LF bytes delimit rows. A terminal LF does not create an extra row. Empty input contains zero rows; an empty delimited row is valid text containing zero scalars.
* Each row may contain at most 255 bytes, excluding LF. CR, NUL and a byte-order mark are ordinary content. A 256-byte row is rejected once, consumed through LF/end of file, and later rows are still processed.
* Rows are decoded as strict UTF-8. Overlong sequences, isolated continuation bytes, encoded surrogate values, truncated encodings and values above U+10FFFF are rejected. Unicode noncharacters are accepted scalar values.
* A rejected row contributes no scalar counts. Later valid rows still contribute. Error code 1 means invalid UTF-8; code 2 means an oversized row. The first error's row and code are preserved.
* `unicode_scalars` counts Unicode scalar values. It is not a count of visible characters, grapheme clusters, words or display columns. Decomposed accents and emoji sequences can contain several scalars.
* `tamil_scalars` counts code points U+0B80 through U+0BFF. That is a block-range statistic, not proof a document is Tamil. No normalization, case folding, segmentation or language detection runs.
* `bytes` counts consumed input bytes, including LF and rejected rows. The processed-input cap is 1 MiB. Reaching the cap while more bytes remain gives `io_error:1000`; counters then describe only processed input. The current unfinished row is not finalized on I/O/limit failure. The buffered read may have read ahead beyond the processed limit.
* Ordinary I/O failure reports a positive OS error number in `io_error` and preserves partial statistics. Invalid/oversized content is distinct from I/O failure.

Exit status is 0 for complete input with no rejected rows, 2 for complete input containing rejected rows, and 1 for usage, open/read or input-limit failure. Statistics are JSON on standard output. Output-write failure is not currently converted into a reported I/O error.

The parser first validates each row with a recoverable typed result. Only a valid row is passed to the text-view function. This avoids using a fatal view-construction failure as ordinary document recovery. The view's indexing is scalar-based; byte count remains separate. Indexing may decode from the beginning, so this app claims no constant-time Unicode indexing or performance improvement.

Named files are opened read-only, then registered with `defer close(fd)` inside `run_owned`. The compiler attempts closure on its ordinary function exit. Standard input is borrowed and not closed by `run_fd`. Close attempts are best effort and preserve the program's return value; close failure is not reflected in the JSON. Raw descriptor reuse remains a trusted-systems concern, not a linear ownership guarantee. Process traps, explicit process exit, signals and external termination do not execute ordinary function cleanup.

## Verification

`tests/standalone/unicode_lines_verify.py` builds both default and optimized programs and compares their complete JSON reports with Python's strict UTF-8 decoder and independently computed metrics. Inputs include Tamil, emoji sequences, combining marks, NUL, invalid encodings, row limits, continued processing after rejected rows, files, I/O failures and the input cap. In-process probes check that named-file descriptors have closed after successful and failed reads and that standard input remains open. These are finite local software tests, not field results, a security certification or a speed/token claim.
