# Owned files and cleanup errors, 0.15

RF2 now has a noncopyable, function-local owned-file type. Acquisition, byte I/O and release are compiler operations with nominal typed outcomes. This is a checked ownership contract for ordinary RF2 file use, not a sandbox around the trusted raw systems profile.

## Acquire without exposing a descriptor

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

A resource declaration names the result type used by its file operations. The constructor opens the supplied path with explicit platform flags and mode. The owner becomes usable only on success. Open failure returns `err(errno)` immediately through the owning function's cleanup epilogue, releasing previous owners. The function must declare the same nominal result type; main calls it through an exhaustive handler. There is no raw-descriptor adoption constructor.

Owners are function-level declarations, not scalar values. They cannot be copied, assigned, indexed, inspected through properties, passed as parameters or returned. No method reveals the descriptor. Constructing with let, passing to raw intrinsics, ignoring a result and using a consumed owner are refused. The compiler does not infer permissions from a resource name: this first declaration form always implements OS open/close files. It is not arbitrary user-defined destructors or socket acquisition.

## Borrow for checked byte I/O

`read_owned(file,byte_array,count)` and `write_owned(file,byte_array,count)` temporarily use the owner and return its declared result type. Success carries the actual byte count; failure carries a positive OS errno. Counts above nominal array capacity return err22 without issuing I/O. Zero and short I/O remain explicit outcomes; a successful call does not promise all requested bytes transferred. Existing function-wide live-view call restrictions apply.

These operations do not permit moving ownership into helpers or storing it in records. Array parameters and ordinary helper functions remain available for formatting and parsing. Ownership transfer, general lifetime inference, async borrowing and concurrency remain future work.

## Release once, or let the epilogue release

```rf2
handle release(file)
ok ignored
 # file is consumed in both arms
err cause
 return err(cause)
end
```

Explicit release disarms the automatic close before attempting close, including on error. It returns ok0 or err(errno), and consumes the source binding. Later source uses refuse. Consumption is conservative across branches: a release in a conditional prevents a later use even if that branch might not execute. A repeated loop execution of the same release has a runtime armed guard and returns err9 rather than closing a reused descriptor.

Every reached owner is closed in reverse registration order on ordinary return. Owners and legacy defers share a maximum of 16 registrations and the existing 256 local-slot limit. An owner occupies its named slot plus two hidden capture slots. Unreached acquisitions remain unarmed. Return tags and payloads survive cleanup.

If automatic close fails after an authored ok result, the function returns `err(65536+errno)`. For example, err65545 means automatic cleanup encountered EBADF9. A pre-existing primary err is preserved. The first failure in reverse close order wins; additional failures are not aggregated. Legacy defer close remains best effort and does not gain this error protocol. Explicit release reports raw errno directly, without the 65536 marker.

## Boundaries that remain real

The trusted systems profile still exposes raw open/close/syscalls. Deliberately guessing or externally closing an owner's descriptor can defeat the checked contract. Tests use that unsafe route only to inject deterministic cleanup failures. No raw-syscall containment, resistance to external descriptor mutation, or whole-compiler security proof is claimed.

Fatal bounds/UTF8 traps, explicit process exit and signals bypass ordinary cleanup epilogues. OS process reclamation is distinct from running language cleanup. Close errors do not prove whether every possible OS resource remains open, so the owner is consumed after a close attempt rather than blindly retrying a possibly reused descriptor. Functions can deliberately ignore the meaning of an error arm; exhaustiveness is not proof of a sensible recovery policy.

## A real binary-inspection application

`rf2-hex file` prints 16-byte hexadecimal rows with an ASCII gutter. It uses an internally acquired read-only owner, checked reads, explicit short-output handling and typed errors. Normal, read-error and output-error returns release the input in-process. Input remains unchanged. A 1 MiB cap is an explicit partial-output policy, not silent success. [Exact app contract](../examples/hex/README.md).

The separate [byte reference](BYTE-REFERENCE.md) gives all 128 ASCII codes with decimal and hexadecimal forms. Hex is a representation of bytes; this feature does not invent a different CPU encoding or add a disassembler. [Capability map](CAPABILITY-MAP.md) distinguishes working programming support from unimplemented targets and ecosystem features.

## Evidence and reproduction

Set RF2_TEST_COMPILER to the qualified native compiler, then run tests/standalone/ownership_adversarial.py and hex_app_verify.py. Independent fixtures check atomic acquisition, use-after-release refusals, real write/readback, frame/registration bounds, repeated calls, mixed owners/defers and primary/cleanup error precedence. Unsafe descriptor operations inject failures in disposable local fixtures only. The app output is compared with a separately written byte formatter.

[Ownership receipt](OWNERSHIP-0.15-VERIFICATION.json) · [Application receipt](HEX-0.15-VERIFICATION.json) · [Release qualification](RELEASE-0.15-VERIFICATION.json).

WhatIF separately ran 60 bounded GET probes against a disposable Studio instance, followed by evidence verification and normal shutdown. That checks expected HTTP statuses on two routes, not resource semantics, full user journeys, security or capacity. Its RF2 source heuristic inspected no compiler files; native compiler tests provide separate semantic evidence. No HTTP fault was injected and no speed or token-saving claim is made.
