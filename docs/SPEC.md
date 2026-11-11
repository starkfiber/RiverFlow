# RF² Core 0.1 specification

RF² is pronounced RiverFlow Squared. The square is the product identity; it is not a square-root operator or an infinity primitive.

This release uses `PROFILE RF2_U32_CORE_V0`. It is a new JavaScript bootstrap informed by the earlier RF² v2 contract, not a compatible implementation of every historical FLOW/ASMX dialect. It has no Python dependency. The interpreter is not self-hosted and does not yet generate native code.

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

`compile` emits inspectable JSON IR, not a native executable. `run` parses and validates source before evaluating it. The CLI writes IR only to an explicit path; MCP tools accept text/data and provide no arbitrary file access. No embedded model or inference API is configured. Codex or another client supplies AI assistance.

Compatibility policy: freeze profile semantics; incompatible changes require a new profile. Retain golden programs, independent expected results, failure cases and migration notes. Longevity is a maintenance objective, not a million-year guarantee.

## Prepared execution in package 0.2

`prepare(source)` validates once and returns a callable for separate input arrays. Each invocation has fresh locals and its own work budget. A failed invocation does not reuse partial values in the next call. `execute(source, data)` continues to prepare and evaluate in one operation. `rf2_run_batch` accepts at most 20 arrays, each at most 4096 values, and returns results in order; a failure rejects the tool call rather than returning a success for the full batch. The language profile and arithmetic semantics remain unchanged.
