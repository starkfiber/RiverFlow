# Complete task B: Match metrics

Build one native `main.flow`: `app json|html PATH QUERY` (exactly three arguments).
Read only that selected regular file with io_regular, max4096bytes, input buffer
4097bytes. Validate file and query using text_measure. Query length must be1..128
bytes. Invalid args/mode/file/text/query fail nonzero without stdout. No filesystem
writes, process/network operations or raw platform calls. Emit complete bytes in
a32768byte Writer, inspect error, then checked io_write_no_sigpipe. Output errors
return nonzero. This is exact, case-sensitive overlapping byte search, not Unicode
normalization. Use text_search_overlapping and check return success/status.

Title `Match metrics`. Ordered fields:
- `Path`: exact supplied path text.
- `Query`: exact query text.
- `Matches`: u64 count.
- `First byte`: u64 zero-based first offset if matched; text `none` if no match.
- `Last byte`: u64 zero-based last offset if matched; text `none` if no match.

Output exactly JSON `{"title":"Match metrics","fields":[{"name":"Path","value":"..."},{"name":"Query","value":"..."},{"name":"Matches","value":0},{"name":"First byte","value":"none"},{"name":"Last byte","value":"none"}]}` plus LF (numeric offset values when found).
HTML `<!doctype html><html lang="en"><meta charset="utf-8"><title>Match metrics</title><main><h1>Match metrics</h1><dl><dt>Path</dt><dd>PATH</dd><dt>Query</dt><dd>QUERY</dd><dt>Matches</dt><dd>N</dd><dt>First byte</dt><dd>N_OR_none</dd><dt>Last byte</dt><dd>N_OR_none</dd></dl></main></html>` plus LF.
Escape text with writer_json/writer_html; preserve number/text types and field
order. Use only supplied APIs. Return JSON exactly {"source":"complete main.flow"}.
