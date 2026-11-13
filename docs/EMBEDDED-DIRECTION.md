# RF2 .flow and embedded targets

## Current executable scope

Development0.34 adds a separate native RF2-written ESP32-C3 cross-compiler. It emits RV32/ELF32 and a direct-ROM-load RAM image; actual Espressif QEMU ROM/SPI/UART and scripted sensor-bus controls pass. [Exact scope and evidence](ESP32C3-0.34.md). No physical board/sensor has been tested. The compiler host remains Apple Silicon macOS. The existing Mac systems compiler and stable bounded MCP runtime retain their contracts.

The .flow extension does not choose a target. x86, Linux applications, arbitrary ESP32 variants, Arduino and Pico support require their own implementations and qualification. The 0.33 collection apps remain Mac host applications, not physical sensor integrations.

## Target-specific work

ESP32-C3 has a32-bit RISC-V processor. Its supported development flow includes a target toolchain, build tools and ESP-IDF APIs. See [Espressif's primary guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/get-started/). The ESP32 family is not one universal instruction set: other variants/toolchains require Xtensa support. RF2's current64-bit Darwin ABI and mmap-backed heap are not an embedded runtime.

Arduino support needs a board/platform definition, build recipes and the corresponding architecture/runtime integration. See the [Arduino platform specification](https://docs.arduino.cc/arduino-cli/platform-specification/). Integration with an IDE or vendor SDK does not mean RF2 has independently replaced the vendor bootloader, libraries or toolchain.

Printer firmware adds time-critical queues, peripheral behaviour and fault handling. Klipper's primary [MCU command documentation](https://www.klipper3d.org/MCU_Commands.html) describes scheduled stepper activity and sensor bounds/shutdown behaviour. RF2 is not presently qualified to replace such firmware. Host-side file or data tools are a distinct use case from driving a real machine.

## ESP32-C3 development implementation and remaining gates

1. The bounded32-bit development profile now exists; extend and qualify its arithmetic/overflow, pointer widths, static memory, stack, interrupt/effect restrictions and allocation policy.
2. Direct RV32 instruction selection, calling convention, ELF32 and ROM-image generation now have independent instruction and emulator evidence. Extend their scope deliberately. A host Mach-O renamed.bin is not firmware.
3. Define linker layout, startup/reset contract, runtime support and the exact vendor SDK boundary. An optional C/SDK bridge must be labelled a bridge, not an RF2 native backend.
4. Pure-computation, failure and UART emulator tests now run; retain ELF/disassembly/toolchain identities and expand coverage as implementation grows. Emulation does not prove GPIO, timing, radio or physical energy behaviour.
5. Build an actual board image and qualify UART/read-only sensor behaviour on identified hardware. Record build, flash, boot, reset and observed outputs before support claims.
6. Add peripherals and interrupts individually. Printer motor/heater deployment requires actual timing, limits, watchdog and fault/recovery acceptance on the identified machine.

Host heap collections do not justify dynamic allocation inside an interrupt or a hard real-time control loop. Embedded targets need their own budgets and lifecycle rules. No universal hardware, speed, token, power or safety claim follows from current Mac tests.
