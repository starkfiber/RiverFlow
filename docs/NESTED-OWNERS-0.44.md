# Recursive owned values and structured rows, candidate 0.44

The [isolated native candidate](../experiments/nested-owned/README.md) now implements recursive inline ownership, selected-subtree moves and distinct nominal collections of flat scalar records. It builds on the actual 0.43 function-boundary ownership code. Published downloadable binaries remain unchanged.

| Executed check | Result |
| --- | --- |
| New nested-value and structured-row suite | 452 assertions passed in default and optimized modes |
| Independent in-memory Booking model | 320 generated workload outputs matched; included in the 452 assertions |
| Prior function ownership suite | 432 assertions passed |
| Prior text/aggregate suite | 460 assertions passed |
| Borrowed application values | 687 assertions passed |
| Heap adversarial controls | 78 passed |
| Complete compiler self-generation | Same signed executable bytes as the frozen native compiler produced |
| Existing MCP runtime | Unchanged binary and previous nine-tool contract; preceding handshake/status, Systems-refusal and compact-sum receipt retained |

These controls ran on one Apple Silicon Mac. Source identities and raw-result fingerprints are in [the receipt](NESTED-OWNERS-0.44.json). They do not establish cross-platform readiness, physical hardware operation, human usability, universal safety, faster execution or lower model bills.

## What changed

An owned record can contain an earlier owned record, including its own owned text/collection fields. Recursive frame layout, leaf cleanup registration, construction, scalar-path access/update, move-consumption checks, function parameters, caller-owned results and cleanup traverse that tree. Transferred descriptor pointers refer to destination storage. Moving a leaf or subtree consumes it and leaves other branches available. Moving an ancestor with an already moved descendant refuses.

A separate structured-row collection declaration names its plain nominal row type. Push/read/set/remove/reserve/clear operate on complete rows. Properties count records rather than internal words. Row admission requires 1..16 u64 fields and no borrowed or owned descendants; collections of arbitrary pointer-bearing values are **not** implemented. Input row copies do not alias the collection. Read and mutation bounds checks precede their writes. Allocation and old-mapping retirement failures preserve the existing row count/content and retryable pending state; only a successful reserve is followed by the pushed-row commit.

A native in-memory Booking app combines returned nested Calendar ownership with these row collections. Its shared business module distinguishes rooms and Gregorian day ordinals, allows adjacent half-open bookings, rejects overlaps, validates room/time/day ranges and rejects duplicate identifiers in scan order. The independent Python oracle checks supplied/generated requests. Generated scenarios are test inputs, not customer reservations or a production trial.

## Failure tests and corrections

The initial recursive expression selector called a record lookup even for scalar ID zero because bitwise Boolean operands evaluate eagerly. A guarded helper now handles scalar IDs explicitly. The source-layout cache includes all permitted nominal IDs. Initial direct ownership admission omitted the new structured-row collection kind; explicit admission and cleanup-kind mapping corrected it. Existing immutable descriptor diagnostics remain compatible.

The first new allocation-fault control also had an incorrect no-fault expectation: two successful pushes produce two rows, whereas failure followed by retry produces one. The controller now checks `2 - failures` and retains both the normal and injected controls. This was a test-oracle correction, not a product-performance improvement.

In-process disposable-image observations confirm retirement of all three nested heap mappings after a whole-tree move. Injected first-drop failure checks peer cleanup and retained-child retry at an owned handler boundary. Separate growth controls test failed initial allocation, unchanged rows on retirement failure, owner move with pending state and successful retry. Tests exercise 29 nested record levels, 1/2/8/16-field rows, declared collection limits, output failure and refused oversized layouts. Faults affect only labelled test images; no host OOM or hardware failure is claimed.

## What is still open

Typed file persistence, schema migration, crash/uncertain-save recovery and simultaneous multi-room transactions are **not implemented by this in-memory app**. The published single-room GUI is unchanged. The polished shared UI, bounded Booking agent interface, package promotion and matched complete-development comparison remain open on the fixed [delivery checklist](PROGRESS.md).

Existing bounds are explicit: 32 nominal types including compiler helpers, 16 fields/record, eight parameters, 256 local slots and 16 registered leaf cleanups/function. A row collection is limited to 65,536 u64 words. Type declaration order prevents ownership cycles. Row values are scalar records only; borrowed nested records retain their earlier separate representation. Owning file fields, arbitrary destructors, pointer-bearing row collections, concurrency, panic/signal cleanup and a whole-language borrow/safety proof remain unimplemented. A persistent OS unmap refusal can retain memory until process exit. Raw Systems operations can bypass checked contracts. No new MCP authority is granted.
