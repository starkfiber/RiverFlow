# Passage Desk RF2 starting package

Use the supplied native Mac ARM64 `./rf2c`, shared `sdk/` directory and `.flow` source. The package is source used at compilation, not a runtime. No Python/Node is needed by the native application. No app entry, report assembly or renderer is supplied.

Build to a new output (the compiler refuses an existing output):

```
./rf2c main.flow app --compact --opt --sdk-root "$PWD/sdk" --diagnostic-json
codesign -s - app
```

For a rebuild use a fresh name, sign it and replace your old app only after success. `./rf2c --check main.flow --sdk-root "$PWD/sdk" --diagnostic-json` checks without creating an image. Structured error stderr is one `rf2.diagnostic.v1` object with code, original message, hint and source location or null; source columns are bytes. Ordinary successful stdout is not JSON. Paths use the documented escaped-byte representation; ASCII paths read normally.

## Language essentials

The entry begins with `profile RF2_SYSTEM_A64_V1`. Import exactly `use "@rf2/v1/text.flow"` and/or `use "@rf2/v1/mcp.flow"`. Dependencies are included automatically from the selected package. Imported names share a global namespace; do not define imported functions/types again. Local `use "helper.flow"` still resolves from this application's entry directory. No import search/network download occurs. Trust this supplied package; do not modify it or its manifest.

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

`buffer("unique_name",capacity)` is process-static zeroed storage, not a fresh allocation per call. Reusing a named buffer returns the same memory. The task's maximum input requires 1,048,577 writable bytes for `io_regular`'s overflow detection.

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

## Shared legacy MCP helper

Import `@rf2/v1/mcp.flow` and implement `fn mcp_execute(out:Writer):IO`. The generic helper supplies the output writer. Your callback must reset/write one valid report JSON object, use only the selected file/query recorded at launch, reread the file on each call and return IO success/error. Do not write directly to stdout inside it. A callback failure becomes a tool result with `isError:true` and no successful structuredContent.

`mcp_serve(server_name,version,tool_name,description):IO` handles the task's legacy lifecycle, one explicit-empty-argument tool, bounded lines/results, duplicate decoded keys, method/tool/argument refusals and recovery. It does not read files or implement the application callback. Store selected argv pointer values in unique static buffers before serving if needed; argv remains valid for the process lifetime. Tool notifications do not invoke the callback. This is not a general modern MCP framework or new Core effect.

Deliver `launch.json` exactly `["./app"]`. Test the actual compiled/signed image, not only compilation. The package is Mac Systems support; no other platform, physical sensor, authentication or secret-redaction qualification is implied.
