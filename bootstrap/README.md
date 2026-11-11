# RF2_SYSTEM_A64_V1 seed

This is a trusted bootstrap compiler for the standalone implementation source, not a general user-facing Core parser. The seed is build-time Python. It emits ARM64 words and Mach-O load commands directly, then invokes only the macOS ad-hoc signing utility. No C/C++, assembler or linker is used. The executable uses the normal macOS loader and system interfaces. Do not disable platform security to run it.

Systems syntax:

- `profile RF2_SYSTEM_A64_V1` is mandatory.
- `fn name(parameters)` and `end` define a function. main takes argc and argv. At most eight function arguments. Local identifiers are unique within a function.
- `let name = expression`, `set name = expression`, `do expression`, `return expression`.
- `if expression`, optional `else`, `end`; `while expression`, `end`. No implicit break.
- Unsigned 64-bit modular `+ - * & | ^ << >> //`, comparisons `== != < <= > >=`, unary minus and bitwise complement, parentheses, integer/string literals, function calls. Shift counts use AArch64's low six bits. Division by zero follows AArch64 UDIV (zero); trusted code must choose its checks explicitly.
- `load8/32/64(pointer)` and `store8/32/64(pointer,value)` are raw memory operations. `buffer("unique_name", literal_size)` reserves aligned zeroed storage. Reusing a buffer name must agree on its size. String literals are zero-terminated UTF-8 and are stored in the data segment.
- `read`, `write`, `open`, `close`, `exit` call the corresponding macOS system interfaces. Negative unsigned-64 encodings represent syscall errors. There are no other built-in host effects.

This profile deliberately lacks automatic memory safety. Pointer validity, initialization, shift/division semantics, recursion bounds and explicit parsing limits are the trusted implementation's responsibility. User computations never receive this profile. It is not a security boundary for arbitrary machine-profile source.

The seed currently uses Python's expression AST as a build-time syntax parser for a restricted expression subset; it does not evaluate expressions through Python. Its own instruction encoder, branches, addresses, frames and executable writer produce the native output. This dependency is explicit, not self-hosting. Unknown syntax, unsupported operators, wrong function arity and unresolved locals stop the build. Review changes to both the compiler and systems source, then execute differential and refusal tests.

Build: `python3 bootstrap/seed.py native/rf2.rf2 output/bin/rf2`.

The first static-executable experiment was refused by platform policy. The working format uses normal dyld loading, UUID and signing; no platform policy was changed. The small hello source is retained as an encoder/loader smoke test.
