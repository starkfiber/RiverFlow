# Owned heap collections, development 0.33

RF2 now has bounded, relocating collections of unsigned 64-bit values. Storage grows on the heap rather than consuming the fixed-array stack arena. Two complete `.flow` applications share a parser, heapsort and output library: [numeric summaries and frequency tables](../examples/collection-tools/README.md).

This development source targets Apple Silicon macOS. The stable 0.17 runtime and its nine bounded MCP tools retain their existing contracts. General systems source, including heap operations and raw syscalls, is not admitted through the bounded MCP checker.

## Declare, handle and move

```rf2
profile RF2_SYSTEM_A64_V1
result IO(u64,u64)
collection Numbers(IO,65536)

fn work():IO
 own input=Numbers()
 handle collection_push(input,42)
 ok count
 err cause
  return err(cause)
 end
 own values=move(input)
 return ok(values.length)
end

fn main(argc,argv)
 handle work()
 ok count
  return count!=1
 err cause
  return 1
 end
end
```

The declared limit is a canonical decimal integer from 1 through 65,536 elements. An empty owner is armed but has no allocation. First growth starts at up to 16 elements, with geometric growth bounded by the declared limit. An allocation requests eight bytes per capacity element; actual OS mapping uses its page granularity. This is not allocation of the entire declared limit at construction.

| Operation | Successful result | Recoverable failure |
| --- | --- | --- |
| `collection_reserve(owner,count)` | Current capacity, preserving length and values | Declared-limit or OS mapping/retirement error |
| `collection_push(owner,value)` | New length | Declared-limit or growth error |
| `collection_get(owner,index)` | Value | Out of range or released owner |
| `collection_set(owner,index,value)` | Stored value | Out of range or released owner |
| `collection_clear(owner)` | Zero length, retaining allocation | Released owner |
| `release(owner)` | Zero; ownership disarmed after successful retirement | OS retirement error; retry remains possible |

The operation result is the declared scalar result type and must be exhaustively handled. Bounds errors return 34, declared-limit errors 22 and operations on a successfully released owner 9. `.length`, `.capacity` and `.limit` are checked properties; accessing a released owner through a property traps rather than returning a typed error. These values and policies are target-specific current contracts, not a portable universal errno standard.

## Ownership and borrowing

`own destination=move(source)` is a root-function-scope local transfer. It consumes the source binding and transfers both active and pending mapping ownership. Copying an owner, scalar coercion and returning it from a function refuse. There is no ownership-transfer parameter or owner-return support yet.

A typed parameter such as `fn sort(values:Numbers):IO` is a nonescaping mutable borrow. It may call collection operations but may not move or release that borrowed owner. Sequential borrowed parameters may alias; this is not an exclusive-borrow or concurrency model. Scalar operation arguments finish evaluation before the operation reads current descriptor state, including when an argument helper grows the same collection.

Unlike older owned File/Bytes resources, collection `release` retains the binding for retry after a failure. Successful release is enforced by runtime state checks. This is a combination of checked local moves and runtime lifetime checks, not a complete static linear type system. The contextual spelling `move` after `own name=` conflicts with an older resource constructor literally named `move`; ordinary scalar function calls named `move` are unaffected.

## Growth and cleanup failures

Growth maps new read/write memory, copies live elements, retires the old mapping and only then publishes the new pointer/capacity. A failed mapping leaves the active collection unchanged. If old-map retirement fails, the active values, length and capacity stay unchanged and the new speculative allocation is retained as pending ownership. The next growth first retries retirement of that pending map. A successful retry can then continue normal growth.

Release attempts both active and pending retirement, retaining the first error. It can partially succeed: the active mapping may be gone while a pending mapping still needs retry. **A release error does not promise to preserve collection data.** This differs from the active-data preservation rule for failed growth.

Ordinary function-return cleanup preserves the primary result error. If cleanup alone fails, it reports `65536 + positive errno`. A kernel that keeps refusing retirement can leave a mapping until process exit; cleanup is not infallible. Fatal traps, process signals and deliberate raw-pointer/syscall interference are outside this ownership guarantee. There is no arbitrary C-like pointer memory-safety claim.

## Compiler-owned lowering

The compiler appends four private RF2 helper functions and one private result declaration only when actual collection declarations occur. The [readable snapshot](HEAP-RUNTIME-0.33.md) is derived from the authoritative compiler literal. It is not an external runtime file that users must find or link.

