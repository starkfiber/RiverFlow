# 28. One owner, visible cleanup failures

A short program is useful only when its failure behavior is understandable. The previous release could defer a close, but the file descriptor remained a copyable integer and a failed cleanup could disappear. Release 0.15 adds a checked owned-file path with visible error outcomes.

## Open into an owner

```rf2
result IO(u64,u64)
resource File(IO)
array Bytes(u8,16)
fn inspect(path):IO
 own file=File(path,0,0)
 let data=Bytes()
 let count=0
 handle read_owned(file,data,16)
 ok n
  set count=n
 err cause
  return err(cause)
 end
 return ok(count)
end
```

The constructor opens the file internally. An owner exists only after successful acquisition. Open failure immediately returns an error through the function's cleanup epilogue; earlier owners still receive their cleanup attempts. The owning function must declare the same result type as the resource.

An owner cannot be copied into an ordinary local, returned, placed in a record or passed to another function. It exposes no descriptor property. The checked I/O operations borrow it for one call and return a typed result. Byte counts above the array capacity return an error without issuing the operation. Short and zero I/O remain outcomes the caller must handle.

This initial resource form implements files opened through the platform interface. It is not arbitrary destructors, heap ownership, transferable handles or an async lifetime system. Helpers can still format and parse borrowed arrays without receiving ownership.

## Consume once, preserve the important error

Explicit release returns a handled result and consumes the owner on success or failure. Automatic cleanup is disarmed before the close attempt. A later source use refuses. Branch consumption is conservative; repeated execution of a release in a loop has a runtime guard, so it cannot close a descriptor that has since been reused.

If the function returns normally without explicit release, its epilogue attempts close in reverse registration order. A failed automatic close changes an otherwise successful result into err(65536+errno). A primary error is preserved, and only the first cleanup failure is reported. Legacy deferred closes retain their old best-effort behavior.

A failed close is not blindly retried: the numeric descriptor may have been reused. Trusted raw operations remain available and can deliberately violate the checked ownership contract. Fatal process traps, explicit exit and signals also bypass ordinary epilogues. These limits prevent a finite checked feature from being mistaken for total process isolation.

## Read a real file as bytes

The native hex application accepts a named read-only input and prints fixed rows: offset, hexadecimal bytes and an ASCII gutter. It uses owned acquisition and typed reads, and it handles short output writes explicitly. Tests compare every output byte with an independent formatter, including all 256 byte values and incomplete final rows. Input is unchanged.

In-process checks examine descriptor reuse after successful processing, a read error and an output error. Separate ownership probes perform actual writes followed by reopened readback, force cleanup errors, preserve primary errors and repeat hundreds of lifetimes. These are executed software fixtures, not a claim about all operating-system failures.

The byte reference lists every ASCII code with decimal and hexadecimal forms. RF2 already supports hex literals, bitwise work, native machine-code emission and useful file applications. That does not mean every Java, Python, C++ or assembly workflow is complete. Growable data, floating point, concurrency, more targets and a broader library remain foundations to build and qualify.

## Test the right layer

Agents wrote independent ownership and application probes. WhatIF separately checked a disposable Studio instance with bounded HTTP requests and verified the evidence. Its source heuristic did not parse RF2, and HTTP success does not prove compiler ownership. Each observation belongs to the layer actually tested.

The public capability map, contracts and release receipts make that distinction visible. No new speed, token, energy or hardware advantage follows from this chapter. Next are transferable ownership, richer error data and growable storage, with reproducible applications and failures as their acceptance gates.
