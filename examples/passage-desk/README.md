# Passage Desk

A native read-only text-review tool: exact metrics and overlapping byte search, a static HTML report, and one launch-selected read-only MCP tool. It shares `sdk/v1` with other applications; no local library copy is needed.

Build with a qualified 0.50 source compiler:

```sh
sh examples/passage-desk/build.sh /absolute/path/rf2c /absolute/path/RiverFlow/sdk/v1 /new/build-directory
/new/build-directory/app report examples/passage-desk/fixtures/brief.txt review
/new/build-directory/app html examples/passage-desk/fixtures/brief.txt review > /new/build-directory/report.html
/new/build-directory/app mcp examples/passage-desk/fixtures/brief.txt review
```

The HTML is an exported report opened in a browser, not an HTTP service or native widget window. The MCP command uses legacy2025-11-25 stdio and exposes only `passage_report` with explicit empty arguments. Every callback rereads the selected file; arguments cannot select another path/query or mutate files. No runtime Python/Node or external assets are required.

File bounds: one regular file, at most 1 MiB; final-component symlinks/nonregular files refuse; parent paths are trusted. Text/query are strict UTF-8 with TAB/LF/CR permitted and other C0 controls refused. Query1..128 bytes, exact overlapping byte matches, no normalization/case folding. Code points are not graphemes. Words use ASCII TAB/LF/CR/space breaks. Empty files are valid, absent first match is JSON null. Reads are sequential captures, not atomic filesystem snapshots. No editing, PDF extraction, authentication or cross-platform qualification is implied.

Validation/read failures emit no successful stdout. The full result is assembled before writing; a failed OS write can still deliver a prefix. Checked writes and MCP transport return failures through ordinary IO handling, including closed readers/descriptors. Descriptor policy assumes no concurrent mutation and does not guarantee cleanup on signals or fatal exit.

This is the **post-study repair exemplar**, derived from the third RF2 timed delivery. The parent added one explicit IO import and changed two output calls to `io_write_no_sigpipe`, then rebuilt against SDK B. Original sources,80-check grades, timings and provider usage remain in the [construction evidence](../../docs/SDK-PACKAGES-0.50.md). This repair receives no retroactive token/time credit. The timed SDK A and final SDK B have distinct manifest hashes.

[Shared package](../../sdk/README.md) · [Exact task contract](../../experiments/sdk-task/TASK.md) · [Compiler reproduction](../../experiments/sdk-packages/build.py)