The `__rf2heap` prefix is compiler-owned. Admission checks source-token origin against the appended-source boundary, refusing user declarations or direct calls into the descriptor helpers. Comments and strings that mention a collection do not trigger helper insertion. Expanded/lowered source identity includes the helper code. This boundary protects the typed interface; hiding helper names is not its security mechanism.

The 2,515-byte helper source counts against the existing global budgets: 256 functions, 32 named types, 65,536 tokens and 524,288 source bytes. A collection program therefore admits at most 521,773 expanded user-source bytes before helper insertion. Four function slots and one named-type slot are consumed. Array frame, named-local and existing compiler-image budgets are not silently widened.

## Qualification and retained failure

Final evidence is linked in [the qualification index](HEAP-COLLECTIONS-0.33-QUALIFICATION.json). Tests compare actual native outputs with independently computed expected values, exercise both ordinary and optimized lowering, and include source refusal, in-process mapping lifetime probes, default compiler reproduction, existing resource/cache regressions and actual MCP SDK exchanges.

| Final controller | Passed controls |
| --- | ---: |
| [Heap implementation](HEAP-COLLECTIONS-0.33-ENGINE.json) | 64 |
| [Independent ownership/failure review](HEAP-COLLECTIONS-0.33-REDTEAM.json) | 78 |
| [Two shared-library applications](HEAP-COLLECTIONS-0.33-APPS.json) | 308 |
| [Mixed .flow/.rf2 module boundaries](HEAP-COLLECTIONS-0.33-FLOW.json) | 26 |
| Existing [byte vectors](HEAP-COLLECTIONS-0.33-VECTOR.json), [file cleanup](HEAP-COLLECTIONS-0.33-CLEANUP.json), [file ownership](HEAP-COLLECTIONS-0.33-OWNERSHIP.json) | 94 / 52 / 136 |
| Existing [frame boundaries](HEAP-COLLECTIONS-0.33-STACK.json), [multiple views](HEAP-COLLECTIONS-0.33-VIEWS.json), [ABI probes](HEAP-COLLECTIONS-0.33-ABI.json) | 82 / 18 / 4 |
| [Target cache](HEAP-COLLECTIONS-0.33-INCREMENTAL.json), [function packs](HEAP-COLLECTIONS-0.33-PACK.json), [default-image compiler store](HEAP-COLLECTIONS-0.33-STORE.json) | 58 / 79 / 20 |

These are controller cases, not independent field experiments. The [compiler reproduction and maintained encoder](HEAP-COLLECTIONS-0.33-COMPILER.json) compare generated compiler/runtime bytes; the maintained encoder is not an independent implementation of the collection language. The separate [compact runtime corpus](HEAP-COLLECTIONS-0.33-RUNTIME.json) and official MCP SDK exchange preserve the nine-tool contract. The default signed compiler is16,647,664 bytes, leaving129,552 under the unchanged16,777,216-byte store limit.

The [download package](../dist/0.33-candidate/README.md) includes native compiler, runtime/MCP and both apps, plus their sources. [Fresh extraction](HEAP-COLLECTIONS-0.33-PACKAGE.json) checked every manifest file, signatures, both app results, refusal of malformed input and compilation/execution from the bundled `.flow` source. This is same-Mac qualification; the images are ad-hoc signed, not notarized.

An independent syscall-failure campaign found a genuine ARM64 instruction bug before release: automatic cleanup copied the wrong register and returned the wrong secondary error. The emitted word was corrected from `0xaa000400` to `0xaa0103e0` (`MOV x0,x1`). The corrected compiler was frozen and requalified. Test-only patched syscall results exercise specified failure paths; they are not claims that the host experienced real OOM or kernel failure. In-process retirement probes distinguish explicit cleanup from the OS reclaiming mappings at process exit.

No runtime speed, energy, AI token saving, complete allocator safety or general-purpose library parity is claimed by this change. Dynamic structured records, maps, ownership transfer across functions, concurrency and other targets remain work.

## `.flow` and hardware use

Native entry files and relative imports now accept both `.flow` and `.rf2`, with the same path and module-budget checks. File extensions do not choose a CPU or operating system.

The collection apps can process supplied numeric readings on the qualified host. They do not read a physical sensor. ESP32, Arduino and printer firmware need a target backend, linker/boot contract, drivers and board-specific tests. [The embedded direction](EMBEDDED-DIRECTION.md) distinguishes proposed ESP32-C3 work from current support; no board was flashed and no heater or motor was controlled.
