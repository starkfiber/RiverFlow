# Task C — Log severity summary

Produce one complete native main.flow: `app json|html PATH`, exactly two arguments.
Read only the selected regular nonsymlink file, at most4096bytes in a4097byte input
buffer. Validate strict UTF8 and reject NUL/nontext C0 except TAB/LF/CR. Invalid
args, mode, file or text must return nonzero with no stdout. Build at most32768
output bytes; inspect writer errors before checked no-SIGPIPE output. Output
errors return nonzero. No other file, process or network effects.

Classify each physical LF-delimited line. A final unterminated line counts; an
empty file has zero lines; trailing LF creates no phantom extra line. Strip only
the CR immediately before LF; preserve an unterminated trailing CR. Before
classification ignore leading ASCII spaces and TABs only. An exact uppercase
severity token INFO, WARN or ERROR must then be followed by end-of-line, ASCII
space or TAB. For example ` INFO hello` is INFO, `WARN\tmessage` is WARN,
`ERROR` is ERROR, while `INFO:`, `INFORMATION`, lowercase `warn`, time-prefixed
lines and whitespace-only/empty lines are Other. Text after a valid token may be
any otherwise admitted UTF8. Do not treat other Unicode whitespace as a delimiter.

Title: `Log severity`. Exact ordered typed fields:
- Path: exact supplied path, text.
- Lines: physical line count, u64.
- INFO: count of INFO lines, u64.
- WARN: count of WARN lines, u64.
- ERROR: count of ERROR lines, u64.
- Other: remaining lines, u64.
The four category counts must sum to Lines.

JSON shape: {"title":"Log severity","fields":[{"name":"Path","value":"PATH"},
{"name":"Lines","value":N},{"name":"INFO","value":N},{"name":"WARN","value":N},
{"name":"ERROR","value":N},{"name":"Other","value":N}]} plus one LF, no extra spaces.
HTML uses the documented Report shape with title/h1 `Log severity`, a dl of the
same ordered dt/dd names and values, then one LF. Escape path through the shared
writer's JSON/HTML escaping; numbers remain numeric JSON values. Emit no banner.

Use the given condition's allowed libraries. The CLI condition may delegate all
shared input/output plumbing to text_report_entry and implement only its callback.
The manual condition must implement that plumbing with text/IO/Writer APIs and
must not import the SDK Report or text-report-cli modules. Its own report
records/helpers under any names are allowed and count as returned source. Do not include test fixtures or
controller commands. Return one JSON object with only the key source. Its value is the entire actual RF2 program text beginning with profile RF2_SYSTEM_A64_V1. Return the implementation itself, never a placeholder, description, filename or Markdown fences.
