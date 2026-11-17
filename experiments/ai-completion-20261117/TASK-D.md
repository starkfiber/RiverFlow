# Task D — Duplicate inventory identifier audit

Produce one complete native main.flow: `app json|html PATH`, exactly two arguments.
Read only the selected regular nonsymlink file, at most4096bytes in a4097byte input
buffer. Validate strict UTF8/C0 as documented. Invalid args, mode, file, text or
identifier must return nonzero with no stdout. Build at most32768 output bytes;
inspect writer errors before checked no-SIGPIPE output. Output errors return
nonzero. No other file, process or network effects.

Parse physical LF lines: final unterminated line counts, no phantom trailing line;
strip only CR immediately before LF, retaining an unterminated final CR. Ignore
only zero-length lines after that CRLF rule. Every nonempty line must be exactly
1..32 bytes of ASCII uppercase A-Z, digits0-9, underscore or hyphen. Do not trim,
casefold, normalize, sort or accept spaces/TAB/Unicode. One invalid line rejects
the entire file even if earlier lines were valid. IDs are exact byte identities.

Count nonempty identifier occurrences and distinct identifiers. Every occurrence
after an identifier's first occurrence counts as one duplicate occurrence.
First duplicate line is the physical1-based line number of the earliest such
repeat, including ignored blank lines in physical numbering, or text `none` when
there is no duplicate. Example `A\n\nB\nA\nB\nA` gives IDs5, distinct2,
duplicates3, first duplicate line4. An empty/blank-only file gives zero counts and
`none`. The identity IDs = distinct + duplicate occurrences must hold.

Title: `Identifier audit`. Exact ordered typed fields:
- Path: exact supplied path, text.
- Identifiers: nonempty valid identifier occurrences, u64.
- Distinct: distinct identifier count, u64.
- Duplicate occurrences: repeated occurrence count, u64.
- First duplicate line: u64 physical line number, or text `none`.

JSON shape: {"title":"Identifier audit","fields":[{"name":"Path","value":"PATH"},
{"name":"Identifiers","value":N},{"name":"Distinct","value":N},
{"name":"Duplicate occurrences","value":N},{"name":"First duplicate line","value":N_OR_"none"}]}
plus one LF, no extra spaces. HTML uses the documented Report title/h1 and ordered
dl/dt/dd shape, then one LF. Escape path with shared JSON/HTML writers; preserve
numeric versus text values. Emit no banner or diagnostic to stdout.

Use the given condition's allowed libraries. The CLI condition may delegate all
shared input/output plumbing to text_report_entry and implement only its callback.
The manual condition must implement that plumbing with text/IO/Writer APIs and
must not import the SDK Report or text-report-cli modules. Its own report
records/helpers under any names are allowed and count as returned source. No task implementation/solution is
provided by the guide. Return one JSON object with only the key source. Its value is the entire actual RF2 program text beginning with profile RF2_SYSTEM_A64_V1. Return the implementation itself, never a placeholder, description, filename or Markdown fences.
