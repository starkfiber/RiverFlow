# Count matching lines in supplied logs

`log-scan` reads standard input and reports exact byte matches within each LF-delimited line. It does not discover files, read a production log, classify incident causes or upload data. The examples are supplied programming inputs.

```sh
./tools/build-program.sh /absolute/path/to/rf2c examples/text-search/log-scan.rf2 log-scan-build --opt
printf 'ERROR first\nOK\nERROR ERROR last\n' | ./log-scan-build/program ERROR
# {"bytes":32,"query_bytes":5,"lines":3,"matching_lines":2,"matches":3,"first_line":1}
```

The entry file intentionally lives beside `examples/text-search/main.rf2`, under one module root. Both import the same physical `examples/text-search/lib/search.rf2` implementation and own their own typed prefix workspace. This guide points to that actual source; there is no second library copy or symlink.

Use the qualified development 0.32 native compiler. Programs need no Python, Node or C++ runtime. The current query budget is 4096 bytes and input is bounded at 1 MiB. Developer tests use independent Python byte oracles; that is not an application runtime dependency. No new MCP authority is granted by this CLI.

## Exact line and query semantics

- LF is the only delimiter and is excluded from searched content. CR is retained, including the CR in a CRLF sequence; no normalization occurs.
- Empty input has zero lines. A final unterminated sequence has one line. A trailing LF terminates the preceding line and does not create an additional empty line.
- Empty lines are real lines: `\n\n` contains two. An empty query matches every byte boundary within each existing line. Empty input still has zero matches.
- Matching is case-sensitive exact bytes. UTF-8 text is accepted as encoded bytes; no grapheme, locale, semantic, regex or fuzzy matching is supplied.
- Matches are nonoverlapping within each line. A match cannot cross LF. `matching_lines` counts lines with at least one match. `first_line` is 1-based or null when none matches.
- JSON `bytes` includes all supplied bytes, including delimiters. `matches` totals within-line matches.

The CLI reserves standalone `--help`. It accepts exactly one query, waits for EOF and does not impose a timeout on an unending input stream. An operating-system argument cannot contain NUL; the shared library API accepts binary needles. The borrowed stdin/stdout descriptors remain open.

Exit codes match the text-search application: 0 complete/help,2 invalid arguments/query,3 read failure,4 input above1 MiB,5 write failure. Output after an I/O failure may be partial JSON, so check the process exit code. No files or background workers are created.

## Reproduce both applications

```sh
RF2_TEST_COMPILER=/absolute/path/to/rf2c python3 tests/standalone/shared_search_apps_verify.py
RF2_TEST_COMPILER=/absolute/path/to/rf2c python3 tests/standalone/text_search_verify.py
```

The shared-app controller compiles both entry files using the same source fingerprint, exercises ordinary/optimized modes, compares independently computed results, checks split stdin writes, LF/CRLF/empty/binary/UTF-8 cases and tests input/descriptor failures. Finite passing cases do not establish production-log accuracy, concurrency, general memory safety or speed superiority.

This is source-module reuse: each native executable contains its compiled library code. It is not dynamic shared-object loading or a global package manager. The shared-app controller also changes one library in a disposable project and confirms both applications reflect that change, while canonical source hashes remain fixed.
