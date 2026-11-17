# Passage Desk RF2 starting package

Use the supplied native Mac ARM64 `./rf2c`, shared `sdk/` directory and `.flow` source. The package is source used at compilation, not a runtime. No Python/Node is needed by the native application. No app entry, report assembly or renderer is supplied.

Build to a new output (the compiler refuses an existing output):

```
./rf2c main.flow app --compact --opt --sdk-root "$PWD/sdk" --diagnostic-json
codesign -s - app
```

For a rebuild use a fresh name, sign it and replace your old app only after success. `./rf2c --check main.flow --sdk-root "$PWD/sdk" --diagnostic-json` checks without creating an image. Structured error stderr is one `rf2.diagnostic.v1` object with code, original message, hint and source location or null; source columns are bytes. Ordinary successful stdout is not JSON. Paths use the documented escaped-byte representation; ASCII paths read normally.

## Language essentials

The entry begins with `profile RF2_SYSTEM_A64_V1`. Import exactly the single module permitted by the condition: `use "@rf2/v1/text.flow"` for MANUAL, or `use "@rf2/v1/text-report-cli.flow"` for CLI. No mcp.flow import is permitted in these tasks. Dependencies are included automatically from the selected package. Imported names share a global namespace; do not define imported functions/types again. Local `use "helper.flow"` still resolves from this application's entry directory. No import search/network download occurs. Trust this supplied package; do not modify it or its manifest.

`fn name(args)` / `end`, unsigned u64 scalars, `let x=0`, `set x=x+1`, `if` / `else` / `end`, `while` / `end`, `return value`. Functions are not object methods. Parameters are immutable. At most eight parameters per function; group related values in a declared record if necessary. Declare record locals directly in the function body, outside branches. Result functions require a final root-level return even if nested branches return. No `%` or `break`; remainder is `n-(n//d)*d`. `&` and `|` eagerly evaluate both sides; `all(a,b)` and `any(a,b)` short circuit. Use distinct binding names in handle arms. Strings are UTF-8 with escaped quotes/backslashes/newlines. `load8(ptr+i)` reads one byte; `load64(argv+index*8)` reads an argument pointer. `io_size(ptr)` counts NUL-terminated bytes.

`result IO(u64,u64)` is provided. In an IO-returning function, `let n=try operation()`, `set n=try operation()`, `do try operation()` propagate the same nominal scalar result through ordinary cleanup; direct `return operation()` also forwards that result. These are statements, not arbitrary expression/argument forms. Untyped `main` must handle a result explicitly:

```flow
handle operation()
ok value
 # scalar success
err cause
 # scalar failure
end
```

Typed result returns are `return ok(value)` / `return err(code)`. Main returns a numeric process status. Do not use `exit` as a substitute for ordinary handled cleanup. This is trusted Systems source, not a complete memory-safety sandbox.

## Shared text/byte helpers

`buffer("unique_name",capacity)` is process-static zeroed storage, not a fresh allocation per call. Reusing a named buffer returns the same memory. These two tasks require a 4097-byte input buffer and an io_regular limit of4096; the library maximum is1MiB. Use the task-specific limit, not the library maximum.

- `io_regular(path, data, limit):IO`: bounded regular-file read, final-component no-follow and nonblocking admission, limit at most 1 MiB. Returns byte count; failure is an IO error. Parent paths are trusted. No implicit decoding.
- `TextInfo(status:u64,scalars:u64,lines:u64,words:u64)`. `text_measure(p,n,info)` validates strict UTF-8/C0 controls and fills metrics; `info.status==0` is success. Its exact definitions match TASK.md. Unicode code points, not graphemes.
- `TextPrefix` is a fixed u64 workspace array; construct `let prefix=TextPrefix()` in function scope.
- `TextMatches(status:u64,count:u64,first:u64,last:u64)`. Construct `TextMatches(0,0,0,0)`.
- `text_search_overlapping(p,n,q,m,fold,prefix:TextPrefix,out:TextMatches)` accepts input at most 1 MiB and query 1..128 bytes. Pass fold=0. Returns 1 and sets out.status=0 on success; invalid bounds return0 without altering output/workspace. Validate text/query and check the returned success. Matches overlap. Absent first/last offsets are internal u64-max sentinels; convert to JSON null using count==0. Do not emit that sentinel as a JSON number.
- Existing `text_search` counts nonoverlapping matches; it is not the task's search function. `text_equal(a,n,b,m)` compares exact bytes and lengths.

## Output

`Writer(data:u64,capacity:u64,used:u64,error:u64)` is a borrowed output record. For example `Writer(buffer("unique_output",32768),32768,0,0)`. Reset before reuse with `writer_reset(out)`. Methods are global functions:

- `writer_text(out,zero_terminated_text)` appends a string.
- `writer_number(out,u64_value)` appends canonical unsigned decimal.
- `writer_bytes(out,pointer,length)` appends exact bytes.
- `writer_json(out,pointer,length)` appends a complete quoted/escaped JSON string.
- `writer_html(out,pointer,length)` appends escaped HTML text.
- Inspect `out.error` before publishing; then `io_write_all(fd,out.data,out.used):IO` handles short writes. Stdout is fd1; stderr fd2. Build the complete result before writing it. File/read/validation errors must not publish a partial success. Transport output errors can leave already-written bytes.


