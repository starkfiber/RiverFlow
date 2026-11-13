# Compact native images and function-change evidence: 0.27 candidate

## The problem and implemented change

Earlier RF2 images stored zero-filled buffer reservations in the executable file. Copying, hashing and publishing those bytes added work to the build/cache path. The optional native compiler flag `--compact` separates initialized file data from the zero-filled virtual tail.

Strings and loader binding slots are laid out first; buffer reservations follow them. Object IDs remain stable during fixup resolution. The data segment retains its full virtual size and permissions, while its file size covers only the initialized prefix rounded to the existing page alignment. Link-edit file offsets are updated independently of virtual addresses. The existing default format remains available.

The build driver also avoids a forced disk flush for its reconstructible compiler snapshot. It closes and atomically renames the new snapshot; each reuse validates byte identity, file ownership, permissions and link count. A power interruption can lose that snapshot and require repair. Target-cache entries and published outputs retain their existing durable writes; no crash-atomic multi-file transaction is claimed.

This is RF2 adopting an established operating-system mechanism, not new transistor behavior. Apple's [Mach-O segment definitions](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/EXTERNAL_HEADERS/mach-o/loader.h) distinguish file and virtual sizes. The local executable checks establish the tested implementation behavior.

Raw static addresses and object ordering change in compact mode. Programs must not assume a particular placement of unrelated objects. Buffer identity, initialized strings, zero initialization and tested bindings remain functional. Virtual reservations are not removed, and smaller files do not prove lower physical memory usage.

## Use it

Build a current compiler from a qualified prior native compiler, sign it, then self-build a compact executable into a new path:

```sh
/path/to/prior-rf2c native/compiler/compiler.rf2 output/rf2c-stage1 --opt
/usr/bin/codesign -s - output/rf2c-stage1
./output/rf2c-stage1 native/compiler/compiler.rf2 output/rf2c-compact --opt --compact
/usr/bin/codesign -s - output/rf2c-compact
python3 tools/build-incremental.py output/rf2c-compact output/compact-builder --compact
mkdir -m 700 .rf2-cache
./output/compact-builder/rf2-build output/rf2c-compact examples/file-checksum.rf2 output/checksum-001 .rf2-cache --opt --compact
```

Create `output/` first if absent and use unused output names. The selected compiler must support the flag; older compilers refuse it. The builder's key binds this option, so legacy and compact images cannot be confused. Produced application images still need ordinary macOS signing before execution. The native executable has no Python/Node runtime; Python controls the explicit developer build.

This image flag is separate from compact Core syntax and from the MCP reply-text option. No systems compilation or filesystem capability is added to MCP.

## Complete build measurements

Twenty-one rotated trials per variant and real target, one Apple Silicon Mac, warm filesystem. All timings include process startup and complete compilation or verified reuse plus output publication. Signing and correctness checks are outside the timer. Cold rows start from a fresh empty cache and include compiler snapshot creation and first execution; the filesystem itself is warm. Forced rows have a verified compiler snapshot available. Each format's outputs match its own fresh clean oracle byte for byte. Legacy and compact images intentionally have different layouts.

| Target | Legacy direct | Compact direct | Legacy forced | Compact forced | Legacy warm | Compact warm | Legacy empty cache | Compact empty cache |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Compiler | 49.013 | 23.534 | 80.086 | 26.656 | 18.357 | 3.155 | 234.920 | 147.835 |
| Runtime | 52.357 | 24.066 | 86.346 | 27.331 | 21.805 | 3.215 | 267.649 | 162.393 |
| Checksum | 7.341 | 4.258 | 23.074 | 7.042 | 9.488 | 3.215 | 164.438 | 116.651 |

Times are median milliseconds. Warm reuse improves 5.82x, 6.78x, 2.95x respectively against the previous warm route. Forced rebuilds improve 3.00x, 3.16x, 3.28x. Empty-cache first builds improve 1.59x, 1.65x, 1.41x, but remain much slower than direct compilation. Paired candidate-minus-legacy bootstrap intervals exclude zero in the improving direction for these observed comparisons. These are bounded exploratory measurements on one host, not universal performance ratios. A compact forced rebuild also costs more than direct compact compilation.

