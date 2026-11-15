# Developer loop, source candidate 0.48

This fixes observed repair friction in the retained [0.47 construction study](../../docs/APP-EFFORT-0.47.md). It does not claim a new model-token saving or a complete development-time win against Python. Qualified downloads remain unchanged.

## Build and use

Use the qualified native 0.47B candidate as the bootstrap. The preparation controller needs Python 3; the emitted compiler, driver and apps do not.

```sh
python3 experiments/developer-loop/prepare.py /new/path/candidate
sh tools/build-program.sh /path/to/0.47B/compiler /new/path/candidate/compiler.flow /new/path/compiler-build --opt
sh tools/build-program.sh /new/path/compiler-build/program experiments/developer-loop/dev.flow /new/path/driver-build --opt
mkdir -m 700 /new/path/app-build
/new/path/driver-build/program /new/path/compiler-build/program /path/to/app.flow /new/path/app-build
/new/path/app-build/program
```

The last line executes the app explicitly. `rf2-dev COMPILER ENTRY PRIVATE-DIRECTORY` compiles with `--compact --opt`, signs and verifies a private candidate, then atomically replaces `PRIVATE-DIRECTORY/program`. Use `--no-opt` as the final argument for a plain build. Repeat the same build command; a rejected compile or sign leaves the previous program untouched. An already-running old program keeps its image; new launches see the committed image.

The directory must already exist, belong to the current user and exclude group/other access. It is dedicated to this replaceable `program`; do not point it at an unrelated directory containing a valuable file named `program`. Existing symlinks, directories and hard-linked outputs refuse. A cooperative nonblocking lock refuses simultaneous writers with status75. An owned single-link regular `program` is explicitly replaceable, even if it was not created by this driver. The compiler/source and directory owner are trusted. This is not protection against malicious same-user writers, a shared build service or an application sandbox. The driver never runs app code, resets a database or gains MCP authority.

Publication uses a same-directory rename after file sync. Directory power-loss durability, crash/cancellation cleanup, source/dependency snapshots, incremental-cache reuse, cross-platform operation and keeping a history of successful binaries are not implemented. A killed build may leave a private candidate; the previous committed image remains separate. Do not infer that all malformed executables or hostile compilers are safe from the bounded header checks and normal signing verification.

## Scalar field propagation

```text
fn parse_request(req:Request,bytes,count):IO
 set req.id=try text_parse_u64(bytes,count,18446744073709551615)
 return ok(1)
end
```

This is a syntax fragment requiring the actual `Request`, `IO` and text-library declarations. Plain/nested borrowed scalar fields and scalar fields inside owned records are admitted. The exactly one saved destination address is removed on the error jump before ordinary cleanup. The field is written only after success; RHS effects that already happened are not rolled back. Nominal result compatibility, moved-owner checks and existing assignment rules remain. Arrays, nested `try` expressions, structured/owned result payloads and descriptor rebinding are not added.

## Diagnostics

Imported-source errors name the original path and line/byte column. This is the compiler cursor, sometimes just after the bad token. A bounded range map coalesces contiguous copied source, rather than storing a map entry for each byte. Generated collection lowering retains its distinct fallback label. Messages suggest grouping more than eight parameters into a record, placing record declarations at function scope, and adding the currently required root-level result return. Those language limits have not silently disappeared. Paths are control-character sanitized, not secret-redacted.

## Reproduce the evidence

```sh
RF2_DEV_COMPILER=/path/to/candidate/compiler RF2_DEV_BASELINE=/path/to/0.47B/compiler RF2_DEV_DRIVER=/path/to/driver python3 tests/standalone/developer_loop_verify.py
python3 experiments/app-effort/qualify.py /new/path/candidate/build/program
python3 experiments/developer-loop/replay.py /path/to/candidate/compiler /path/to/driver /new/path/app-replay
python3 experiments/developer-loop/benchmark.py /path/to/0.47B/compiler /path/to/initial-0.48A/compiler /path/to/range-0.48B/compiler
```

The historical qualification controller expects the existing reference artifact layout stated in its source and a candidate at `candidate/build/program` with `candidate/compiler.flow`. It performs real native checks, not ordinary installation. `replay.py` verifies and reads the published 0.47 source archive, makes five mechanical edits and runs the unchanged 55-check grader; it is not a new autonomous authoring trial. `benchmark.py` performs two warmups and 15 rotated measured compiles per arm/workload, checks unchanged-source byte identity, and retains every timing. The source-only [diagnostic comparison archive](../../docs/evidence/DEVELOPER-LOOP-0.48-SOURCES.tar.gz) retains both candidate compiler sources. Rebuild/sign them with the same qualified bootstrap before the three-arm comparison. Model usage, billing, application runtime and signing time are outside this compilation measurement.

[Results, failures and remaining gates](../../docs/DEVELOPER-LOOP-0.48.md) · [source-bound receipt](../../docs/DEVELOPER-LOOP-0.48.json).
