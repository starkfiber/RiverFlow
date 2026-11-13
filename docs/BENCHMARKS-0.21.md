# What RF2 can do, and what the measurements actually show

13 November2026. One Apple Silicon Mac. Fresh process timings include startup; nine rotated trials per native CLI task, after a retained warmup. Raw inputs, sources, binary hashes, losses and ranges are in the linked reports. Small differences on this uncontrolled host are not robust rankings.

## Fresh task measurements

Median milliseconds, lower is better. C and Python use the specifically named algorithms/libraries; these are task comparisons, not identical implementations.

| Task | RF2 0.21 | C/Clang comparator | Python comparator |
| --- | ---: | ---: | ---: |
| mixed | 3.552 | 3.563 | 152.127 |
| conditional | 1.603 | 5.702 | 10.390 |
| latency-summary | 1.771 | 1.714 | 13.864 |
| file-sha256-32KiB | 2.885 | 1.842 | 11.109 |
| sha256-batch50-32KiB | 55.680 | 2.486 | 12.240 |

For the conditional reduction, the equally specialized C formula measured 1.771ms; the table shows the ordinary C loop. Both specialized paths avoid the repeated loop. Mixed arithmetic is similar to C within this experiment. Sort uses RF2 insertion sort versus C qsort and Python built-ins. File hashing compares RF2 software SHA-256 against optimized library implementations.

The batch of50hashes is decisive: once startup is amortized, RF2 loses to both Python/hashlib and Clang/CommonCrypto. The native one-file win over a fresh Python process does not mean RF2 has the faster hash implementation. The actionable bottleneck is RF2 SHA-256, not a missing universal transistor shortcut.

## Real HTTP application comparison

Fresh loopback measurements:480timed requests, three single-worker backends, two routes, concurrency1and4, five rotated batches per cell. Bodies and bounded protocol failures were checked. The RF2 server was compiled with the current compiler; its temporary owned process was stopped. The Linux/Python arm remains an existing QEMU/HVF guest, not the new RF2 bounded hypervisor.

| Sequential median, ms | RF2 native | Python host | Python Linux guest |
| --- | ---: | ---: | ---: |
| Static page | 0.101 | 0.123 | 0.236 |
| Compute10000 | 0.138 | 0.632 | 0.802 |

The RF2 backend is faster on these two measured routes. Different implementations, parsers, runtime/OS and VM forwarding contribute; this is not a general language result. The parallel Linux arm has occasional large tails, retained in the raw report. The experiment establishes neither internet capacity nor arbitrary browser/platform compatibility.

## MCP measurements and AI-task gap

Persistent local native stdio, nine rotated trials with20calls each per cell. These measurements include host JSON, pipes, native execution and authentication. They exclude model generation.

| Input bytes / steps | 0.20 run ms | 0.21 run ms | 0.21 verify ms |
| --- | ---: | ---: | ---: |
| 8 / 1 | 0.0666 | 0.0679 | 0.0677 |
| 128 / 8 | 0.2224 | 0.2299 | 0.2251 |
| 128 / 32 | 0.2573 | 0.2488 | 0.2520 |

These are similar bounded tool costs, not evidence of a general MCP speed improvement. Actual complete AI-task latency, billed tokens, correctness-per-dollar and autonomous repair success have NOT been measured. Earlier compact-interface/tokenizer fixtures count their exact encoded examples, not provider usage. A proper AI study needs matched tasks, model/version/settings, randomized language order, tests held constant, actual provider receipts and failures counted. No controlled provider-inference benchmark or model training was performed. The coding host supplied AI assistance, but that was not an instrumented AI-task trial.

## Parity and retained evidence

RF2 is not a100%replacement for Python, C or assembly. Major gaps include floating point, arbitrary precision, general heap/ownership transfer, concurrency, comprehensive libraries, broad FFI, other CPU/OS targets and every machine instruction/ABI. Native ARM64 emission and a few complete apps do not close those gaps. [Capability map](CAPABILITY-MAP.md).

The [inventory](BENCHMARK-INVENTORY.json) lists19retained benchmark reports, including legacy native/C backend, optimizer, collections, invoice/reuse/UI, contract overhead, WASM and website experiments. Historical reports are labelled rather than combined into a misleading aggregate score. Three benchmark families were rerun in this sprint: native CLI tasks, HTTP applications and MCP. Some entries are microbenchmarks, not real-world apps.

[Fresh CLI raw report](APPLICATION-BENCHMARKS-0.21.json) · [HTTP raw report](HTTP-BENCHMARKS-0.21.json) · [MCP raw report](MCP-BENCHMARKS-0.21.json).
