# RF2 on ESP32-C3

These `.flow` examples target an ESP32-C3 RV32IM RAM image. The new backend
emits RISC-V instructions, an ELF and an ESP ROM image directly. A `.flow`
extension by itself does not add microcontroller support to the Mac compiler.

`uart-smoke.flow` writes `RF2 ESP32C3 UART` using UART0 FIFO registers.
`uart-echo.flow` announces READY, receives one byte, echoes it and returns an
explicit bounded timeout if no input arrives. Four actual QEMU UART cases
exercise bytes0/90/255 and no-input timeout; these are modeled serial inputs,
not physical UART wiring measurements.
`tmp102.flow` contains an RF2 open-drain GPIO driver, bounded I2C transactions,
a TMP102 register reader and exact Celsius formatting. Neither app links
Arduino, ESP-IDF, C or C++ runtime code. Vendor register definitions are used
as technical references, with pinned URLs and hashes in
[register-sources.json](register-sources.json).

## Build and boot contract

Use the separate native ESP32-C3 compiler, not the Apple Silicon compiler:

```sh
rf2-esp32c3 examples/esp32c3/uart-smoke.flow output/uart-smoke
rf2-esp32c3 examples/esp32c3/tmp102.flow output/tmp102
```

Each new output prefix produces `.elf`, `.bin` and `.map` files. Existing
outputs refuse replacement. Native binaries and source hashes for this sprint
are recorded under `artifacts/sprint-034/`; the compiler is a development
candidate, not a general release for every ESP32 board.

The RAM entry is `0x40380000` with stack top `0x3FCC0000`. Startup disables
machine interrupts and calls `main`. UART clock, baud and routing are inherited
from the ROM loader. The examples do not initialize an arbitrary cold UART or
change watchdog configuration. When `main` returns, entry parks; its status is
not an OS process exit status. Continuous operation, interrupt handling and
watchdog service need a further runtime implementation.

## Read-only temperature example

The proposed board is ESP32-C3-DevKitM-1. UART0 uses GPIO21 TX and GPIO20 RX.
GPIO4 SDA and GPIO5 SCL are exposed GPIO pins but also share external JTAG
functions. They must not be driven simultaneously by an external JTAG probe.
This board/pin contract is recorded in [board.json](board.json).

For a later authorized physical test, use a 3.3 V TMP102 setup with common
ground, ADD0 grounded for address `0x48`, and suitable external SDA/SCL pullups
to 3.3 V. RF2 sets open-drain mode before enabling these outputs. It drives a
line low or releases it, without actively driving a high level. GPIO2/8/9
strapping pins, flash pins and USB pins are not used by this bus example.
No physical device was attached, flashed or operated during this sprint.

The reader writes only the TMP102 register pointer. It reads configuration
register 1 and temperature register 0; it does not modify configuration or
threshold registers. It accepts normal 12-bit mode, checks the read-only
resolution bits, rejects extended mode and validates the unused low bits.
A successful UART line contains the wire word and its exact conversion:

```text
TMP102 00001900 25.0000C
```

That line above is a **test fixture**, not a sensor observation. The conversion
is `signed12(raw >> 4) / 16`; integer formatting uses `625/10000` Celsius per
step, without floating point. Negative and boundary values are checked as
numeric fixtures. Reporting a register word does not establish sensor accuracy,
conversion freshness, calibration or environmental temperature.

The driver assumes a single master and a stable sensor configuration during a
read. Arbitration, repeated physical sampling, shutdown/conversion scheduling,
CRC, bus recovery pulses and multi-master behavior are not implemented. Delay
loops are bounded but **uncalibrated**: 500 loop ticks are not microseconds.
Clock rates, rise times, pullups and timing margins require physical measurement.

## Failure contract

| Code | Meaning |
| --- | --- |
| `0x80000001` | Slave NACK |
| `0x80000002` | SCL stayed low for 1,000 polls on an edge |
| `0x80000003` | SDA was low at a required idle/STOP sample |
| `0x80000004` | Unsupported helper argument or register-word range |
| `0x80000005` | Invalid reserved/unused register bits |
| `0x80000006` | Unsupported resolution or extended mode |

Every failure path in the board-level transaction releases SDA/SCL. A primary
transaction error survives a later STOP error. `main` preserves a sensor error
even when UART output also fails; UART failure is returned only when the sensor
read was accepted. UART polling is separately bounded to 100,000 attempts per
byte. There is no indefinite clock-wait loop.

An electrically disconnected SDA can read high. The driver cannot distinguish
every disconnected or incomplete exchange from valid all-high samples. The
fixtures show this explicitly: omitting only the final STOP sample can still
produce an accepted word. Configuration and format checks help reject some
invalid inputs; they are not sensor authentication or perfect bus-fault detection.

## Test the protocol without a board

```sh
RF2_TEST_COMPILER=output/rf2c-033-heap-v4 \
  python3 examples/esp32c3/tests/verify_protocol.py
```

The controller extracts the actual protocol functions unchanged from
`tmp102.flow`, supplies test-only GPIO hooks, and compiles/runs the result with
the Apple Silicon compiler. It separately checks wire-operation traces against
a Python oracle. Both default and optimized host builds are checked. The model
has no ESP32 register access and is never linked into a board image.

Cases cover raw words, negative Celsius formatting, transmitted bit order,
ninth-clock ACK/NACK, address/pointer/read NACKs, all 96 positions of permanent
clock faults in a two-register read, shorter clock stretches, stuck SDA,
argument refusal, reserved/configuration bits, missing fixture samples, STOP
failure precedence, UART failure and the actual board `main` result policy.

The host controller passed 464 cases across default and optimized builds.
A second controller runs unchanged protocol, formatting and UART functions on
the new RV32 backend through Espressif QEMU ROM/SPI boot:

```sh
RF2_ESP_COMPILER=artifacts/sprint-034/engine-build-v6/rf2-esp32c3 \
RF2_ESP_QEMU=artifacts/sprint-034/espressif-qemu/qemu/bin/qemu-system-riscv32 \
  python3 examples/esp32c3/tests/verify_protocol_rv32.py
```

Its four cases use supplied +25 C and -25 C wire words, an address NACK and a
stuck clock. All four passed, including exact UART output, the actual board
`main` return status, script/clock-read bounds, released lines, restored stack
and disabled interrupts. Only GPIO hooks are replaced; the original protocol
and formatting functions remain byte-identical. Test state occupies declared
scratch DRAM at `0x3FCA0000`, separate from code and stack. Each controller
saves its input/source/compiler hashes and logs under `artifacts/sprint-034`.

These results establish host and RV32 model execution, not sensor observation.
Espressif QEMU does not supply a TMP102 on this bit-banged bus, so emulator UART
output must not be reported as a successful temperature measurement. The
remaining physical acceptance work is:

1. Identify a board and sensor, verify wiring and pullups, and authorize operation.
2. Confirm UART baud and capture the actual boot image/source hashes.
3. Measure SDA/SCL timing and open-drain voltage levels with a logic analyzer.
4. Compare actual readings with a traceable reference and account for sensor limits.
5. Inject safe disconnected-sensor/stuck-bus cases and verify release and watchdog behavior.

No speed, energy saving, universal Arduino compatibility or physical sensor
result is claimed by these examples.
