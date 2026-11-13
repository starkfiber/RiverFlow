# RiverFlow engineering history

Historical experiments retain their original measurement scope. This page is a record, not a list of stable release guarantees. Start with the [current project overview](../README.md) or [capability map](CAPABILITY-MAP.md).

## Native memory research update: 0.25 source candidate

Bulk zeroing, vector byte conversion, two-span SHA chaining and guarded scalar frame omission are implemented and tested. In the measured 64-byte repeated-hash task, median time fell from 1.103 to 0.666 ms; specialised ARM C took 0.627 ms. The whole project-file workload did not show a reliable improvement. One Mac, finite tests, stable downloads unchanged.

[Implementation, measurements and limitations](NATIVE-MEMORY-0.25.md). The book includes the new research chapter. These changes use established ARM instructions and compiler techniques; they do not claim new physics or universal language superiority.

## Research direction: make results challengeable

The [Evidence Contract candidate](EVIDENCE-CONTRACT.md) combines five tested mechanisms in a native RF2 application: permission and work checks, atomic byte transformations, independent execution, source-bound SHA-256 receipts and self-contained replay capsules. [Further tests and measured overhead](CONTRACT-REPLAY-RESEARCH.md) retain shared-defect and unsigned-receipt negative controls. It is a research candidate built with 0.17, separate from the released package. These mechanisms have [established prior art](FIVE-HYPOTHESES-REVIEW.md); their integration is the experiment.

The [ten-language source audit](TOP-TEN-LANGUAGE-AUDIT.md) compares RF2 with selected implementations from Python through C, SQL and Go, with assembly as a separate low-level reference. It includes an A–Z acceptance ledger and marks missing capabilities explicitly. Popularity and shorter spelling do not prove correctness, speed or adoption.


## Earlier 0.24 preparation measurements

General byte-swap instructions, safer call-preservation selection and a native file-checksum utility. In-process 20,000 x64-byte hashing improves from **6.06 ms to 1.09 ms**. CommonCrypto measures3.42ms; a direct specialised C implementation remains faster at0.62ms. These warm-loop measurements exclude startup and initialization. [Scope, tests, failures and all comparisons](SHA-PREPARATION.md).


## Earlier 0.23 SHA measurements

Direct ARM SHA2 lowering reduces the matched 50-hash task from **35.59 ms to 2.56 ms**. The 2,000-hash task measures **22.72 ms RF2**, **22.46 ms C/CommonCrypto**, and **33.29 ms Python/hashlib**. RF2 retains the software fallback. These are local task measurements, not a universal speed claim or stable release. [Tests, method and remaining gap](SHA-ACCELERATION.md).

## Earlier 0.22 measurements: native rotate

A direct32-bit rotation primitive reduces the selected50-hash SHA batch median from56.98to35.35ms in21matched trials. Library baselines remain faster. This is a source candidate; stable downloads are unchanged. SFE connector authentication was verified before publication. [Evidence and limits](ROTATE32-0.22.md).

## 0.21 development: owned mappings and authenticated guest entry

RF2 now owns guest mapping lifetimes and authenticates a fixed boot contract with shared-key HMAC. The final local suite passed 34 guest runs, 77 refusals, 23 mapping scenarios in both compiler modes and six controlled fault substitutions. A stronger test found an older HVC #0 counterexample; the current profile requires HVC #1. [Contract and limits](BOOT-CONTRACT-0.21.md).

RF2 is not a complete Python/C/assembly replacement or universally faster. Fresh task, HTTP and MCP measurements retain both wins and losses, including the slower RF2 repeated-hash path. [Benchmark tables and raw reports](BENCHMARKS-0.21.md) · [Capability gaps](CAPABILITY-MAP.md).

## 0.20 development: owned VMs and bounded guest images

RF2 now checks VM/vCPU ownership, validates a small guest-image format and enforces a virtual-timer time slice for admitted looping guests. The final local suite passed 136 guest executions, 31 image refusals, 52 branch-admission checks and 14 ownership scenarios in both compiler modes. MCP authority is unchanged. [Implementation, clock correction and limits](VM-OWNERSHIP-0.20.md) · [Run the native image loader](../examples/vm-runner/README.md).

## 0.19 foundation: direct guest control and portable computation

RF2 now emits explicit Hypervisor framework bindings and runs its own bounded VMM program without QEMU. Forty local guest runs cover arithmetic, permission faults, cleanup and same-process VM reacquisition. Apple supplies hardware virtualization; Linux boot and devices remain future work.

The native RF2 WebAssembly encoder passed 588 differential cases across generic and optimized modes. A guarded sum specialization reduced its selected local WASM medians by 63–66%; the simpler JavaScript baseline remained slightly faster for 64 words. [Evidence, losses and next gates](FOUNDATION-0.19.md) · [Try the browser lab](https://starkfiber.github.io/RiverFlow/lab/) · [Cloud candidate and free-service boundaries](FREE-CLOUD-0.19.md).

The browser uses compiled WASM when available and labels its limited JavaScript fallback. Android 4.1 device compatibility and Cloudflare deployment are not claimed. Existing MCP authority is unchanged.

## Frozen 0.18 development candidate

A separate native verifier, HMAC-authenticated receipts and three bounded contract MCP tools are working. The eligible XOR/reversal path has matched before/after measurements; complete authenticated MCP timings are recorded separately. [Trust model, setup and measured evidence](TRUST-0.18.md).

Shared-key authentication is not a public signature or proof of uncompromised hardware. The separate algorithm catches the tested two-path defect; a shared three-path defect still escapes. Stable downloads remain 0.17. The separate [0.18 native candidate bundle](../dist/0.18-candidate/) contains the trust service, verifier, compiler, website and VM controller, with a pinned checksum. It is ad-hoc signed, not notarized.

## Now running: one website, three execution paths

A native RF2 server, host Python control and Python inside a real HVF Linux guest serve the same page and checked computation. RF2's VM controller launches QEMU; QEMU supplies virtualization. The two local 3,600-response comparisons and their confounders are [fully recorded](STACK-LAB-0.18.md). A second hosted ARM Mac also exposed and verified a fix for the compiler's macOS 15 loader metadata. The exact candidate archive passed local and hosted checks; stable downloads remain 0.17.

