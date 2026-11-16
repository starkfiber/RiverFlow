# Passage Desk: frozen application construction task

Build a useful read-only text review application in the assigned language. Deliver a CLI, a standalone HTML report and a launch-selected read-only MCP interface. This is a warm-SDK composition task: reusable helpers are supplied, but no application entry, report assembly or renderer is supplied. Do not use another implementation language, install packages, access other workspaces or prior attempts, contact remote services, or modify the supplied task/SDK. Keep generated source and self-tests. Do not invent results.

## Launch and JSON contract

Deliver `launch.json` as exactly `["./app"]` for RF2 or `["python3","app.py"]` for Python, relative to this directory. RF2 must actually compile and sign a native executable `app`. No shell wrapper. Commands:

- `report FILE QUERY`: read the selected regular file and emit one JSON object and a newline.
- `html FILE QUERY`: emit one UTF-8 standalone HTML document to stdout.
- `mcp FILE QUERY`: serve newline JSON-RPC over stdin/stdout, without a banner.

Exactly three application arguments (command, FILE, QUERY) are required: RF2 argc is 4 and Python len(sys.argv) is 4; the Python interpreter itself is not an application argument. No file writes, recursive directory discovery or arbitrary network effects. The selected path may contain spaces/Unicode. Refuse a final-component symlink, directory, FIFO or missing file; parent directory components are trusted. File content is at most 1,048,576 bytes; read with that bound, not an unbounded read. Empty files are valid. File reads are sequential captures, not atomic filesystem snapshots. The selected file must be reread on every MCP callback. Never change its bytes or any other source file.

Input and query must be strict UTF-8. Reject NUL and C0 control scalars except TAB (9), LF (10) and CR (13). Query must be 1..128 encoded UTF-8 bytes; no normalization or case folding. Match exact byte substrings, including overlapping matches. `first_byte` is the first zero-based byte offset, or JSON `null` when absent. Unicode scalars are code points, not graphemes. Lines equal the number of LF bytes plus one for a nonempty file not ending in LF; CR alone is not a line break. Words are maximal nonempty runs separated by exactly TAB/LF/CR/ASCII space; other Unicode whitespace is part of a word.

Successful JSON has exactly these keys and types:

```
{"schema":"passage-desk.v1","bytes":0,"scalars":0,"lines":0,"words_ascii_breaks":0,"query":"a","matches":0,"first_byte":null}
```

Numbers are ordinary JSON integers within the stated small bounds. The query string is the original Unicode string. No extra fields. On invalid arguments/input/read failure, CLI exits 2, emits no stdout success or partial result, and writes a short explanatory diagnostic on stderr. All normal successes exit 0. Do not claim that a missing/invalid file is an empty successful report. Build the complete result before writing it. Output failures exit 2 with a diagnostic where possible; transport writes may already have emitted bytes and cannot be rolled back.

## HTML report

Use the same reading, validation and metrics as `report`. The document must have `<!doctype html>`, `html lang="en"`, a nonempty `title`, one `h1`, a captioned table with human-readable `th` labels and six `td` elements identified by `id="bytes"`, `scalars`, `lines`, `words`, `matches`, `first_byte`. Their text is the exact decimal metric, except absent first offset is `none`. Show the original query as escaped text inside one element `id="query"`. Include embedded responsive CSS, readable typography and focus styles for a local link to the report heading. No scripts, event-handler attributes, iframes, external fonts/images/stylesheets, remote URLs or raw source-file content. Escaping must preserve visible text, including `<`, `>`, `&`, quotes and non-ASCII characters. Use a viewport meta tag and table headers. This is an exported report, not an HTTP server or native widget GUI.

## Bounded read-only MCP

Use the supplied generic legacy helper if useful. Advertise exactly one tool named `passage_report`, with object input schema, no properties and `additionalProperties:false`. Protocol version `2025-11-25`; initialize, initialized notification, ping, tools/list and tools/call must work. Tool arguments must be an explicit empty object. No path/query/write/source/network tools or arguments. The callback produces the exact same report as CLI for the launch-selected file/query and rereads the file on each call. The maximum report is bounded by the task, below the helper's 65,536-byte payload cap.

Invalid method/tool/arguments use JSON-RPC errors; a callback read/validation failure uses a tool result `isError:true` and no successful `structuredContent`. Notifications must not call the callback. Malformed JSON, duplicate decoded keys and oversized lines refuse while leaving a later valid ping usable. The MCP connection must stay usable after a failed callback so correcting the selected file allows a later call to succeed. Normal EOF exits 0. No authentication or modern protocol compatibility claim.

## Delivery and constraints

Write README.md with build/run steps, a working example and the documented limits. Use your own tests before finishing. You have one 600-second attempt. No human repairs occur during it. The external controller grades afterward; do not inspect, edit or claim to pass that unseen grader. Supplied library/package development is excluded from this authoring timer and is not your work. All actual attempts, failures, elapsed time and provider-reported usage will be retained.
