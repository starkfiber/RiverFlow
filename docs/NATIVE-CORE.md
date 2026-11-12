# Native Core and kernel lowering, release 0.6

Core programs using `RF2_U32_CORE_V0` now run without Node, npm, Python or C++. The native parser validates names, types, assignments, helper arity, all functions including unused ones, loop scope, limits and an acyclic call graph. Functions may call forward-declared scalar helpers. Both checked and wrapping u32 arithmetic retain the reference contract.

## Two execution routes

`rf2 run program.flow '[1,2,3]'` parses and checks source, then executes bounded internal IR in the RiverFlow-written native ARM64 runtime. This is native runtime execution, not per-request JIT compilation.

For a separately compiled program:

```sh
./tools/build-core.sh ./rf2 ./rf2c examples/sum.flow sum-build
./sum-build/program '[1,2,3]'
```

The script creates a new output directory, invokes native `rf2 lower` to produce systems-profile kernel source, combines that fragment with `native/lowered-harness.rf2`, invokes native `rf2c`, and applies normal macOS code signing. The result contains per-program ARM64 functions. It does not use an IR dispatch loop to execute the generated kernel. The input harness still validates supplied JSON data.

Both routes preserve successful outputs, abstract work counts and overflow/LOAD/loop/work-budget refusal behavior in the executed corpus. These events are language accounting, not CPU cycles. The generated kernels use bounded memory-backed frames and explicit error/work state; no speed comparison has been made.

`rf2 lower` prints a kernel fragment, not a standalone application or a Mach-O file by itself. `rf2_lower` over MCP returns the same fragment as text and never compiles it or writes a file. Creating an executable remains an explicit developer action.

## Exact boundary

The unchanged Core operations are ADD, MUL, LOAD, POPCOUNT, NONZERO and named CALL. Main takes one readonly u32 array and a count. Helpers take at most four scalar u32 parameters. Calls are acyclic, loops are non-nested and confined to main, induction variables/parameters are immutable, and loop-local names cannot escape. A LOAD uses full input capacity rather than the chosen prefix count.

Limits remain 16 functions, 512 statement nodes, 65,536 input words/loop iterations and 1,048,576 work events. Source must be well-formed UTF-8 with at most 32,768 UTF-16 code units, matching the reference string budget for valid Unicode. Native transport rejects malformed UTF-8 and unpaired surrogate escapes; it does not copy JavaScript's permissive replacement of malformed file bytes. Case and canonical Core statement formatting are retained. Tested whitespace includes Unicode trimming/parameter spaces, source-title Unicode and dot-regex line-separator refusals.

The systems compiler profile remains distinct and trusted. Core has no filesystem, network, arbitrary pointer or machine-instruction syntax. Native kernels require the trusted generated caller and stable valid buffers. Neither differential agreement nor bounds checks establish process isolation, a hostile-host sandbox or formal proof.

## Verification

- `GENERAL-CORE-VERIFICATION.json`: 109 program entries, 317 admission checks and 1,095 executions against the JavaScript reference, including 180 seeded source mutations. Checks include helper chains, four named arguments, unused invalid functions, scope restoration, recursion, overflow and work limits.
- `DIRECT-KERNEL-VERIFICATION.json`: 18 native build cases and 163 actual executable runs through native lowering and compilation. These include all five complete book programs, 501 distinct scalar registers and a large-work refusal probe. Values and work counts match; expected dynamic refusal categories are checked.
- `COMPACT-0.6-VERIFICATION.json`: the existing 1,016 compact comparisons and transport/input refusal checks rerun against the expanded native runtime.
- `NATIVE-COMPILER-0.6-VERIFICATION.json`: systems-compiler fixed point retained, and the complete composed 0.6 runtime image matches the historical encoder's bytes.

The self-written parser, compiler and generated code have not received an independent security audit. The retained C-backend sanitizer tests are separate and must not be described as sanitizer coverage of these direct machine-code paths. No speed, energy or token-saving claim is made.

## Native tools

`rf2_status`, `rf2_check`, `rf2_run`, `rf2_lower`, `attendance_export`.

The first four report/check/execute/return source. The fifth is the separately versioned application capability documented under `capabilities/attendance.local.v1/`. The older JavaScript research catalog and batch/C-emission tools remain a separate reference server.

Test counts describe corpus entries, build cases and executions. Some reference/book fixtures overlap; unique source counts are recorded separately. They are not independent experiments or counts of unique algorithms.

## Release 0.7 checkpoint

Core semantics are unchanged and the corpus was rerun against the 0.7 runtime; suffixed 0.7 reports retain its exact binary hash. The sixth native tool is invoice_total, using the separate RF2_APP_V1 plan and generated Core subtotal kernel. The systems runtime now composes seven modules and reaches the compiler's 128-function limit. See the versioned invoice contract and measured results; native implementation alone does not establish lower latency or fewer AI tokens.

Release 0.8 reruns the Core and lowering corpora unchanged. Native transport fast-paths canonical integer tokens and borrows unescaped string bytes only during a request; escaped numeric/string forms retain exact parsing. No borrowed input is persisted in prepared plans. Nine runtime modules now include immutable plan reuse and a CLI-only file-based document/PDF workspace. Corresponding 0.8 reports bind the final binary. Core still has 16 functions and input-only effects; the separate systems compiler expands to 256. See PREPARED-PLANS.md, INVOICE-WORKSPACE.md and REUSE-MEASUREMENTS.md.
