# Owned function boundaries, candidate 0.43

The isolated source in [owned-functions](../experiments/owned-functions/README.md) now transfers local text, u64 collections and flat owned records into functions and returns them through explicit owned results. Stable downloadable compilers are unchanged.

## Executed acceptance

| Check | Observed outcome |
| --- | --- |
| New cross-function qualification | 432 assertions passed across default and optimized modes; includes 280 independently checked application JSON outputs |
| Prior owned-value qualification | 460 assertions passed against this candidate |
| Borrowed application-value regression | 687 assertions passed against this candidate; qualified baseline refusal retained |
| Heap adversarial regression | 78 controls passed against this candidate |
| Self-generation | Candidate compiled its complete source into the same signed executable bytes as the frozen qualified compiler produced |
| Existing bounded MCP | Nine tool names retained; status/handshake, Systems rejection and compact sum verified |
| Fixed progress renderer | 13 controls passed; stale rendering, changed denominator and unsupported completion refuse |

These are finite developer controls on one Apple Silicon Mac. They are not human trials, independent academic review, cross-platform qualification or speed/token benchmarks. [Receipt and source identities](OWNED-FUNCTIONS-0.43.json).

The application now has a loader returning an owned Unicode label and number batch, and a renderer consuming that batch. Supplied input, malformed UTF-8, numeric overflow, closed output and length limits are exercised. Empty text, combining marks, Tamil and emoji retain scalar-based behavior. This is not grapheme segmentation or normalized Unicode.

## ABI and failure behavior

An explicit `result Ready(own Packet,u64)` uses caller-provided result storage in x8. Ownership moves there before the callee frame expires. A caller's `ok own value:Packet` arm takes responsibility. Named root registers are refreshed from the result storage before use. `fn consume(own value:Packet):IO` moves the argument into private callee storage on entry; callers write `consume(move(value))` and cannot reuse the consumed source. Result and parameter descriptors are rebased rather than copied as escaping frame pointers.

All scalar arguments are evaluated before the call; x8 is installed afterwards. Owned parameters and handler bindings participate in the same registration ordering as ordinary owners. A normal arm exit drops its owner. Early function return uses the common cleanup epilogue. If producer cleanup changes a success into an error after a result was moved, the caller drops the undeliverable result. A failed arm drop attempts other children and then retries retained ownership through the enclosing epilogue. Primary errors remain primary.

In-process test-only mapping observations confirm actual retirement after normal and early-return handler exits. Disposable images inject a first unmap failure to test peer cleanup and retry. Another control verifies undeliverable result disposal while explicitly observing a failed **callee-local** mapping retained until exit. These hooks change only disposable test images; they are not claims of actual host resource exhaustion. The retained mapping is an existing limitation, not silently called recovered.

## Failures fixed and preserved

1. The first candidate source failed compilation because two branch-local declarations shared a function-local name. Renaming the second internal counter corrected the source.
2. A root-record return initially used the field-only selector. Root and field paths now select explicitly.
3. The first optimized cross-function suite crashed: the caller's named root was kept in a register while the callee filled its stack storage. Reloading the root from that storage corrected the mismatch. The exact failed case and crash remain in local evidence.
4. Incoming parameter owners and handler-owned bindings initially lacked cleanup-registration cursor advancement. The corrected prologue and handler account for those registrations; tests also construct owners afterwards.

The final new suite, prior suites and self-generation were rerun after these changes. Source identity and failed-run hashes are preserved in the receipt.

## Remaining boundaries

This closes the explicitly bounded cross-function ownership item. It does not close nested ownership, structured collections, typed persistence, transactional multi-room Booking, polished UI, its bounded agent interface, downloadable promotion or the matched development comparison. The fixed [delivery tracker](PROGRESS.md) keeps those separate.

Owned/borrowed typed parameters cannot coexist in one signature; this conservative refusal avoids admitting unchecked aliases. Only the documented owned text/u64-collection/flat-record types are supported. Functions remain limited to eight parameters, 256 local slots and 16 cleanup registrations. Handler owner bindings are arm-scoped; returning or passing one requires `move`. Missing result ownership annotations, scalar copies, mismatched nominal types, moved values, moved aggregate children and borrowed escapes refuse before executable emission. Ordinary-return cleanup cannot guarantee retirement after a persistent kernel refusal, trap, signal, raw systems interference or process exit.

No new speed, energy, token saving, hardware or universal memory-safety claim is made. General nested ownership is the next active delivery requirement. Trusted Systems compilation remains CLI-only; MCP still exposes its earlier nine bounded tools.
