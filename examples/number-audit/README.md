# RF2 number audit

A native document-processing application using compiler-checked typed results and immutable byte views. Requires the 0.13 compiler; the native package also contains a ready-to-run rf2-number-audit.

Input is stdin or one explicit read-only file. Rows are delimited by LF. ASCII space, tab and CR are trimmed at row ends; the remaining content must be decimal ASCII digits forming u64. Leading zeros are accepted. A row can contain at most 128 bytes before LF; too-long rows are rejected and processing resumes after LF. An empty file has no rows. An empty row is invalid. A terminal LF does not create an extra row.

Accepted values contribute to sum. A value that would overflow the accumulated u64 sum is rejected; later rows still run. JSON reports accepted/rejected counts, nonwrapping sum, first error's one-based line/code, processed bytes and I/O error. The first error code is 1 empty, 2 nondigit, 3 number overflow, 4 row too long, 5 sum overflow. Zero indicates no recorded row error. I/O errors contain errno, or 1000 for the 1 MiB processed-input limit; such statistics are partial.

Process status 0 means complete with no rejected rows; 2 means complete with rejected rows; 1 means usage/I/O/limit failure. The app closes its own opened file on tested processing/error paths and leaves borrowed stdin open. Input is not modified.

```sh
printf '12\nbad\n30\n' | ./rf2-number-audit
```

Expected JSON: accepted 2, rejected 1, sum 42, first_error_line 2, first_error_code 2, bytes 10, io_error 0.

Build from source through tools/build-program.sh and examples/number-audit/main.rf2. The parser's view is a checked immutable window over bytes; it does not imply Unicode-valid text. The result types have scalar payloads and fixed ok/err handling. See docs/RESULTS-VIEWS.md for restrictions and reproducible tests.
