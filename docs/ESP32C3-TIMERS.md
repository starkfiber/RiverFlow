# ESP32-C3 timers and watchdogs

RF2 now includes reusable `.flow` libraries for SYSTIMER time snapshots, bounded delays, TIMG0 watchdog supervision and reset reporting. The native ESP32-C3 compiler is unchanged from the qualified 0.34 development build. This is a library and application extension, not a new CPU backend or a claim of physical board qualification.

The [timed heartbeat](../examples/esp32c3/timed-heartbeat.flow) completed 480 quarter-second intervals in each of two vendor-QEMU runs, with a watchdog feed after every successful interval. Measured firmware SYSTIMER elapsed times were 120.011900 and 120.179177 seconds at QEMU instruction-clock shifts 6 and 10. These are **emulator virtual durations**, not 120-second wall-clock tests, performance benchmarks or measured electrical timing.

## Use the libraries

From the source checkout, use an explicitly selected native compiler from the [0.34 bundle](../dist/0.34-candidate/README.md):

```sh
/absolute/path/to/rf2-esp32c3 examples/esp32c3/timed-heartbeat.flow NEW-PREFIX
```

The existing bundle is unchanged and does not include these newly added libraries. Use the complete source example and its `lib` directory together. The compiler emits RV32 machine code and boot images directly; no Arduino CLI, ESP-IDF runtime, Node, C++ or external assembler is needed for this compilation. Python and the vendor emulator remain development test tools.

```rf2
profile RF2_ESP32C3_V1
use "lib/time.flow"
use "lib/watchdog.flow"
fn main()
 let failure=watchdog_arm_ms(1000)
 if failure
  return failure
 end
 set failure=timer_init()
 if failure
  return failure
 end
 set failure=timer_delay_us(250000,100000)
 if failure
  return failure
 end
 set failure=watchdog_feed()
 if failure
  return failure
 end
 return watchdog_disarm()
end
```

Each library has an exclusive foreground owner by contract. This is not a compiler-enforced ownership type, thread-safe driver, ISR facility, RTOS scheduler or Arduino API compatibility layer. Raw MMIO remains trusted and can bypass library conventions. No hardware is opened or flashed automatically.

## Time contract

`timer_init()` enables the peripheral bus and SYSTIMER unit0 without deliberately resetting the count. It disables unit0 CPU-stall settings and captures a snapshot. `timer_capture()` clears the previous valid flag, requests a new snapshot, and polls at most64 times. It returns status separately from timestamp data; timestamp bit31 is valid data.

After a successful capture, `timer_us32()` combines both halves of the latched counter and converts16 ticks per microsecond into a wrapping u32 microsecond value. The target contract assumes the normal40MHz XTAL-derived SYSTIMER clock. It has not been physically calibrated. Snapshots must not be interleaved by other owners. Readback before initialization or after a failed capture is not a fresh timestamp.

`timer_elapsed(now,start)` uses wrapping subtraction. `timer_due(now,deadline)` uses the half-range convention: comparisons are meaningful only when the relevant times are separated by less than2^31 microseconds. `timer_delay_us(duration,poll_budget)` refuses durations above0x7fffffff and a zero poll budget. A zero duration with a positive budget succeeds immediately. Every wait also has an independent iteration budget, so a stopped counter can return an error. Budgets count polls, not microseconds; an insufficient budget can fail even with a functioning clock. Delays busy-poll and never feed the watchdog automatically.

| Status | Meaning |
| --- | --- |
| `0x80000101` | Timer initialization or snapshot did not become valid |
| `0x80000102` | Delay exhausted its poll budget |
| `0x80000103` | Invalid delay arguments |

## Watchdog and reset contract

`watchdog_arm_ms(timeout)` accepts10 through60000ms, takes over TIMG0 watchdog supervision from ROM flashboot mode, explicitly selects the40MHz XTAL source, and configures a40000 prescaler for1000 watchdog ticks per second. Stage0 requests a system reset; later stages are disabled. Register updates are explicit, the watchdog is fed, write protection is restored and relevant configuration is read back. These values are target assumptions, not a physical timeout measurement. Other timer-group timers are not deliberately reconfigured.

`watchdog_feed()` refuses a disabled or incompatible configuration. It unlocks, feeds and relocks the watchdog. Feed only after the application has checked useful progress. `watchdog_disarm()` explicitly clears both ordinary enable and flashboot protection; clearing ordinary enable alone is insufficient. Invalid arm arguments leave existing supervision unchanged. A configuration/readback failure is reported, but is not a transaction or guarantee that the previous watchdog remains active: review or explicitly disarm/reset after failure. No automatic feed hides a stalled operation.

