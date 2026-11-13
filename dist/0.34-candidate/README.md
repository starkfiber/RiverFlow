# RF2 0.34 development candidate

Compiler host: Apple Silicon macOS. Firmware target: bounded ESP32-C3 RV32IM RAM image. Ad-hoc signed, not notarized. Stable downloads unchanged.

The bundle contains native Mac RF2 compiler, native ESP32-C3 cross-compiler, bounded MCP runtime, three board examples and generated ELF/ROM images, source, manifest and MIT licence. Compilers run without Node/Python/C++/assembler/linker runtimes. The cross-compiler can be rebuilt using the bundled RF2 compiler and composed RF2 source.

Vendor QEMU ROM/SPI boot, UART TX/RX and explicitly scripted sensor-bus controls pass. **No physical board or sensor has been tested.** No automatic flashing is performed. ROM UART initialization, bus timing, watchdog and physical validation limits matter. Read [the contract and evidence](../../docs/ESP32C3-0.34.md) and the bundled board instructions. No arbitrary Arduino/Pico/ESP32-family, x86/Linux, Secure Boot, radio, speed or energy claim.
