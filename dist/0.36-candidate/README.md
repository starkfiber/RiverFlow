# RF2 0.36 native development bundle

Host: Apple Silicon macOS. Firmware target: bounded ESP32-C3 RV32IM/Zicsr RAM image. Ad-hoc signed, not notarized. Stable 0.17 and earlier0.34 downloads remain unchanged.

The ZIP includes native RF2 compilers, the unchanged nine-tool MCP runtime, source, checked manifests and five board examples with ELF/boot images. New support covers one non-nested interrupt dispatcher, a separate stack, fail-closed fault/storm handling and checked boot-local timer/watchdog leases. The compiler runs without Node/Python/C++/assembler/linker runtimes.

```sh
./rf2-esp32c3 examples/esp32c3/interrupt-heartbeat.flow NEW-PREFIX
./rf2 mcp
```

[Download the native ZIP](RF2-0.36-dev-macos-arm64.zip) · [SHA-256](RF2-0.36-dev-macos-arm64.zip.sha256) · [Contract and evidence](../../docs/ESP32C3-INTERRUPTS-0.36.md)

Qualification uses vendor QEMU and explicit test fixtures. Two 600-second virtual-time runs completed with over 60000 timer interrupts each. **No physical board or sensor has been tested.** RTC watchdogs, physical timing, electrical safety, nested asynchronous interrupts, floating-point state, RTOS coexistence and other boards remain unqualified. Checked leases do not sandbox trusted raw MMIO or make copied integer handles unforgeable. No automatic flashing or new MCP device authority is introduced.
