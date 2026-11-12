# Language and interface measurements, 0.10

| Kernel, 2 million iterations | 0.9 ms | 0.10 default ms | 0.10 opt ms | Clang O2 ms | Python ms |
| --- | --- | --- | --- | --- | --- |
| accumulate | 14.334 | 15.185 | 11.970 | 5.349 | 181.976 |
| mix | 29.849 | 29.326 | 15.790 | 7.506 | 313.676 |
| branches | 16.071 | 15.715 | 10.243 | 5.349 | 208.129 |

Each kernel prints a checksum independently calculated by the test controller. Nine fresh launches per variant are rotated in a deterministic shuffled order. Wall time includes process start. The same scalar RF2 source is compiled with frozen 0.9, default 0.10 and optional --opt. Three kernels cover accumulation, mixed bit/arithmetic operations and branches. Default output retains the old instruction path; timing noise is still visible. Clang -O2 and Python implement matched checksum operations, not RF2's parser, effect checks or complete application behavior. The C loop bound comes from argv; RF2 and Python use the specified fixed count. A compiler can legitimately optimise different loop work. This is a small code-generation comparison, not language ecosystem parity or universal speed.

On this host, --opt is faster than 0.9 on all three kernels. Clang is faster than all RF2 variants. The earlier development run, before adding C/Python comparisons, is retained locally; the final report is not selected for the lowest absolute times. No energy, hardware, inference or general speed claim follows.

## MCP

A 64-word POPCOUNT request has median 62.31 µs in 0.9, 52.46 µs in 0.10 and 50.58 µs in opt-in compact mode. One hundred rounds rotate live persistent server variants; complete structured values are checked. This is one process per variant on one host, not a hardware population or confidence interval.

The complete retained 100-call session, including initialization, discovery and one overflow error, encodes to 23,877 o200k tokens in 0.9/default 0.10 and 22,277 in compact mode, a 6.70% reduction. Schema bytes remain identical. Complete raw exchanges and cl100k counts are retained. These are text encodings, not billed model usage, AI generation speed or full development-task success. Compact mode is explicit and requires clients to use structuredContent; the default readable summaries remain.

## Source and limits

The workload application entry is 122 o200k tokens; its complete four-file source is 1,369. Shared library context and compiler documentation still cost context. This is not a claim that an entire application can be generated correctly from 122 billed tokens.

The native 0.10 release runtime is built with --opt. The compiler self-reproduction/reference receipt uses the default emitter; module/type/optimiser tests separately execute both modes. Raw reports pin the compiler/runtime and frozen baseline hashes. Background host load and power state are uncontrolled. See LANGUAGE-MEASUREMENTS-0.10.json, LANGUAGE-TOKEN-FIXTURES-0.10.json and MODULES-TYPES-0.10-VERIFICATION.json. No third-party agent-language runtime was benchmarked; RELATED-LANGUAGES.md is a separate static review.
