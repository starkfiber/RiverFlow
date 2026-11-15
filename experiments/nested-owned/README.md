# Recursive owned records and structured rows, candidate 0.44

This isolated compiler extends the source-pinned [0.43 ownership candidate](../owned-functions/README.md). Prepare into a new directory, compile its generated `compiler.flow` through the qualified native compiler, then select that candidate explicitly. Published downloads remain unchanged.

```sh
python3 experiments/nested-owned/prepare.py NEW-CANDIDATE
sh tools/build-program.sh PATH-TO-QUALIFIED-rf2c NEW-CANDIDATE/compiler.flow NEW-CANDIDATE/compiler --opt
RF2_NESTED_OWNER_COMPILER=NEW-CANDIDATE/compiler/program python3 tests/standalone/nested_owned_verify.py
```

Compile-time ownership composition is recursive and inline. Types must be declared before containing types, so ownership cycles cannot be declared. Existing frame, type, field and cleanup bounds still apply. A large layout refuses rather than wrapping its slot count. A source-bound cache avoids repeatedly expanding the same bounded layout.

```flow
record Booking(id:u64,room:u64,day:u64,start:u64,finish:u64)
collection Bookings(IO,256,Booking)
record CalendarMeta(title:own CalendarTitle)
record Calendar(meta:own CalendarMeta,bookings:own Bookings,revision:u64)
result CalendarReady(own Calendar,u64)
```

`CalendarTitle` is a declared owned text type. Owned nested records may contain scalar fields, owned text, owned u64 collections, structured-row collections and earlier owned records. Borrowed fields and files inside these records still refuse. Construct, move, pass and return entire trees or selected subtrees; read and update scalar leaves through checked paths. A moved subtree is unavailable while its unmoved peers remain usable. Partially moved ancestors cannot transfer as complete values. Recursive copying rebases destination pointers and disarms source leaf ownership; it does not let stack pointers escape.

Structured-row collections have a distinct nominal kind. Their third declaration argument must be a plain flat record of 1..16 u64 fields. No row contains pointers or owned descendants. Use:

- `records_push(items,row)` copies the current row after a successful reserve.
- `records_read(items,index,out)` fills a mutable nominal row; bounds failure leaves it unchanged.
- `records_set(items,index,row)` copies an in-range replacement.
- `records_remove(items,index)` compacts following rows.
- `records_reserve(items,count)` requests capacity in rows.
- `records_clear(items)` clears logical length and retains capacity.
- `release(items)` uses the existing recoverable heap-drop protocol.

All operations return the declared scalar IO result and require exhaustive handling. `.length`, `.capacity` and `.limit` count records. Internal storage uses a bounded relocating u64 heap. At most 65,536 words, including all row fields, can be declared for one collection. Failed allocation or retirement does not commit a pushed row. The prior pending-mapping/retry contract remains. Typed borrows may be used sequentially; this is not concurrency or exclusive-alias proof.

The [in-memory Booking application](examples/booking-values.flow) reads groups of `id,room,Gregorian-day-ordinal,start-minute,finish-minute`, builds a returned nested Calendar and applies the shared [Booking rules](examples/lib/booking.flow). Build a private tree with these entry/library files and `numbers.rf2`/`output.rf2` from `examples/collection-tools/lib/`, preserving the `lib/` paths. The same original parser/output modules are reused. Invalid rows, duplicate IDs, cross-room/day independence, half-open overlaps, input failures and output failures have explicit outcomes.

**This application does not persist bookings, implement transactional storage, serve a new GUI or add a Booking MCP tool.** Those remain delivery items. [Executed evidence and limitations](../../docs/NESTED-OWNERS-0.44.md).
