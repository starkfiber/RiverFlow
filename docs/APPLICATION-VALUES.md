# Typed application values: contract before promotion

Foundation draft, 15 November 2026. This specifies acceptance behavior for G1; it does not enable new owned fields in released compilers. The [isolated candidate](../experiments/nested-records/README.md) provides borrowed composition. The separate [owned-field candidate](OWNED-VALUES-0.42.md) now adds bounded text/collection fields and local moves, while cross-function ownership remains unimplemented. The full-platform [pipeline](PROGRESS.md) keeps these states separate.

## Current borrowed composition

A nested field points to an earlier plain record type. It aliases that record's function-local or parameter storage. It is not an inline copy and does not own the child's storage. Construction requires an initialized value of the exact nominal type. Scalar leaf updates traverse checked field names/types. The selected receiver address survives right-hand-side helper calls. Two references may intentionally alias; there is no exclusive mutable-borrow guarantee.

Child binding replacement, traversal through a scalar, missing fields, a different nominal child type, resource/collection children and borrowed-record result escape must refuse. The compiler's original type, field, local-slot and expression budgets remain in force. Plain records stay at function scope; raw pointer/syscall escape is trusted and outside the type guarantee. Default and optimized execution must agree.

The Booking conflict prototype uses the real date/time/text/I/O library snapshots and two borrowed `ReservationValue` records containing `TimeWindow` records. It validates Gregorian dates and same-day half-open minute intervals. It computes a conflict only; it neither books a room nor writes a journal. It must not be presented as the full Booking migration or owned-value support.

## Owned-value acceptance rules

The 0.42 candidate implements scoped parts of V1–V3 and V6–V9, with finite evidence linked above. It does not complete these requirements generally or satisfy V4/V5/V10/V11 as a full application-value model.

These rules are design requirements. Exact surface syntax, representation and ABI remain unapproved until a candidate implements and qualifies them.

| ID | Required behavior | Acceptance pair |
| --- | --- | --- |
| V1 | Each field states value, ownership or borrow semantics unambiguously | Construct/read a nested value; refuse an ownership-ambiguous or incompatible initializer |
| V2 | Owned text and collections are nominal typed values, never scalar addresses disguised as safe ownership | Correct typed field; refuse pointer/scalar substitution |
| V3 | Moving an owner transfers its entire cleanup responsibility once | Valid move; refuse use/release through the consumed source |
| V4 | Returning an owned value moves it across the call boundary | Returned value remains valid; returning a borrow into a dead frame refuses |
| V5 | Borrow lifetime cannot outlive its owner, and mutation permissions are explicit | Supported temporary borrow; refuse escape and incompatible concurrent mutation |
| V6 | Constructor inputs evaluate left to right exactly once; partial construction does not publish a usable aggregate | Side-effect counter agrees; inject failure at each fallible child construction |
| V7 | A failed constructor retires only successfully acquired children and reports cleanup uncertainty honestly | Each cleanup happens once; preserve primary failure and reachable retry state where needed |
| V8 | Aggregate moves and cleanup use declared layout, alignment and per-field rules | Validate generated layout/offsets; refuse unsupported recursive by-value cycles |
| V9 | Explicit copies are allowed only for copyable fields or a fallible deep-copy operation | Independent value copy; refuse implicit owner duplication |
| V10 | Serialization writes field values/schema identity, never process pointers or raw padding | Reopen/round-trip; refuse schema mismatch, truncation and malformed lengths |
| V11 | Updating a persistent aggregate has confirmed, failed or uncertain outcomes | Restart/concurrent-writer agreement; no false success after partial save |
| V12 | New lowering preserves known programs and admission rules | Default/optimized execution, ABI and source/target cache regressions; explicit versioned migration for changed behavior |

The current collection release contract can partially retire mappings and return an error. Aggregate cleanup must preserve that distinction rather than promising rollback of already released data. Fatal traps/signals, allocation refusal, cleanup refusal and ordinary typed errors require separate experiments. A digest identifies an artifact; it does not prove safety.

## Promotion checklist

- [ ] Specify the actual owned layout, ABI and surface syntax; resolve alias/copy/lifetime questions.
- [ ] Implement ownership transfer and partial-construction state in an isolated compiler candidate.
- [ ] Execute all V1–V12 acceptance pairs, including allocation/cleanup faults and default/optimized modes.
- [ ] Run existing compiler, ABI, ownership, reference, cache and MCP regression gates on the exact candidate.
- [ ] Replace one real application's manual data packing, preserving existing persistence or supplying a tested migration.
- [ ] Produce a qualified package and fresh extraction/build run before advertising general owned nested values.

Borrowed conflict tests advance one application boundary, not every checkbox. No compiler release, concurrency proof, whole-language memory-safety result or new MCP authority follows from this design.
