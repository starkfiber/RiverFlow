# Owned rows, native candidate 0.46

Prepare from the unchanged source-pinned 0.44 compiler, then build explicitly:

```sh
python3 experiments/owned-rows/prepare.py NEW-CANDIDATE
sh tools/build-program.sh QUALIFIED-rf2c NEW-CANDIDATE/compiler.flow NEW-CANDIDATE/build --opt
RF2_OWNED_ROW_COMPILER=NEW-CANDIDATE/build/program python3 tests/standalone/owned_rows_verify.py
```

The compiler and injected runtime are RF2. Python prepares reviewed source and tests; it is not an end-user dependency. The generated compiler is self-reproducible natively.

```flow
result IO(u64,u64)
text Title(IO,256)
collection Scores(IO,64)
record Entry(title:own Title,scores:own Scores,id:u64)
collection Entries(IO,64,Entry)
result EntryReady(own Entry,u64)
```

The new collection owns complete inline row values, including recursive records and collections. `rows_push(entries,move(entry))` requires exhaustive scalar IO handling and consumes the source binding on every outcome. A successful insertion transfers ownership. A failed insertion leaves the collection's logical contents intact; the source remains armed for its existing scope cleanup when transfer did not occur. Code cannot reuse that statically consumed binding after failure.

`rows_take(entries,index)` requires an explicitly annotated owned result handler, such as `ok own selected:Entry`, and a declared result carrying that nominal row type. A successful extraction transfers ownership to caller storage, removes the row and compacts/rebases following rows. An invalid index returns error34 before changing rows or publishing an owner.

`rows_reserve`, `rows_clear`, `release` and the ordinary `.length/.capacity/.limit` properties complete the API. Clear/drop recursively attempt every child. If cleanup partly fails, row access is quarantined with error16 until clear/release finishes; partially retired rows cannot escape through extraction. Persistent kernel refusal may retain mappings until process exit. These are ordinary-return guarantees, not trap/signal recovery or a whole-language safety proof.

Use `catalog.flow` as an actual Unicode-label manifest application. Build it in a new source tree with `lib/batch.flow` from `experiments/owned-functions/examples/lib/` and `lib/numbers.rf2`, `lib/output.rf2` from `examples/collection-tools/lib/`. It validates all arguments before JSON output, stores complete owned labels/readings, transfers the catalog between functions and extracts rows for rendering. It does not modify user files. The qualified bundle includes these sources and `rf2-labels`.

Type declaration order prevents ownership cycles. The existing type/local/cleanup bounds still apply; rows are at most255 inline words and a collection at most65,536 words. Flat scalar `records_*` APIs retain their copying semantics. The new consuming `rows_*` APIs are separate. No indexed borrowed row views, arbitrary destructors, owned files in records, general FFI, concurrency, cross-platform execution or new Core/MCP effects are introduced.

[Evidence, corrections and exact limits](../../docs/OWNED-ROWS-0.46.md).
