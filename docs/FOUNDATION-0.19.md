# RF2 0.19 foundation: direct guest control and WebAssembly

13 November 2026. Development source; the frozen 0.18 candidate remains unchanged.

## What now works

RF2 compiles explicit, allowlisted scalar calls into Apple's Hypervisor framework through direct Mach-O bindings. The native VMM creates a VM, maps separate code and data pages, configures a vCPU, handles exits and releases resources. It does not launch QEMU or another process. Apple owns the virtualization mechanism; RF2 owns the VMM program and lifecycle logic.

A second native RF2 program emits WebAssembly binary directly from the checked Core frontend. The module has no OS imports or WASI, fixed four-page memory and exports run/status/work/memory. It supports the existing bounded Core integer operations, scalar helpers and non-nested main loops. Raw systems programs, Hypervisor calls, DOM, files, threads and arbitrary Python/C++ compatibility are not admitted to this backend.

## Direct VM observations

Forty guest runs tested runtime input arithmetic and three controlled fault modes. The three-instruction guest adds X0 and X1, stores through X2 and executes HVC. Writable data receives the expected sum. Read-only data and unmapped stores fault without changing the protected data. Removing code execute permission produces an instruction abort. Duplicate VM creation, unaligned mappings and an invalid register are refused. An unentitled copy cannot create the VM.

Cleanup results are checked, and the same process reacquires/destroys a VM after cleanup. This distinguishes explicit resource release from reliance on process exit. The test controller has an external timeout; the VMM itself does not yet provide a general guest deadline or arbitrary-code execution service. No Linux boot, interrupt controller, timer device, console, virtual disk, networking or physical phone result is claimed.

The first guest ADD constant was encoded incorrectly. A retained executable returns the wrong arithmetic and the checker rejects it. The corrected encoding and all final cases passed. A truncated framework path during initial Mach-O emission was also corrected. Preserve these failures as development evidence.

## WebAssembly differential checks and bounded optimization

The optimized and generic encoders passed 588 differential cases for values, arithmetic refusals and exact Core work counts, plus eleven boundary/output-path checks. Cases cover checked/wrapping sums, multiplication, popcount, nonzero, scalar helpers, loop/load limits, work exhaustion, reset after failure and refused existing/symlink outputs. The retained Core runtime is version 0.17, the unchanged Core baseline used by the 0.18 application candidate. Separately, the exact 0.18 compiler rejects the new platform intrinsic; current compiler fixed-point/runtime/SDK checks passed.

The generic encoder initially used unsigned LEB encoding for a positive signed i32 work-limit constant. Inspection identified the signed-constant boundary. Replaying the work-cap case against the frozen first encoder confirmed that it incorrectly accepted excess work; the corrected writer uses signed encoding and rejects at work 1,048,577. This correction is not a result of model training.

The sum optimization is limited to a structural four-node, one-function IR shape: zero accumulator, bounded loop, indexed input load and add. Admission establishes count <= words, aligned pointer range inside fixed memory and count <= 65,536. The load is therefore in bounds. Work is 3 + 3n, at most 196,611, below the 1,048,576 cap. If checked addition fails on zero-based iteration j, work remains 3 + 3(j + 1), with the same overflow status. The optimizer retains that error point, result convention and work accounting. Other shapes use the generic path. --generic preserves a separately selectable comparator.

This is guard hoisting and loop specialization, not novel Boolean logic or proof of arbitrary compiler transformations. Finite cases supplement, not replace, the eligibility argument.

## Measured costs, including the loss

One Node/V8 process rotated optimized WASM, generic WASM and a simpler checked JavaScript sum across 21 trials per size. Identical inputs and result checks were retained.

| Words | Optimized WASM median us | Generic WASM median us | Direct JS median us |
| --- | --- | --- | --- |
| 64 | 0.0338 | 0.0997 | 0.0313 |
| 1,024 | 0.5097 | 1.3787 | 0.9346 |
| 16,384 | 7.9675 | 21.5867 | 15.0521 |

