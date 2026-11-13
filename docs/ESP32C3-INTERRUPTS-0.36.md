# ESP32-C3 interrupts and checked peripheral leases, 0.36

RF2's native ESP32-C3 compiler now emits a direct machine-mode interrupt entry, private interrupt stack, integer-register save/restore and `mret`. The new `.flow` heartbeat combines periodic timer interrupts, foreground computation, watchdog progress checks and checked peripheral leases. This is a bounded bare-metal development target. **No physical board has been tested.**

[Native Mac development bundle](../dist/0.36-candidate/README.md) · [Executable tests](../tests/standalone/esp32c3_irq_verify.py) · [Qualification index](ESP32C3-INTERRUPTS-QUALIFICATION.json)

## What ran

The same firmware completed two 600-second virtual-time workloads in Espressif QEMU:

| QEMU instruction-clock shift | Firmware elapsed microseconds | Timer interrupts | Foreground result |
| --- | ---: | ---: | ---: |
| 8 | 600437180 | 60068 | 992375520 |
| 10 | 601747697 | 60176 | 992375520 |

Each run completed 2400 quarter-second foreground intervals with checked watchdog feeds. Interrupt counting starts when the timer is armed, while elapsed sampling begins after interrupt enable and the UART introduction; their origins differ. These are **emulator virtual durations and counts**, not wall-clock endurance, physical frequency accuracy or speed comparisons.

Thirty interrupt/lease controls passed. The same compiler passed the existing34-row independent compiler suite,27 timer/watchdog product controls,257 UART cases and 20 scripted sensor cases. The previously observed emulator watchdog-protection failure remains separately recorded. Native MCP exchanges passed with the unchanged nine-tool runtime. Source/binary/report identities are retained in the qualification index.

## Build and syntax

The compiler host remains Apple Silicon macOS. It emits ESP32-C3 RV32IM/Zicsr machine code, ELF32 and ROM-loadable images directly. The new native package includes the compiler, RF2 sources and five precompiled examples; compilation needs no Node, Python, C++, assembler or external linker at user runtime. GNU and QEMU are development oracles.

```sh
./rf2-esp32c3 examples/esp32c3/interrupt-heartbeat.flow NEW-PREFIX
```

The [complete example](../examples/esp32c3/interrupt-heartbeat.flow) imports the time, watchdog, UART and peripheral modules:

```rf2
interrupt fn on_interrupt(cause)
 return owned_timer_interrupt(cause)
end
```

`irq_install(on_interrupt)` takes a declared handler identifier, not an arbitrary pointer. The handler takes one u32 cause and returns u32 status. Exactly one dispatcher is supported. Handler declarations cannot be called as ordinary functions. The compiler checks the entire handler call graph and refuses loops, recursion and interrupt install/enable/restore/replenish effects. An indirect blocking helper also refuses. These restrictions produce finite admitted control flow, not a measured worst-case interrupt latency or proof against arbitrary trusted MMIO.

The interrupt setup owns the bare-metal machine interrupt domain: it masks existing CPU interrupt lines before installing RF2's vector. It is not designed to coexist with an existing FreeRTOS, Arduino or vendor interrupt runtime.

## Entry, return and failure contract

`irq_install` installs direct `mtvec` at 0x40380100 and initializes `mscratch` to the private stack top. `irq_enable()` checks the installed marker/vector and rejects foreign enabled CPU lines. Only CPU line 1 is admitted by the dispatcher. The external-interrupt transport mask is enabled separately from global `mstatus.MIE`.

`irq_save()` clears global MIE and returns its prior bit 0x8. `irq_restore(saved)` restores only that bit; a zero mask really disables global interrupts. Re-enabling requires the installed runtime and permitted CPU-line configuration. Other `mstatus` bits are not restored from caller-supplied integers. `irq_active()` reads the runtime's handler flag. These are trusted compiler intrinsics, not bounded Core or MCP effects.

The entry exchanges the foreground SP with the private stack, then saves all nonzero integer registers, interrupted SP, `mepc`, entry `mstatus`, `mcause` and `mtval` in a144-byte aligned frame. The handler calls ordinary RF2 helpers on that stack. On status0, the entry restores the frame, foreground SP and trap-return state, then executes `mret`. RF2 currently has no floating-point or vector register contract. Full processor state, RTOS context switching and nested asynchronous interrupts are not implemented.

