# 30. Retain more data, return a useful report

Larger applications need collections that can grow and results that can carry more than one number. Release 0.17 adds bounded byte vectors and small record-valued success results. Both have narrower contracts than a general heap or a generic type system.

## Grow within a declared reservation

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

The vector reserves its declared maximum virtual span with no access permissions. Length and logical capacity begin at zero. Reserve enables a writable prefix and commits capacity after success; append grows capacity within the maximum before writing a checked byte. Clear resets length while retaining capacity. The mapping address stays stable.

This is reservation-backed growth, not relocating malloc or an unlimited heap. OS permissions are page-granular, while checked indexing uses logical length. A successful permission change does not prove physical memory residency or guarantee later behavior under memory pressure.

The owner cannot be copied, passed or returned. Explicit release consumes it, and ordinary function cleanup unmaps the full reservation. Cleanup errors follow the owned-file result protocol. Fatal traps, signals and deliberate raw systems interference retain their existing exclusions.

An agent found an actual lifetime bug: a loop could index a released vector on its next iteration even though the source index appeared before release. Runtime armed checks now cover indexing and all properties. The retained program produces a controlled bounds error rather than dereferencing unmapped storage.

## Return values, not frame pointers

```rf2
record Stats(bytes:u64,lines:u64,zeros:u64,fingerprint:u64)
result Report(Stats,u64)
fn make():Report
 let stats=Stats(3,1,0,42)
 return ok(stats)
end
```

Success records have one through four scalar fields; errors remain unsigned scalar codes. Fields are copied into return registers before the function frame ends, then copied into the handler's frame. The callee's local address does not escape.

The success arm names its exact type with ok summary:Stats. That payload is immutable and visible only inside its arm. Scalar fields can be passed to helpers, but the whole payload cannot be passed to a helper that could mutate it. Returning it again makes another value copy. Cleanup preserves all payload registers.

This does not provide nested records, generic containers, pointer ownership or arbitrary structured errors. Owned acquisition still uses scalar IO results. A public report function may call an IO helper that fills a borrowed record, then return the completed record by value.

## Use both in a document tool

The buffered byte audit reads an explicit file into growing storage, then traverses the retained bytes. Its report contains bytes, lines, NUL count and an FNV-1a64 fingerprint. The fingerprint is noncryptographic. The input limit is one MiB; an extra byte produces an error rather than a truncated success. Input remains unchanged.

Tests compare complete reports with an independent byte-counting and fingerprint implementation, including binary data, malformed UTF-8, empty files, chunk boundaries and limits. Separate probes cover result lifetime, nested calls, immutability, cleanup and frame boundaries.

Controlled instruction patches exercise reservation, protection and unmap error paths in disposable binaries. They test response to injected errno/carry states, not actual kernel OOM. Prior contents and logical metadata remain unchanged after a failed growth attempt. The evidence does not claim physical-memory measurements or complete allocator proof.

## Invite a useful second opinion

The accompanying roadmap compares selected pinned CPython, OpenJDK and LLVM sources. It separates language semantics, compiler, runtime, libraries, tooling and target support. It is an independent task in the same AI-assisted session, not a separate provider or human audit.

A copyable external-review brief asks another AI to record revisions, reproduce failures and preserve expected results before proposing patches. Next gates include a typed compiler representation, richer data and numerics, ownership transfer, libraries, concurrency and more targets. No universal compatibility, speed or token-saving conclusion follows from this release.
