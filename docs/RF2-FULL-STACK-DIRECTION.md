# One programming language, explicit execution contracts

RF2's direction is a readable language for human and AI authors, with one compiler-owned representation connecting application logic to machine execution. A request such as “build this app for Android, iOS and Mac” needs more than translating syntax: the toolchain must also implement the selected platform's interface, resources, permissions, packaging, signing and observable tests. This is the development direction, not the current compatibility claim.

The current qualified target is Apple Silicon macOS. RF2 owns its ARM64 emitter and bounded native compiler. It has local modules, nominal u64 records, operating-system interfaces, a native runtime and a bounded MCP interface. The browser-based Studio is an application example, not a complete cross-platform GUI toolkit. Systems compilation is trusted and not a sandbox.

## Research ideas must become mechanisms

| Research direction | Useful transfer to RF2 | Required evidence before stronger claims |
| --- | --- | --- |
| Kernel 8 | Deterministic candidate rules, resource estimates and retained fallbacks | Executed target programs, resource accounting and independent output checks; recovered query hints alone do not prove compiler speed |
| Kernel 9 | Auditable selection, explicit admissibility and recorded decisions | Compare against fixed simple policies; planner scores do not prove faster native instructions |
| Developmental AI | Reuse observations from completed work and account for adaptation cost | Held-out workloads and total costs including selection; do not assume an adaptive selector beats a simpler baseline |
| Tamil Time Continuum | Make deadline assumptions and scheduling objectives explicit | Measured workload execution, dependencies, synchronization costs and failures; a reservation is not CPU-time enforcement |
| VOIKE | Separate common-mode error from independent noise and validate provenance | Calibrated physical observations before optical accuracy/latency/energy claims; model trials remain model trials |
| RU'OS | Define authority, state and recovery separately from nominal execution | Target-specific boot, rollback, isolation and device checks; host tests do not qualify a phone |

These are scoped engineering directions informed by the research programme. They do not report all papers as completed, published or independently approved. Private manuscripts and participant records are not software-release assets.

## What the Clang comparison taught us

The retained Clang diagnostic reports vectorization width two and interleave four for the conditional masked-sum loop. The retained output assembly includes vector arithmetic and a scalar conditional-select remainder. This explains a concrete implementation difference, not all of Clang's internals. The source and exact diagnostic accompany the measurement tool's output. LLVM documents reductions, vectorization cost models and diagnostic remarks in its [vectorizer documentation](https://llvm.org/docs/Vectorizers.html).

A new RF2 candidate handles one exact conditional periodic recurrence through arithmetic. Its contract, derivation, tests, failures and strongest stated comparison are in [conditional reductions](CONDITIONAL-REDUCTION.md). General vectorization remains future work. Both algebraic reduction and vectorization are established optimization techniques; their RF2 implementation must earn its results.

## A coherent implementation route

1. Stabilize the language contract: integer/overflow rules, modules, diagnostics, structured values, errors, lifetimes and version compatibility. Build a typed, effect-aware representation rather than recognizing every future application as a string template.
2. Build collection and resource semantics with positive and failure tests. Strings, nested structured values, ownership and concurrent sharing are not provided merely by the current u64 records.
3. Extend native lowering with verified scalar/SIMD alternatives. Qualify aliasing, overflow, tail handling and side effects, then measure end-to-end workload costs. Keep a correct scalar fallback.
4. Define concurrency before claiming it: task lifetime, shared-memory rules, atomics, cancellation, deterministic test hooks and bounded resource ownership. Fork/process support is not an RF2 threading or memory model. Compare single-thread and multi-worker paths including synchronization.
5. Implement a platform adapter per target while keeping application source in RF2. Begin with a small shared computation and UI event test on macOS, Android and iOS; require actual built and exercised packages on each. SDK compatibility and signing requirements remain real even when the source language is unified.
6. Add a web target with a specified DOM or WebAssembly boundary, user input, browser tests and deployment artifact. Current static documentation pages are not an RF2 web-app compiler.
7. Qualify boot targets separately: selected architecture, image format, entry contract, interrupts, memory ownership and emulator boot receipt. A macOS Mach-O executable is not a boot sector. Never write a physical disk as an incidental language test.
8. Expose reviewed capabilities through MCP with explicit input/output contracts, bounded effects and reproducible receipts. The AI host proposes and explains; the compiler and runtime enforce what they actually implement. Existing nine tools remain bounded rather than silently acquiring raw system authority.

Each stage must produce an application or machine experiment, an independent expected result, negative cases, reproducible commands and an honest target matrix. Progress is capability-specific, not a percentage inferred from enthusiasm or word count.

## Hardware and speculative backends

On an existing CPU, RF2 can choose legal instructions, vector units, memory access patterns and scheduling. That can reduce work and improve use of existing hardware. It does not change fabricated NMOS/PMOS structures, redefine the chip's instruction encodings or directly allocate individual transistors through ordinary application instructions.

A new virtual instruction set or bytecode can be designed. It still needs an interpreter, translator or compatible processor. Hexadecimal is a notation for bits, not a new execution mechanism. A custom ISA requires a specified decoder and implementation, then conformance and hardware evidence.

Optical, FPGA, GPU, neural and quantum targets can become separate backends if their execution contracts, precision, data transfer, calibration and error models are specified. A classical “virtual quantum” model is a simulator until actual quantum execution is demonstrated. No physical quantum advantage, optical machine or reconfigured transistor substrate is delivered by this compiler work.

The practical differentiator to build is compact readable intent connected to auditable effects and measured execution across targets. It remains an engineering objective, not a universal compatibility, safety, speed or token-saving guarantee.