While the handler runs, `mscratch` is zero. If a synchronous fault occurs inside the handler, a second entry detects that sentinel before writing a stack frame. It records a nested-fault status and halts with CPU interrupts masked; it does not write through a zero SP or resume the interrupted foreground code. Unknown causes and nonzero handler returns also quarantine execution. This is a conservative terminal path, not recoverable exception delivery. A separately armed watchdog can reset the machine; without it the fault remains halted.

The dispatcher admits64 handler calls per foreground progress grant. `irq_replenish()` resets those credits in a critical section after checking the installed runtime. It is forbidden on handler call paths. Missing acknowledgements or stalled foreground progress eventually exhaust the credits and quarantine interrupts. The example replenishes only after a completed foreground interval. A caller that continuously grants credits without checking progress can defeat that policy; no universal liveness guarantee is claimed.

| Status | Meaning |
| --- | --- |
| `0x80000401` | Interrupt runtime/vector/CPU-line state is unsuitable |
| `0x80000402` | Dispatcher is already installed; existing setup is retained |
| `0x80000403` | Unexpected interrupt or synchronous trap cause |
| `0x80000404` | Foreground-granted interrupt credits exhausted |
| `0x80000405` | Synchronous fault during an active handler |

The runtime records credits, fault, cause, interrupted PC, trap value, marker, accepted-handler count and active flag in its reserved diagnostic area. A successful `irq_save()` leaves global interrupts disabled even if the `mie` CSR still contains the external mask0x800. The test checks global MIE separately from that mask.

## Peripheral ownership contract

The [peripheral library](../examples/esp32c3/lib/peripheral.flow) supports two resource bundles:

| Resource | Covered hardware |
| --- | --- |
| 1 | SYSTIMER unit 0, comparator 0 and CPU interrupt line 1 |
| 2 | Timer-group0 watchdog |

`peripheral_claim(resource)` grants at most one active lease for that bundle. Handles encode a boot-local generation and resource ID. `peripheral_validate` checks the exact live token and resource; wrong-resource, stale and released handles refuse. Reclaim increments the generation. Generation exhaustion refuses rather than wrapping back to a stale handle.

Registry mutations execute with global interrupts masked and restore the saved enable state. Handler paths cannot call mutating lease functions because they reach the forbidden restore effect. The timer handler only validates the live lease, acknowledges comparator 0 and increments a31-bit event count. There are no threads or multiple CPU owners.

`peripheral_release` quiesces the comparator, source routing and interrupt line, or disarms the watchdog, before revoking the handle. If quiescence readback fails, the lease is retained for retry. This is not rollback: some hardware changes may already have succeeded. A test hook verifies retained ownership and successful retry after a simulated readback failure.

`owned_timer_start`, `owned_timer_ticks`, `owned_watchdog_arm` and `owned_watchdog_feed` require a matching live lease. Starting a timer checks its period and relevant configuration readbacks. The timer period is1000 through 1000000 microseconds under the existing16-ticks/us target assumption. Physical clock accuracy is unverified. A claim also refuses a timer/interrupt bundle already active outside the registry.

These are **checked library leases**, not affine/linear types, unforgeable capabilities or hardware isolation. An integer handle can be copied. Trusted code can read the registry, guess a live handle or bypass every helper with raw MMIO. Use the covered API consistently; arbitrary raw access is outside its guarantee. GPIO, UART, DMA, radio, other interrupt lines and other peripheral groups do not gain lease-enforced drivers from this change.

| Status | Meaning |
| --- | --- |
| `0x80000501` | Unsupported resource or invalid argument |
| `0x80000502` | Resource or required interrupt route is busy |
| `0x80000503` | Missing, stale, released or wrong-resource lease |
| `0x80000504` | Peripheral configuration/quiescence readback failed |
| `0x80000505` | Generation exhausted; no wrap/reuse allowed |

## Memory and compatibility

The 0.36 compiler retains the V1 source profile name but changes its development ABI by reserving runtime memory. Source using raw addresses must honor these new reservations; no universal byte-for-byte recompilation compatibility is claimed. Existing0.34 downloads are unchanged.

| Region | Purpose |
| --- | --- |
| IRAM 0x40380000 onward | Generated code and boot entry |
| IRAM 0x40380100 | Direct trap entry, when a handler is declared |
| DRAM 0x3FCA8100..0x3FCA811F | Interrupt diagnostics and credits |
| DRAM 0x3FCA8200..0x3FCA8217 | Boot-local lease registry |
| DRAM 0x3FCA8300 | Timer event counter |
| DRAM 0x3FCAC000..0x3FCAFFFF | Private16KiB interrupt stack |
| DRAM 0x3FCBC000..0x3FCBFFFF | Existing16KiB foreground stack |

