# RF2 app SDK: start here

This is a development SDK for trusted Mac ARM64 programs, not portable or fully memory-safe source. The compiler accepts `.flow`; `./rf2c main.flow app --compact --opt` then `codesign -s - app` produces a standalone native program. No Node/Python runtime is needed for that program. All imports resolve from the entry directory; imported names share a namespace. Each source file begins with `module name` or the entry's `profile RF2_SYSTEM_A64_V1`.


If a native `./rf2-doc` is supplied, prefer `./rf2-doc symbol [symbol ...]` for the exact signature, contract and source location; `./rf2-doc --list` lists 29 reviewed cards. It reads no files and runs no application code. The records_read card explicitly describes an intrinsic, not a source-defined function. Batch independent card queries in one call. Start with this guide and targeted cards; the supplied SDK contracts are starting interfaces, so implementation inspection is needed only when a missing detail or failing test calls for it. Inspect only the needed source function when a contract is unclear; dumping entire libraries adds context without implementing the app. SIGNATURES.md is the full source-extracted fallback. More context is not a substitute for a failing test.

## Language essentials

Current compiler limits matter: at most 8 function parameters, so group related values in a declared record; record locals must be declared directly in the function body; result functions need a final root return even if nested branches return. The compiler never overwrites an existing output. For a rebuild use a fresh output name, sign it, then replace your prior build only after success. These are existing constraints, not syntax errors to work around by changing data semantics. The frozen trials retain the repair cost of discovering them; this final guide adds the missing reminders.

Unsigned 64-bit integers, `let x=0`, `set x=x+1`, `if`/`else`/`end`, `while`/`end`, `fn name(args)`/`end`. No `%` or `break`: remainder is `n-(n//d)*d`. `&` and `|` evaluate both operands; `all(a,b)` / `any(a,b)` short circuit. Reusing local names in different `handle` arms can fail; use distinct names. Declare record locals directly in the function body, before branches, then set their fields. Calls are not object methods.

`result IO(u64,u64)` and `record Writer(data:u64,capacity:u64,used:u64,error:u64)` are imported by the SDK. A result function ends with `return ok(value)` or `return err(code)`. Direct `return operation()` now forwards the same nominal scalar result through ordinary cleanup. It must be the whole call, not an expression; structured or owned results still need explicit ownership handling. Explicit handling:

```flow
handle operation()
ok value
 # use the success value
err failure
 return err(failure)
end
```

New scalar statement shorthand in an IO function: `let n=try operation()`, `set n=try operation()`, `do try operation()`. It propagates the same nominal IO error through ordinary cleanup. It is a whole statement, not an expression, argument, record field assignment, or structured/owned result. A top-level untyped `main` must still handle the final result. Owned rows use explicit `handle ... / ok own rows:Bookings / err ... / end`; don't copy owners. Local owned cleanup runs on ordinary returns, not exit/traps/signals. Raw systems pointers remain trusted.

## Bytes and output

`buffer("unique_name",capacity)` is zeroed static storage, not a fresh allocation per call. `io_size(pointer)` counts a zero-terminated string. `load64(argv+index*8)` gets an argument. `io_copy(dst,src,bytes)` copies exactly bytes. Buffers must be large enough.

`Writer(buffer("unique",65536),65536,0,0)` is an output object. `writer_reset(out)`, `writer_text(out,zero_terminated)`, `writer_number(out,unsigned)`, `writer_bytes(out,pointer,bytes)`, `writer_json(out,pointer,bytes)` (includes quotes), `writer_html(out,pointer,bytes)` (escapes text). Check `out.error` before output; print with `do try io_write_all(1,out.data,out.used)`. Never emit a success before storage succeeds.

`text_parse_u64(pointer,length,max):IO` admits canonical unsigned decimal. Call with a supplied max; enforce positive IDs separately. Format errors return22; numeric overflow or exceeding max returns75. Map both to your application’s input-error code when its interface requires22. `date_parse(ptr,len):IO` accepts exact YYYY-MM-DD and returns numericYYYYMMDD; `date_ordinal(key):IO` returns Gregorian ordinal; `time_parse(ptr,len,allow_end):IO` returns minutes (allow_end=1 admits24:00). `date_format(out,key)`, `time_format(out,minute)` render; `ui_date_key(ordinal)` reverses a day ordinal.

## Booking domain and persistence

Import `lib/store.flow`. `StoreRequest(action,expected,id,room,day,start,finish)` actions:0list,1init,2reserve,3cancel. `StoreState(revision,bytes,version,tail,digest,committed,result)`.