`reset_cause()` exposes the raw low6-bit RTC reset reason. `system_reset()` requests a software system reset; success never returns. If a test hook ignores that request, the function returns an error after100000 loop iterations. This fallback is an iteration bound, not a calibrated reset deadline.

| Status | Meaning |
| --- | --- |
| `0x80000201` | Invalid watchdog timeout |
| `0x80000202` | Configuration or disarm readback failed |
| `0x80000203` | Watchdog is not in the expected armed configuration |
| `0x80000204` | Software reset request returned without taking effect |
| `0x80000301` | UART output exhausted its polling budget |

The heartbeat checks UART failures, keeps primary errors visible, and leaves supervision armed on failures before deliberate shutdown. After successful work it disarms the watchdog before returning. The current ROM-image startup still parks after `main`; it does not become an RTOS or install interrupt handlers.

## Executed qualification

The [test receipt](ESP32C3-TIMERS-TESTS.json) records27 passing product controls and **one separately classified emulator limitation**, not28 protection passes. Tests include ordinary delays at two instruction-clock scales, microsecond-counter rollover, frozen-clock recovery, invalid arguments, disarm survival beyond expiry, protected configuration writes, withheld feeds, shorter rearming deadlines, invalid rearming preserving supervision, and software reset causes. Watchdog reset cases require causes1,7,7; software reset requires1,3,3. Returning a result before the required reset fails the oracle. Finite-return cases check restored SP, entry return loop and disabled machine interrupts.

Four failure controls use explicit test substitutions: never-valid snapshots, ignored software reset, incorrect watchdog readback and an always-full UART status. Their results verify RF2 error paths; they are not evidence that the underlying emulator or physical peripheral produced those faults. The UART control copies the reviewed function with only its status-read expression replaced. Other controls execute the vendor peripheral models directly.

The source reviews and models expose two limits:

* RTC watchdog behavior is not implemented in this vendor emulator. This library does not claim RTC watchdog takeover, boot-time protection, power-loss/brownout recovery or physical reset behavior.
* The emulator rejects locked writes to watchdog configuration0 but permits locked writes to the stage-hold register. RF2's own calls use the documented unlock/write/relock sequence; the permissive model cannot prove physical register protection. The discrepancy is retained in the receipt as a failed protection expectation, not concealed as a pass.

Fresh regressions also passed257 UART boot cases and20 RV32 scripted sensor cases. Direct native MCP discovery, status, embedded-source rejection and subsequent bounded computation passed with the same nine-tool runtime. There is no new compiler, flashing, raw GPIO or device authority over MCP. The system Node SDK harness was already blocked by a missing host library, so no fresh SDK pass is claimed. See the [qualification index](ESP32C3-TIMERS-QUALIFICATION.json).

Reproduce with reviewed vendor QEMU and native compiler paths:

```sh
export RF2_ESP_COMPILER=/absolute/path/to/rf2-esp32c3
export RF2_ESP_QEMU=/absolute/path/to/qemu-system-riscv32
python3 tests/standalone/esp32c3_time_verify.py
```

The controller creates new evidence directories, enforces wall-clock and UART-output limits, closes its emulator process, and records source/binary hashes. No physical port or external network is used. Physical timer accuracy, actual UART baud, oscillator changes, sensor wiring, RTC watchdogs and extended operation still need identified hardware.

## Reference review

Register contracts came from [Espressif SYSTIMER LL](https://github.com/espressif/esp-idf/blob/v5.5/components/hal/esp32c3/include/hal/systimer_ll.h) and [MWDT LL](https://github.com/espressif/esp-idf/blob/v5.5/components/hal/esp32c3/include/hal/mwdt_ll.h), checked against register definitions. Emulator behavior was examined in the [vendor timer model](https://github.com/espressif/qemu/blob/40edccac415693c5130f91c01d84176ae6008566/hw/timer/esp_timg.c). The vendor binary is the previously pinned9.2.2/20260417 release; it was not rebuilt from those sources. These are existing peripheral mechanisms, not new transistor physics.

Three Arduino MCP source reviews and the Arduino-ESP32 timer API informed the [integration review](ARDUINO-MCP-REVIEW.md). No third-party Arduino server was installed, executed or silently attached. The RF2 library is original source; reviewed vendor and server implementations are not linked or copied into the firmware.