Reserve the full0x3FCA8100..0x3FCA83FF window for the runtime. Startup clears its interrupt state and invalidates the registry marker on every boot. Lease handles do not survive reset. Numeric generations can repeat after a new boot; no cross-boot replay authentication is provided. The 144-byte trap frame plus the existing maximum admitted call/expression stack bound is12688 bytes, below the private 16KiB region. Raw memory corruption, user stack-pointer rewriting and unmodeled hardware faults remain outside that calculation.

Main still returns to the entry park loop at 0x40380018. Interrupt programs must deliberately mask and quiesce their sources before normal return. The example releases both leases and disables global interrupts before printing its final result.

## Qualification and retained failures

The [interrupt receipt](ESP32C3-INTERRUPTS-TESTS.json) includes direct QEMU interrupt delivery/release, enable-state restoration, duplicate installation, register preservation, missed acknowledgements, foreground starvation, unknown CPU line, handler error, nested exception, watchdog reset, stale/cross-resource leases, generation exhaustion, retained release ownership, operation without an installed dispatcher and invalid early enable. Eleven invalid handler programs refuse before target output publication.

The register-preservation probe uses independently assembled RISC-V instructions patched into a reserved test function. It seeds integer registers, performs a counted loop across real timer interrupts, checks values and returns through the caller ABI. The nested-exception control injects an actual `ebreak` into a test helper's image. Both images retain valid checksums/digests; these are explicit binary fixtures, not claims that the source language contains an assembler feature. The release-failure control substitutes one register read in the library. Other cases use the vendor peripheral models directly. GNU independently reassembled67204 instruction words across the final interrupt corpus, and 16203 in the separate baseline corpus.

The initial interrupt prototype printed DONE with zero interrupts because the external-interrupt transport mask had not been enabled. The implementation and the application oracle were corrected; final runs require substantial delivery counts and the independently expected arithmetic result. That failed prototype remains local evidence and is not counted as a pass.

A first600-second attempt at instruction-clock shift6 exceeded a30-second wall-time observation budget. A follow-up snapshot showed2745 deliveries, zero recorded fault and ongoing work after two wall seconds. No completed 600-second run at shift6 is claimed. Final600-second results are at shifts8 and 10, under the same30-second observation budget. The controller now retains monitor/memory diagnostics before reporting a timeout. This budget is a harness limit, not proof of firmware performance.

An early release test confused a runtime-fault option with its readback hook; its incorrect fixture failed and was corrected. Python ZIP extraction also omitted executable-mode restoration in the first package check. Native macOS extraction verifies the archive's actual executable metadata, all 38 file hashes, three signatures, a byte-identical RF2-only compiler rebuild and five identical regenerated firmware images. These harness corrections are retained, not represented as product fixes.

The known vendor emulator limitations from the [timer work](ESP32C3-TIMERS.md) remain: RTC watchdog behavior is absent, and a locked watchdog stage-register write is permitted by the model. This work does not establish physical interrupt latency, electrical behavior, RTC boot protection, brownout recovery, energy savings or universal MCU compatibility.

## Reproduce

```sh
export RF2_ESP_COMPILER=/absolute/path/to/rf2-esp32c3
export RF2_ESP_QEMU=/absolute/path/to/vendor/qemu-system-riscv32
export RF2_RISCV_TOOLS=/absolute/path/to/riscv32-esp-elf/bin
python3 tests/standalone/esp32c3_irq_verify.py
```

Tests use private emulator files, bounded output/deadlines, no network adapter and explicit cleanup. No physical device is opened or flashed. Native MCP retains its nine bounded tools; interrupt source, compilation, raw MMIO and device effects are not admitted over that interface.

Primary references are the [Espressif interrupt registers](https://github.com/espressif/esp-idf/blob/v5.5/components/soc/esp32c3/register/soc/interrupt_core0_reg.h), [vendor RISC-V vector implementation](https://github.com/espressif/esp-idf/blob/v5.5/components/riscv/vectors.S), [QEMU interrupt matrix](https://github.com/espressif/qemu/blob/40edccac415693c5130f91c01d84176ae6008566/hw/riscv/esp32c3_intmatrix.c) and [QEMU CPU interrupt adapter](https://github.com/espressif/qemu/blob/40edccac415693c5130f91c01d84176ae6008566/target/riscv/esp_cpu.c). The native emitter and lease library are RF2 source; vendor implementations are reference material, not linked firmware dependencies. The pinned source manifest preserves exact reviewed bytes and the vendor executable hash.