Checked output: io_write_no_sigpipe(fd,p,n):IO is available. Handle or try only inside IO functions.
TextSpan(start:u64,length:u64), TextCursor(next:u64,line:u64,done:u64,status:u64) are provided.
Initialize each with zero fields at function body root. text_next_line(p,n,cursor,span)
returns1for next line,0for finished/error; inspect cursor.status. It excludes LF and
CR immediately before LF, not an unterminated final CR. No phantom trailing line.
ALL record locals must be directly in the function body, before entering branches/handle.
No arrow return syntax, no scalar :u64 annotations, no io_args. main(argc,argv) supplies args.
Only functions declared :IO can use try. Plain writer/report helpers return scalars; use do.
Ordinary function statements require do. No invented APIs, recursion, raw platform operations.
NATIVE-ADMITTED COMMON SYNTAX (not a task solution):
profile RF2_SYSTEM_A64_V1
use "@rf2/v1/text.flow"
fn byte_count(path):IO
 let data=buffer("style_data",4097)
 let info=TextInfo(0,0,0,0)
 let n=try io_regular(path,data,4096)
 do text_measure(data,n,info)
 if info.status
  return err(info.status)
 end
 return ok(n)
end
fn main(argc,argv)
 if argc!=2
  return 2
 end
 handle byte_count(load64(argv+8))
 ok value
  return 0
 err cause
  return 2
 end
 return 2
end

# Report composition source API

Use `use "@rf2/v1/report.flow"`; dependencies include text and IO. No runtime
installation. This is one explicit candidate SDK supplied by the controller.
Do not redefine its records/functions. `Report(format:u64,fields:u64,state:u64)`:
construct `let report=Report(0,0,0)` and a Writer once per output, directly in the
function body. `report_begin(report,out,format,title,n)` opens the report; format0
JSON,1HTML. `report_text(report,out,name,n,value,m)` adds typed text;
`report_number(report,out,name,n,u64)` adds a number; `report_end(report,out)`
closes with LF. Use `do` for these calls, then check `out.error` before publishing.
Title, labels, values use explicit byte lengths; no implicit UTF8 or pointer length.
The writer owns no memory: caller supplies buffer/capacity, checks error and writes
through IO. State/refusal/capacity errors are sticky; no partial success is published
by a conforming caller. Up to1024fields, text at most1MiB, subject to caller output
capacity. UTF8/C0 validation and JSON/HTML escaping are library operations. It
emits the exact task's JSON/HTML shapes including typed array fields. No file read,
format detection, text counting or I/O is hidden inside the report API. Names
report_field/report_field_end are internal composition helpers, not app APIs;
do not mutate Report fields yourself or invent higher-level capabilities.

# Shared text-report CLI source SDK

Import `@rf2/v1/text-report-cli.flow`; it includes text, IO and Report dependencies.
Implement exactly `fn text_report_fields(input:TextReportInput,report:Report,out:Writer):IO`.
This callback is called once synchronously after validated input and report_begin.
Append ordered typed fields using report_text/report_number; return ok(0) or err(code).
Do not call report_begin/report_end, read files, parse args, reset Writer/Report or
write stdout in the callback. Native library owns that shared flow and checks errors.

TextReportInput's scalar fields are path (NULterminated argument), query (0when
absent, otherwise NULterminated validated1..128byte query), data (read-only input
pointer), size (byte count), format (0JSON/1HTML), lines/words (TextInfo metrics).
Use io_size on path/query, never on data; use input.size. No methods. Use existing
TextCursor/TextSpan or TextPrefix/TextMatches in callback for task-specific work.
All record locals still belong at function-body root, outside branches.

`fn main(argc,argv)` returns `text_report_entry(argc,argv,TITLE,TITLE_BYTE_LENGTH,QUERY_REQUIRED)`.
QUERY_REQUIRED0means exact `app json|html PATH`;1means `app json|html PATH QUERY`.
The library validates args/mode, bounded4096byte regular input/no symlink/FIFO,
UTF8/C0 and optional query; builds a32768byte output; handles checked output/short
writes/no-SIGPIPE with explicit nonzero failure. It adds LF and the same exact
Report JSON/HTML shapes. Title/path/text escaping stays centralized.

Trusted single-invocation Systems library with static buffers, no concurrent/reentrant
guarantee, sandbox, new Core MCP tool or arbitrary callback-effect enforcement.
Inputs/records must not escape the synchronous callback. This API removes shared
CLI plumbing; it does not calculate longest lines, search matches or invent fields.

MATCHED UTILITY TRIAL: The exact same guide is supplied in both conditions. Condition MANUAL may import only @rf2/v1/text.flow (plus its own transitive IO dependencies); it must not import the SDK Report/text-report-cli modules or copy their sources. Its own report records/helpers under any names are allowed and count as returned source. Condition CLI imports @rf2/v1/text-report-cli.flow, defines its callback and calls text_report_entry from main. It delegates common argument/file validation, output buffering/formatting and checked output to this library, but implements the complete task-specific calculation. Do not copy library source or hardcode fixture results. No task solution is provided.

## Exact common output serialization contract

Both conditions must emit identical output bytes. HTML begins exactly:
`<!doctype html><html lang="en"><meta charset="utf-8"><title>` followed by the HTML-escaped title, `</title><main><h1>`, the HTML-escaped title, and `</h1><dl>`.
For each ordered field append `<dt>`, HTML-escaped label, `</dt><dd>`, escaped text value or canonical decimal number, then `</dd>`. End exactly `</dl></main></html>\n`, where \n is one LF byte. There are no indentation, CSS, extra spaces, body element, or extra tags. Escapes are &: &amp;, <: &lt;, >: &gt;, double quote: &quot;, apostrophe: &#39;.
JSON has exactly the task's shape, unescaped UTF8 remains UTF8, and one final LF. Strings use shared writer_json; each field is {"name":quoted_label,"value":quoted_text_or_decimal}, comma-separated in a fields array, with no spaces.

Only the selected-file input is read. Use the supplied typed text/IO helpers.
No raw syscall, process execution, network, directory mutation, inline assembly, SDK modification, test fixtures, or controller execution belongs in returned code. Return a source proposal only.