Earlier retained trials with and without the compiler-snapshot flush were not a controlled causal comparison; they do not establish a separate latency benefit from that small change. Fresh snapshot creation and first execution still need profiling. The compact image measurements compare the complete candidate against the previous route, rather than attributing every millisecond to one instruction.

Unsigned image bytes fell from 12,304,384 to 229,376 for the compiler target, 13,647,872 to 212,992 for the runtime target, and 1,097,728 to 49,152 for the checksum target. The selected signed compiler also shrank from about 9.8 MiB to about 242 KiB, and the build driver from about 34 MiB to about 98 KiB. Source/runtime behavior must be checked independently of file size.

Raw reports retain cumulative child CPU-time observations as well as wall time and file bytes. CPU-time observations are not watts or joules. No hardware power measurement, model-token experiment, Clang/Python runtime superiority or physical transistor redesign is claimed.

[All build trials](COMPACT-BUILD-MEASUREMENTS.json).

## Function-level progress

`rf2c source new-output --opt --compact --functions` emits an additional `new-output.functions` sidecar after compilation. It contains per-function canonical token fingerprints, code ranges, relocation records and named direct-call edges, plus declaration/signature context and mode flags. Blank-line/comment-only changes do not create false body changes in the tested case.

`tools/function-impact.py old.functions new.functions` compares those records and propagates changes to callers. Type/declaration or mode changes conservatively request global revalidation. The [working sample](../examples/function-changes/) demonstrates one changed leaf, affected callers and an unrelated unchanged function.

This is a diagnostic foundation, not function-level code caching. The output explicitly reports `machineCodeReused: false`. Positional relocation IDs are not stable linker identities; object registration, shared-buffer effects, type/ABI validation, compiler provenance and complete relocation replay are still required before admitting cached function bodies. An unchanged-source candidate is not proof of safe machine-code reuse.

Maps are bounded developer data, not signed attestations. The parser refuses truncated, malformed or unresolved-call maps. A sidecar creation error can leave the newly emitted image; the compiler does not claim an atomic multi-artifact transaction. Existing sidecars are never overwritten.

## Executed gates and retained failures

- Compact and legacy target execution passed for zero-filled buffers, named-buffer identity, calls/branches, typed arrays and clock-library binding in both compiler modes; modular SHA checks bring the execution total to 44.
- Reordering-induced alignment overflow was refused by a direct native boundary probe.
- Compact compiler self-generation produced identical unsigned images. Default compiler self-generation still matched the independent historical seed encoder, with runtime corpus and official MCP SDK checks passing.
- All 58 incremental scenarios passed in compact mode and all 58 passed in the legacy route, including stale inputs, compiler/option identity, corruption, lock contention, captured-source edits and output preservation.
- A compact cached native runtime passed its corpus and nine-tool official MCP SDK checks. Eight process-owned Hypervisor probes matched legacy observations and cleanup; no Linux boot or wider hardware claim follows.
- Function-change and call-propagation controls passed, including type-context invalidation and four malformed-map refusals. A comment-only counterexample exposed newline-sensitive fingerprinting; consecutive blank-line tokens were normalized and the exact test rerun.

Earlier compiler-source spacing incompatible with the seed oracle and an incomplete map header were corrected. Failed attempts and raw receipts remain in project-owned local artifacts. No successful result is inferred from a file-size change alone.

[Image and map checks](COMPACT-IMAGES-VERIFICATION.json) · [compact cache](COMPACT-INCREMENTAL-VERIFICATION.json) · [legacy cache](LEGACY-INCREMENTAL-0.27-VERIFICATION.json) · [compiler, MCP and VM integration](COMPACT-0.27-INTEGRATION.json).

The next function-reuse stage needs a relocatable unit format and replay of semantic/object effects, followed by the same clean-build oracle. Energy efficiency needs an explicit hardware measurement protocol. Existing examples and controls remain executable references in the [developer guide](DEVELOPER-EXAMPLES.md).