`store_configure(max_journal_bytes):IO` before first operation, explicit1 MiB..16 MiB; default1 MiB. For full256-row task history choose4194304. Configuration freezes on the first store_execute/store_view, even failure; later changes return16. Every process opening a larger journal must select a sufficient budget; an older/default1 MiB reader safely refuses larger files. This is a bounded snapshot journal, not a general unbounded DB or compactor.

`store_operation(path,request,out):IO` writes JSON state to Writer; `store_execute(path,request,out,state):IO` also fills observed state. Domain rejects overlaps/stale409, duplicate17, missing row404, invalid22, busy35, capacity27, corrupt9001, uncertain save9002. Missing **file** is native2: application CLI may map2 to404 as specified. Do not turn uncertain saves into success. Journal bytes/schema/hashes/locking are private; do not rewrite them.

`store_view(path,state):StoredRows` returns `ok own rows:Bookings` after closing its descriptor. `Booking(id,room,day,start,finish)` and `records_read(rows,index,row):IO`; `rows.length`; row fields are unsigned. Example:

```flow
let state=StoreState(0,0,0,0,0,0,0)
let row=Booking(0,0,0,0,0)
handle store_view(path,state)
ok own rows:Bookings
 let i=0
 while i<rows.length
  do try records_read(rows,i,row)
  # render row; owner stays in this arm
  set i=i+1
 end
err load_error
 return err(load_error)
end
```

## Browser foundation

Import `lib/app-server.flow` and `lib/ui.flow`. Implement `app_dispatch(fd):IO`. `app_request_budget(0):IO` explicitly serves until terminated; default4096 processed connections. Budget freezes when serve begins. `app_serve():IO` binds private loopback/ephemeralport and prints URL. Existing8connection, bounded request/read/close deadlines remain. This isn't a public production HTTP server.

Call `do try form_session()` before serving: it creates the unpredictable token. The server calls `form_request(fd)` before dispatch; it validates bounded HTTP framing, Host and POST Origin, but the app must enforce routes/fields. Dispatch: `load64(globals()+8)` is1GET/2POST; target is zero-terminated `buffer("app_target",32)`; body pointer/length are `load64(globals()+16)` / `load64(globals()+24)`.

Declare `let values=FormValues()` in function scope. `form_parse(body_ptr,body_len,allowed_bitmask,values):IO` returns seen-bitmask, refuses duplicates/unknown/unallowed fields/invalid token. Each field key k uses values[k*2] pointer and values[k*2+1] byte length. Keys:0token,1rev,2action,3date,4start,5end,6name,7id,8source,9data,10room,11appearance. Preferred admission: `let mask=try app_form(fd,allowed,values)` then `if mask==0 / return ok(0) / end`. Zero means a400/403 rejection response was already sent: never execute a storage action. Transport failure returns an IO error. A nonzero value is the parsed field mask, with values retained for business-error redisplay. The lower-level form_parse does not send HTTP status on its own. Always require the exact mask for each action: reserve1215, cancel135. Both include token/rev/action. `form_hidden(out,revision)` writes token/rev inputs. Use parser return to check action-specific completeness before storage. Preserve values on failed reserve. Rendering helpers: `ui_begin(out,title)`, `ui_end(out)`, `ui_notice(out,error_code,saved_boolean)`, `ui_stat(out,label,numeric_value,detail)`, `ui_input(out,name,label,kind,value_pointer,bytes,hint)`, `ui_response(fd,out,status)` (HTML), `app_bad(fd,status)` (safe error). These return scalar; `ui_response` returns1 on sent,0 on transport failure. Library state is trusted private process state, not portable HTTP API.


## Reusable read-only MCP

Import `lib/mcp.flow`. Implement `fn mcp_execute(out:Writer):IO` to write a single valid JSON object for the one launch-selected workspace. Store its selected path in your own private buffer at startup. Call `mcp_serve(server_name,version,tool_name,description):IO` from the mcp CLI branch. It handles legacy2025-11-25 initialize/initialized, ping, tools/list and tools/call over newline JSON-RPC; exactly one explicit-empty-argument read-only tool. Unknown tool/arguments are protocol errors; callback failures are isError tool results.65536-byte lines; output object≤65536bytes; UTF8/duplicates/depth checked; notification never invokes callback; no path/source/network argument is accepted. Callback effects are the application author's responsibility: review it as read-only. Existing broader Booking agent and nine Core tools are unchanged. This helper is a bounded subset, not a general MCP framework or modern-protocol claim.
