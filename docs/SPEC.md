# RF² Core 0.1 specification

RF² is pronounced RiverFlow Squared. The square is the product identity; it is not a square-root operator or an infinity primitive.

This release uses `PROFILE RF2_U32_CORE_V0`. It began as a JavaScript reference informed by the earlier RF² v2 contract, not a compatible implementation of every historical FLOW/ASMX dialect. It has no Python dependency. The reference emits C11 in package 0.3. Native 0.6 separately implements the Core parser/runtime and per-program systems lowering; see NATIVE-CORE.md. The systems compiler has its own bounded self-reproduction evidence.

Programs begin with `FLOW "name"`, the profile and `ARITHMETIC CHECKED` or `ARITHMETIC WRAP`. Functions have named `u32` parameters and return `u32`. `main` requires one `u32[]` and one `u32` count, in that order. Helpers accept up to four scalar parameters. Calls are acyclic. Forward helper calls work.

`VAR name = value` declares a local. `STEP label = OP WITH { named: value, result: variable }` computes and stores a result. Supported operations:

| Operation | Arguments | Result |
|---|---|---|
| ADD | a, b | unsigned sum |
| MUL | a, b | unsigned product |
| LOAD | array, index | input element |
| POPCOUNT | value | number of set bits |
| NONZERO | value | zero or one |
| CALL helper | names from helper signature | scalar return |

Values are local names or decimal/hex unsigned literals. Parameters and induction variables are immutable. Loops use `FOR i FROM 0 TO count LIMIT 65536` and `END FOR`. The upper value is captured at entry, excludes the endpoint and cannot exceed its declared limit. No nested loops. Locals introduced in a loop do not escape it. Every function finishes with `RETURN value` and `END`. `#` starts a line comment.

Checked addition/multiplication reject overflow beyond 2^32−1. Wrapping arithmetic is modulo 2^32. The runtime uses BigInt internally to preserve multiplication accuracy. Errors produce no language result. Compilation validates all functions, including unused functions.

Limits: 32,768 source characters, 16 functions, 512 body nodes, 65,536 supplied input elements and loop iterations, 1,048,576 execution work steps. Each call, statement and loop iteration consumes steps. Work steps are abstract interpreter events, not CPU cycles, deadlines or energy measurements. Input elements must be integer Numbers in the u32 range. Count must be within the input capacity. LOAD can address any supplied input element, independently of count.

The only effect is `read_input`. The language has no allocation syntax, network, filesystem, UI, raw instructions or device capabilities. Its JavaScript implementation allocates host memory. Bounded language execution is not a complete hostile-host security sandbox. Compiler internals and bootstrap runtime are trusted. Hardware services require a future explicit, versioned extension.

`compile` emits inspectable JSON IR, not a native executable. `emit-c` emits checked C11 source; compilation and execution are separate host operations. `run` parses and validates source before evaluating it. The CLI writes IR only to an explicit path; MCP tools accept text/data and provide no arbitrary file access. No embedded model or inference API is configured. Codex or another client supplies AI assistance.

Compatibility policy: freeze profile semantics; incompatible changes require a new profile. Retain golden programs, independent expected results, failure cases and migration notes. Longevity is a maintenance objective, not a million-year guarantee.

## Prepared execution in package 0.2

`prepare(source)` validates once and returns a callable for separate input arrays. Each invocation has fresh locals and its own work budget. A failed invocation does not reuse partial values in the next call. `execute(source, data)` continues to prepare and evaluate in one operation. `rf2_run_batch` accepts at most 20 arrays, each at most 4096 values, and returns results in order; a failure rejects the tool call rather than returning a success for the full batch. The language profile and arithmetic semantics remain unchanged.

## C11 backend in package 0.3

The entry point is `int rf2_eval(const uint32_t *data, size_t words, uint32_t count, uint32_t *out, uint32_t *work)`. Caller must provide valid, stable allocations and truthful capacities. Inputs may contain at most65536words. The wrapper rejects invalid capacities, null required pointers, unsupported alignment, address-range overflow and overlap between input, result and optional work storage. It cannot prove allocation validity. Status0 writes the result. Status-1 rejects the ABI before evaluation; -2 is checked overflow, -3 LOAD bounds, -4 loop limit and -5 work budget. Evaluation failure preserves out; work may receive consumed events.

Default emission recognizes only the exact zero-initialized input-sum pattern. Its work formula is3+3n, bounded by196611. Checked sums stop at the first overflowing addition; wrapping sums accumulate at most65536u32 values in u64 and reduce on return. Other programs use the general event-counted backend. `emitC(source,{optimize:false})` selects the conservative emitter. Existing profile semantics are unchanged. Native host tests do not establish phone execution or general security.


## Standalone 0.4 profiles

RF2_COMPACT_V1 is a deliberately narrow front end for the four reductions specified in STANDALONE.md. Its expansion preserves this Core profile's checked/wrap arithmetic, successful work counts and read_input effect. It is not a general Core parser. The native systems implementation is RF2_SYSTEM_A64_V1, with modular u64 operations and trusted raw pointers/syscalls; it is not a sandboxed Core extension and is never accepted from MCP callers. The seed emits machine instructions directly and still requires build-time Python and macOS signing. It is not self-hosted. Read STANDALONE-VERIFICATION.json for actual execution evidence.


## Native Core in 0.6

The Core contract above is implemented by the native parser and bounded IR runtime, including scalar/forward helpers, graph checks and all-function validation. An optional lowering path emits checked systems-profile functions and compiles them to ARM64 with native rf2c and the trusted input harness. Read NATIVE-CORE.md for source encoding, format boundaries, actual tests and distinctions between the execution routes. Runtime and machine-code generation are not inferred from a returned source listing.

The application capability attendance.local@1 is separate from Core's read_input effect. Its MCP tool returns CSV; its CLI writes only the explicitly requested new output path. It does not add file/network operations to arbitrary Core source.

## RF2_APP_V1, native release 0.7

A distinct application-plan profile, not an extension to Core effects. Exact grammar: `rf2 app v1 invoice total currency ABC tax N bps`. ASCII whitespace separates ten words. ABC is exactly three uppercase ASCII letters; N is canonical decimal 0..10000. Maximum 256 bytes. The app CLI and invoice_total MCP accept this plan; computation check/run/lower retain their existing profiles. The full data, arithmetic, rounding and effect contract is in capabilities/invoice.total.v1/README.md. Unsupported intent syntax remains unsupported.

## Release 0.8 lifecycle and workspace

Core and RF2_APP_V1 semantics are unchanged. See PREPARED-PLANS.md for immutable process-local invoice plan prepare/apply/release, and INVOICE-WORKSPACE.md for the separate explicit CLI-only document/edit/PDF effects. No MCP file path is admitted. The systems compiler bound expands to 256 functions with separate metadata/local table capacities and boundary tests.
