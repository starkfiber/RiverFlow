# RF2 .flow and embedded targets

## Current executable scope

A source extension does not select a CPU or operating system. The native compiler reads the supplied source text and profile; a `.flow` file can contain a supported native RF2 program. The qualified systems backend emits ARM64 Mach-O for Apple Silicon macOS. It does not emit ESP32 firmware, Arduino board images or printer MCU binaries today.

The new collection-tool applications use `.flow` entries with the existing native profile. They are host applications, not firmware or a serial-device integration. No board was flashed or physical actuator operated.

## Target-specific work

ESP32-C3 has a32-bit RISC-V processor. Its supported development flow includes a target toolchain, build tools and ESP-IDF APIs. See [Espressif's primary guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/get-started/). The ESP32 family is not one universal instruction set: other variants/toolchains require Xtensa support. RF2's current64-bit Darwin ABI and mmap-backed heap are not an embedded runtime.

Arduino support needs a board/platform definition, build recipes and the corresponding architecture/runtime integration. See the [Arduino platform specification](https://docs.arduino.cc/arduino-cli/platform-specification/). Integration with an IDE or vendor SDK does not mean RF2 has independently replaced the vendor bootloader, libraries or toolchain.

Printer firmware adds time-critical queues, peripheral behaviour and fault handling. Klipper's primary [MCU command documentation](https://www.klipper3d.org/MCU_Commands.html) describes scheduled stepper activity and sensor bounds/shutdown behaviour. RF2 is not presently qualified to replace such firmware. Host-side file or data tools are a distinct use case from driving a real machine.

## Proposed first target: ESP32-C3, not implemented

1. Specify a bounded32-bit embedded profile: arithmetic/overflow, pointer widths, static memory, stack, interrupt/effect restrictions and allocation policy.
2. Implement and independently check RV32 instruction selection and calling convention, then emit usable relocatable/object or executable artifacts. A host Mach-O renamed.bin is not firmware.
3. Define linker layout, startup/reset contract, runtime support and the exact vendor SDK boundary. An optional C/SDK bridge must be labelled a bridge, not an RF2 native backend.
4. Run pure-computation equivalence and failure tests on a suitable emulator; retain ELF/disassembly/toolchain identities. Emulation does not prove GPIO, timing, radio or physical energy behaviour.
5. Build an actual board image and qualify UART/read-only sensor behaviour on identified hardware. Record build, flash, boot, reset and observed outputs before support claims.
6. Add peripherals and interrupts individually. Printer motor/heater deployment requires actual timing, limits, watchdog and fault/recovery acceptance on the identified machine.

Host heap collections do not justify dynamic allocation inside an interrupt or a hard real-time control loop. Embedded targets need their own budgets and lifecycle rules. No universal hardware, speed, token, power or safety claim follows from current Mac tests.