The optimization reduced the selected WASM medians by about 63–66%. The simpler JavaScript baseline was still slightly faster at 64 words. These are in-process microbenchmarks, not browser/network latency, native-vs-VM timing, device performance, energy or token savings. The initial generic-only and separate confirmation measurements remain local alongside the paired final report.

## Browser and legacy route

The RF2 native HTTP subset serves a real page, ES5 host glue, source and module on loopback port 18790. Browser actions confirmed a WebAssembly result of 42, checked overflow refusal and the explicitly selected JavaScript compatibility result. The isolated browser/Worker tests passed 34 checks. WhatIF's final 60-request GET suite passed and its evidence hashes verified; capacity and complete security remain unestablished.

The fallback is a limited JavaScript sum for this example, not a complete RF2 runtime. It uses no fetch, async syntax, BigInt or required WebAssembly API. Browser feature detection selects the path. Android 4.1's stock WebView was WebKit-based; an OS label alone does not establish the capabilities of an installed alternate browser. Chrome 57 introduced default WebAssembly. No Android 4.1 device or original WebKit engine was executed, so physical compatibility, browser installation and TLS remain open.

## Cloud and review boundaries

A Cloudflare Worker candidate runs the RF2-emitted arithmetic behind small platform glue. It was tested locally, not deployed. No Cloudflare credentials, Redis hive, inference or weight training are configured. Free public GitHub CI is the cloud execution used. See FREE-CLOUD-0.19.md for dated provider limits and the retirement of GitHub Models.

Reverse Lab inspected actual Mach-O metadata and the entitlement on the final tested VMM artifact. It observed separate RX code and RW data segments and the Hypervisor dependency. Its import inventory is incomplete, and its generic coverage gate supports JavaScript graphs rather than this native operation. The native gate returned unsupported; it is not a coverage pass. A profileless snapshot save was rejected, so complete raw observation envelopes were retained separately and the target closed normally. Runtime guest results are separate evidence.

## Build and continue

Developer builders use Python to compose source and run qualification; emitted tools are native RF2. Build with tools/build-foundation.py, tools/build-wasm.py and tools/build-browser-lab.py. The VMM requires the explicit hypervisor entitlement supplied in examples/hypervisor. The trusted systems intrinsic accepts only literal Hypervisor names and its finite API/arity table. It is not exposed through bounded Core or MCP.

Next gates: typed VM/vCPU owners and cleanup error propagation; a VMM-enforced cancellation/deadline; guest image loading and boot contracts; then explicit interrupt/device models before claiming Linux boot. Broader WASM programs and original legacy browser/device tests need their own evidence. Keep the 0.18 archive frozen, require exact new artifact qualification before another release and retain all smaller-baseline losses.

Evidence: HYPERVISOR-0.19-VERIFICATION.json, WASM-0.19-VERIFICATION.json, WASM-0.19-MEASUREMENTS.json, BROWSER-WORKER-0.19-VERIFICATION.json and COMPILER-0.19-REGRESSION.json. Hosted outcomes, when complete, are recorded separately; hosted VMs do not supply nested hardware-virtualization proof.

Primary platform references: https://developer.apple.com/documentation/hypervisor ; installed macOS SDK Hypervisor hv_vm.h/hv_vcpu.h/hv_vcpu_types.h ; https://webassembly.github.io/spec/core/binary/modules.html ; https://v8.dev/blog/v8-release-57 ; https://source.android.com/docs/compatibility/4.1/android-4.1-cdd.pdf .

Final hosted qualification: https://github.com/starkfiber/RiverFlow/actions/runs/43331849687 passed. It rebuilt the compiler and WASM encoder, ran 588 differential cases and 34 isolated browser/Worker checks, and requalified the unchanged 0.18 package and trust suites. The retained Core baseline required the known loader-container repair on macOS 15; crashes now reject explicitly rather than being classified as overflow. This is free public CI execution, not nested hardware virtualization or model training. Full receipt: FOUNDATION-0.19-SECOND-HOST.json.
