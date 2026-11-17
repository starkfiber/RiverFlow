# Frozen complete authoring task, 17 November2026

Write one native RF2 `main.flow` application. Command: `app json|html INPUT_PATH`.
Exactly two arguments are required. Any other mode/count fails. Read the selected
regular file, maximum4096bytes, with `io_regular`; the buffer needs4097bytes for
its overflow check. Validate text using `text_measure`. Invalid UTF8, disallowed
C0, missing/oversized/nonregular file, invalid mode/args and output failures
return nonzero. Validation/input failures produce no stdout. Do not create files,
run commands, open a network, change signals or use raw platform operations.

Success emits one complete report with title `File summary` and these fields in
this exact order: text `Path` (exact supplied argument), text `Text` (entire input),
u64 `Bytes` (input byte count), u64 `Words` (`TextInfo.words`). JSON shape:
`{"title":"File summary","fields":[{"name":"Path","value":"..."},{"name":"Text","value":"..."},{"name":"Bytes","value":0},{"name":"Words","value":0}]}`
followed by LF. JSON must escape text safely and retain numerical types.

HTML bytes must be exactly:
`<!doctype html><html lang="en"><meta charset="utf-8"><title>File summary</title><main><h1>File summary</h1><dl><dt>Path</dt><dd>PATH</dd><dt>Text</dt><dd>TEXT</dd><dt>Bytes</dt><dd>N</dd><dt>Words</dt><dd>N</dd></dl></main></html>`
followed by LF. Escape PATH/TEXT using `writer_html` (including quotes).

Build all bytes in a32768byte Writer, check `out.error`, then publish with
`io_write_no_sigpipe(1,out.data,out.used):IO`, handling failure. This operation
handles short writes and temporarily changes/restores a borrowed descriptor's
no-SIGPIPE policy; it is the only permitted output operation. No MCP server,
GUI, filesystem writes or external libraries are required. Functions and source
may use only the supplied trusted SDK plus ordinary RF2 control flow.

Return strict JSON with exactly one key `source` containing complete main.flow.
No explanation, test outputs, shell commands or claims that you ran anything.
