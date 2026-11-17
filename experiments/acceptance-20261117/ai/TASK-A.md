# Complete task A: Line metrics

Build one native `main.flow`: `app json|html PATH` (exactly two arguments).
Read only that selected regular file with `io_regular`, max4096bytes, using a4097byte
input buffer. Validate strict UTF8/C0 with text_measure. Invalid args/mode/file/
text fail nonzero with no stdout. No filesystem writes, process/network operations
or raw platform calls. Emit one complete report using a32768byte Writer; check
its error before checked io_write_no_sigpipe. Output failures return nonzero.

Title is `Line metrics`. Exact ordered fields:
- `Path`: text, exact supplied path argument.
- `Lines`: u64, TextInfo.lines (LF-delimited, final unterminated line counts;
  empty file0, no phantom line after trailing LF).
- `Words`: u64, TextInfo.words (only ASCII TAB/LF/CR/space delimit words).
- `Longest bytes`: u64, maximum line byte length,0for empty file. Exclude LF
  and the CR immediately before an LF; retain CR on an unterminated last line.

Use text_next_line with caller-owned TextCursor/TextSpan; check cursor.status.
For both conditions the output contract is the same:
JSON `{"title":"Line metrics","fields":[{"name":"Path","value":"..."},{"name":"Lines","value":0},{"name":"Words","value":0},{"name":"Longest bytes","value":0}]}` plus LF.
HTML `<!doctype html><html lang="en"><meta charset="utf-8"><title>Line metrics</title><main><h1>Line metrics</h1><dl><dt>Path</dt><dd>PATH</dd><dt>Lines</dt><dd>N</dd><dt>Words</dt><dd>N</dd><dt>Longest bytes</dt><dd>N</dd></dl></main></html>` plus LF.
Escape text with writer_json/writer_html as appropriate, preserving numeric values.
Use only documented functions. Return JSON exactly {"source":"complete main.flow"}.
