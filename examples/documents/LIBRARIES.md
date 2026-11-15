# Reusable RF2 text and collection APIs

These modules are consumed by both `workspace.flow` and `text-lines.flow`. Imports resolve relative to the entry directory. Reuse in another project requires explicitly placing the local modules under that project's import root; there is no registry or automatic global include path.

They target the trusted `RF2_SYSTEM_A64_V1` profile. Callers supply valid byte ranges and separate output records/workspaces with sufficient lifetime. Raw pointers, record aliases and deliberate syscall interference can violate these contracts. The implementation is sequential and not reentrant or concurrency-safe: named staging/formatting buffers are shared within a process. Compiler-checked collection access does not make all raw pointer operations safe.

## Text: lib/text.flow

| API | Behavior |
| --- | --- |
| `text_equal(a,n,b,m)` | Exact byte-range equality; no NUL scanning |
| `text_trim(p,n,span)` | Borrowed byte offsets excluding ASCII edge whitespace |
| `text_measure(p,n,info)` | Strict UTF-8 validation, scalar/LF-line/ASCII-word counts; status 84 for invalid text, 22 over 1 MiB; invalid results clear counts |
| `text_search(p,n,q,m,fold,prefix,matches)` | Established KMP search, O(n+m), nonoverlapping matches; count/first/last byte offsets; fold 0/1 affects ASCII A-Z only |
| `text_line(p,n,index,span)` | Random LF line lookup from start; 0-based index, CR stripped only before LF; refuses missing line without publishing a new span |
| `text_next_line(p,n,cursor,span)` | Forward iterator, linear total scan across successive calls; initial `TextCursor(0,0,0,0)`; cursor.line becomes 1-based |
| `text_parse_u64(p,n,maximum):IO` | Canonical unsigned decimal; invalid syntax 22, overflow/maximum failure 75; no sign, leading zero sequence or exponent |
| `text_decode(p,n,dst,cap):IO` | URL-form percent decoding and plus-to-space; needs room for NUL; C0/DEL reject; invalid syntax 22 or insufficient capacity 28; UTF-8 validation is a separate step |
| `text_html(p,n,dst,cap):IO` | Escape ampersand, angle brackets and both quotes for validated HTML text/attributes; returns bytes written, no NUL terminator |

Search accepts n up to 1 MiB, m up to 256 and a distinct caller-owned `TextPrefix` array. Unsupported lengths/fold values refuse before input reads. No match uses `18446744073709551615` for first/last. An empty needle matches every byte boundary, n+1 times. These are byte offsets, not glyph or screen positions. No locale rules, regex, fuzzy matching or normalization are implemented.

`text_decode` accepts at most 4,096 encoded bytes. `text_html` accepts at most 1 MiB. Their two-pass implementations validate size/syntax before destination writes, so those refusals preserve the destination. Source/destination must be disjoint and must not change between passes. This is not a concurrent or arbitrary-overlap guarantee. HTML escaping does not validate UTF-8; call `text_measure` first when accepting external text. JSON rendering requires validated text without unsupported C0 controls.

## Collections: lib/collections.flow

`Items(IO,4096)` is an existing RF2 bounded u64 heap collection. The library adds reusable operations, not a new general container type:

- `items_lower_bound(items,key):IO`: binary insertion position in an already sorted sequence. Caller must maintain ascending order.
- `items_insert_unique(items,key):IO`: insert while keeping sorted unique values; return existing/new index. Reserve/limit failures occur before shifting. No callback or concurrent mutation is allowed during the operation.
- `items_append_row4(items,row):IO`: append a `Row4(a,b,c,d)` to a flat table. Existing length must be divisible by four. Capacity preflight precedes appends; at most 1,024 rows fit.
- `items_row4(items,index,out):IO`: validate row shape/range, complete all reads, then publish the output record. Invalid index/shape returns 34 and preserves that output record.

The row API and sorted-item API use the same nominal collection, so they are separate documented conventions rather than statically distinct types. Do not apply sorted scalar insertion to an existing row table. These methods do not promise rollback after arbitrary raw mutation, allocator sabotage, fatal traps or signals. They inherit the compiler's collection growth/release/cleanup rules in [the heap contract](../../docs/HEAP-COLLECTIONS-0.33.md).

## I/O and catalogue composition

`io_regular(path,data,limit):IO` opens a Darwin regular file read-only with nonblocking/no-follow-final-component flags. The caller owns `limit+1` writable bytes; one extra byte distinguishes a full-size file from an oversized file. The function closes its acquired descriptor on ordinary success/error paths, preserves a primary error and reports a cleanup-only error as `65536+errno`. Parent directories may contain symlinks. It is not path containment, a live file lock or a general asynchronous I/O abstraction.

`Writer(data,capacity,used,error)` and its helper operations build bounded output with a sticky error. They do not grow a buffer or guarantee transactional stdout. Byte ranges and output records must not alias unexpectedly.

The catalogue combines these modules into four-u64 rows of content offset, content length, source-name offset and source-name length. The text and name arenas outlive the table and requests. HTTP requests select only row IDs; they do not acquire new files. A failed initial load may leave partial internal tables until cleanup, but the application does not publish them or begin listening. The application requires empty input tables; it does not offer transactional replacement of a previously loaded live corpus.

[Application boundaries and examples](README.md) · [Executed tests](../../docs/DOCUMENTS-0.37-VERIFICATION.json)
