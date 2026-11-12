# Growable byte vectors and structured results, 0.17

This release adds bounded growable byte storage and small record-valued success results in the trusted native systems compiler. The nine bounded MCP schemas and effects remain unchanged. It does not add general heap allocation, ownership transfer, generic collections or universal target support.

## Reservation-backed growth

```rf2
result IO(u64,u64)
vector Bytes(IO,1048576)
fn build():IO
 own data=Bytes()
 handle buffer_push(data,65)
 ok length
 err cause
  return err(cause)
 end
 return ok(data[0])
end
```

A vector declaration takes a scalar/scalar IO result type and a canonical positive decimal maximum from 1 through 1048576 bytes. Hex/leading-zero/oversized literal spellings refuse. The constructor reserves that maximum virtual span with anonymous mmap and PROT_NONE. Logical length and capacity start at zero. The mapping address does not relocate during growth.

`buffer_reserve(data,n)` enables a read/write prefix through mprotect and commits logical capacity only after success. It returns ok(current capacity), never shrinks, and returns err22 above the declared maximum. `buffer_push(data,byte)` validates 0..255, grows capacity geometrically (initial 16 clamped to the maximum), then writes and increments length. It returns the new length. Invalid byte/limit requests leave contents, length and capacity unchanged. `buffer_clear(data)` returns ok 0, resets length and retains capacity. `buffer_get(data,index)` returns ok(byte) or err34 outside logical length. These operations require exhaustive IO handlers. The four buffer operation names are reserved native intrinsics; older functions/types using those names must be renamed.

Properties `.length`, `.capacity` and `.limit` are scalar metadata. `data[index]` reads a byte with logical-length bounds; no direct element assignment is supported. A bad direct index or a runtime read after release traps with RF2 bounds/status2. Copying/passing/returning the owner, raw pointer extraction, scalar coercion and views of a vector are not supported. The existing live-view mutation/call restrictions remain.

OS protections are page-granular and may cover more than the logical capacity. The reservation is not a claim that physical memory is committed or resident, and mprotect success does not guarantee future memory-pressure behavior. No relocating malloc/realloc or unbounded heap is claimed. The API is useful bounded growth over a stable address reservation.

## Lifetime, errors and checked state

Vectors use function-local ownership and share the 16-registration/256-local-slot budgets with owned files and legacy defers. A vector occupies one named slot and four hidden descriptor slots. `release(data)` disarms before munmap and consumes the source binding; an explicit release error is positive errno. Automatic cleanup unmaps the full declared reservation and uses the existing err(65536+errno) protocol after an otherwise successful result, preserving a primary error. Fatal process paths and raw systems interference remain outside this contract.

A real defect was found during adversarial testing: static consumption alone allowed a loop to index a released vector on a later iteration, causing SIGSEGV. Runtime armed checks now guard direct indexing and every property as well as mutation/release operations. The retained case now produces a controlled bounds error. This is a specific corrected defect, not a whole-language safety proof.

mmap/mprotect/munmap failure paths were tested by exact instruction patches in disposable signed binaries, with original words, offsets and hashes recorded. The injected errno/carry state is a controlled fault, not an actual kernel out-of-memory observation. Growth-failure tests preserve prior logical length, capacity and data. They do not claim atomic kernel page-protection changes or direct measurement of physical release.

## Record-valued success results

```rf2
record Stats(bytes:u64,lines:u64,zeros:u64,fingerprint:u64)
result Report(Stats,u64)
fn make():Report
 let stats=Stats(3,1,0,42)
 return ok(stats)
end
```

The success payload may be a previously declared nominal record of 1..4 scalar u64 fields. Error payloads remain u64. Arrays, views, owners, vectors, nested records and larger records cannot be result payloads. A structured return uses a local/borrowed record value; it copies its scalar fields into result registers before the callee frame ends. It does not return a pointer into that frame.

A structured success arm requires an exact nominal annotation:

```rf2
handle make()
ok summary:Stats
 do print_count(summary.bytes)
err cause
 return cause
end
```

The handler copies register values into its own frame before arm code runs. The binding and fields are immutable and arm-scoped. Passing the whole payload to a mutable record helper refuses, including through parentheses; passing scalar fields is allowed. `return ok(summary)` may copy it by value into another compatible result. Mutating an original source record after return does not change the copied payload.

The native internal ABI is tag x0 and up to four scalar fields x1..x4. Cleanup preserves the complete payload. Existing scalar results keep their x0/x1 protocol. This is not a general foreign-function ABI or deep ownership of pointers stored as raw u64 values.

Owned files/vectors still require scalar IO result types. A structured public function can call a scalar IO helper that fills a borrowed Stats record, then return that record by value. There is no generic implicit error conversion from scalar IO into arbitrary structured results.

## Real application and evidence

`rf2-buffer-audit file` loads a named read-only file, then inspects the retained bytes in a second pass. It returns bytes, lines, NUL count and a noncryptographic FNV-1a64 fingerprint as a four-field record. It handles a 1 MiB input, rejects an extra byte with error 22, and closes/unmaps on ordinary result paths. [Exact app contract](../examples/buffer-audit/README.md). Buffering is not claimed faster or more memory-efficient than a streaming summary.

Final targeted checks: 94 vector probes, 120 structured-result probes and 210 app checks across default/optimized builds. The vector count includes agent-authored probes and added canonical-limit refusals. These are finite local software tests, not human review or general allocator/security proof.

[Vector receipt](VECTOR-0.17-VERIFICATION.json) · [Result receipt](STRUCTURED-RESULTS-0.17-VERIFICATION.json) · [App receipt](BUFFER-AUDIT-0.17-VERIFICATION.json) · [Release qualification](RELEASE-0.17-VERIFICATION.json).

[Second opinion and roadmap](SECOND-OPINION-ROADMAP.md) compares pinned primary CPython/OpenJDK/LLVM sources. [External review brief](EXTERNAL-REVIEW-BRIEF.md) is ready for another AI/provider to reproduce and challenge the repository. No external provider was contacted and no competitor benchmark or parity claim was invented.
