# RF2 0.20 development: owned VMs, bounded image loading and cancellation

13 November 2026. Native source development, not a new stable binary release.

## Implemented boundary

The compiler now supports `resource Machine(IO,vm)` and `resource CPU(IO,vcpu)`. A CPU constructor names its live VM parent. Owners are function-local and cannot be copied, rebound, returned, passed to helpers or supplied as raw scalar arguments. Typed operations return IO results that must be handled. Explicit parent release requires its live children to be released first. Ordinary returns perform reverse-order cleanup; failure changes a successful result into a cleanup error, while preserving an existing primary error. There is no general move/borrow system, cleanup on fatal traps/signals or safety guarantee for raw trusted platform calls.

The runner takes a private RF2G020 image snapshot before acquiring VM resources. It checks the exact header, length, ISA, entry, reserved fields and every instruction. The 4 KiB code bound and separate 16 KiB code/data pages remain explicit. Admitted instructions are NOP, ADD X0,X0,X1, STR X0,[X2], HVC #0 and an immediate B whose destination is inside the image. The host fixes X2 to the data page. No admitted instruction can change timer registers, X2 or mapping permissions. This is a small validated instruction language, not arbitrary ARM64, ELF or Linux loading. The format does not authenticate authorship.

The VMM sets Apple's virtual timer, then runs the vCPU. `vm_clock_ticks()` uses mach_absolute_time and `clock_timebase(pointer)` supplies the conversion ratio. A timed looping image exits with HV_EXIT_REASON_VTIMER_ACTIVATED. A requested pre-entry cancellation uses hv_vcpus_exit and returns HV_EXIT_REASON_CANCELED. The test controller timeout is a failure guard, not the implementation of cancellation. Host scheduling prevents a hard real-time upper bound. There is no concurrent external cancellation protocol or guarantee for arbitrary code that can disable its timer.

## Actual observations

The final suite passed 136 guest executions: 72 arithmetic/entry/repeated-operation cases, 36 timer exits and 28 explicit cancellations including admitted-branch cases. It also rejected 31 malformed or unsupported input files, checked 52 branch encodings against an independent range rule, and checked 14 ownership scenarios in both default and optimized builds. These scenarios include partial acquisition, primary errors, copying, raw-handle escape, incorrect parent release, use after release and injected cleanup failure. Another VM is acquired before process exit, so process termination is not the cleanup oracle.

The 36 timer cases use two looping images and requested slices of 1, 2, 5, 10, 20 and 50 ms, repeated three times. Recorded in-run intervals ranged from about 1.0003 to 50.0020 ms on this Mac. These are timer observations, not a speed benchmark or a universal latency bound. Full raw ticks, time conversion and process wall times remain in the receipt.

The first prototype used an architectural CPU counter as though it shared the timer's mach_absolute_time origin. That was wrong on this host: a requested 10 ms loop exited immediately. The frozen failing executable and its observation are retained locally. The correction uses the documented platform clock domain and a timebase conversion. The final loop test requires both the platform's timer exit reason and a substantial elapsed interval; merely returning promptly would not pass.

A separate comparison checked three arithmetic inputs, including u32 maxima, against the frozen 0.19 guest executable. Values and stored results agree. An unoptimized new runner also passed arithmetic and timer cases. No speed comparison is claimed: the new runner performs image validation and timer/ownership work absent from the old experiment.

## Regression evidence

The original 0.19 raw VMM still passed its 40 guest tests under the new compiler. Native compiler self-generation, retained encoder byte comparisons, the full Core runtime corpus and nine-tool SDK checks passed. The generated Core runtime retains its prior byte identity. The WASM suite passed 588 differential cases. Existing owned-file tests passed. The trust service passed 520 checks, 245 key/protocol checks and the independent three-tool SDK session with a disposable key. Core and MCP receive no new hardware or raw guest authority.

All new execution observations were local to one Apple Silicon Mac. The previous hosted run remains a 0.19 result; it is not relabelled as 0.20 qualification. Stable 0.17 and the exact frozen 0.18 archive are unchanged.

## Reproduce and continue

See [runner instructions and format](../examples/vm-runner/README.md), [VM test receipt](VM-OWNERSHIP-0.20-VERIFICATION.json), [baseline comparison](VM-0.20-BASELINE-COMPARISON.json), [compiler regression](COMPILER-0.20-REGRESSION.json) and [other regressions](VM-0.20-REGRESSIONS.json). Developer orchestration is separate from native executable runtime requirements.

Next work: owned mapping buffers with lifetime checks, a clearly defined external cancellation service, authenticated image provenance and an independently specified guest boot contract. Interrupts and virtual devices must precede Linux claims. Wider instruction support needs a new cancellation threat analysis rather than silently trusting the current timer rule.

Primary API references: installed macOS SDK Hypervisor hv_vcpu.h/hv_vcpu_types.h (virtual timer mask, offset and exit contract), and Apple's documentation for [timer masking](https://developer.apple.com/documentation/hypervisor/hv_vcpu_set_vtimer_mask(_:_:)), [system-register access](https://developer.apple.com/documentation/hypervisor/hv_vcpu_set_sys_reg(_:_:_:)) and [explicit cancellation](https://developer.apple.com/documentation/hypervisor/hv_vcpus_exit(_:_:)). Apple supplies virtualization. RF2 supplies the compiler, owned wrapper, admitted-image validation and host control flow.
