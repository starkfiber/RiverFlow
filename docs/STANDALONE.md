# Standalone RiverFlow tools

Native user tools run on Apple Silicon macOS without Node, npm, Python or C++ runtimes. The encoded minimum OS target is macOS 14; execution qualification is on the recorded local Mac, not every OS/device. Binaries are ad-hoc signed, not notarized.

Use [Start here](START-HERE.md) for package selection and [the first .flow application](FIRST-APP.md) for the tested installation/build journey. The stable 0.17 release, current 0.36 development bundle and historical release receipts remain separate. No frozen package is replaced by a documentation change.

## Developer helper

From the source checkout, explicitly select an extracted native bundle:

```sh
export RF2_HOME="$HOME/Downloads/RF2-0.36-dev-macos-arm64"
sh tools/dev.sh doctor
sh tools/dev.sh check examples/collection-tools/telemetry-summary.flow
sh tools/dev.sh build examples/collection-tools/telemetry-summary.flow summary-build --opt
printf '9,1,9,3,2' | ./summary-build/program
```

`--home DIRECTORY` before the subcommand overrides `RF2_HOME`. Spaces in paths are supported. Output directories/prefixes must be new. Builds compile and locally sign; they never execute the resulting application. A failure may leave newly created output for inspection. The helper uses shell and ordinary Mac utilities around native RF2; it adds no compiler feature or MCP effect.

`doctor` verifies the selected native executable signatures and reads runtime status. It is not a manifest verifier, publisher authenticator or notarization check. The unchanged runtime reports 0.17.0 inside the 0.36 package. Follow normal macOS approval processes; no security setting is changed by the helper.

## Direct Mac application build

The helper delegates to the existing direct route:

```sh
sh tools/build-program.sh "$RF2_HOME/rf2c" examples/collection-tools/telemetry-summary.flow another-build --opt
./another-build/program
```

Source is trusted local systems code. It may use raw OS/memory effects and is not a sandbox. Relative local imports resolve under the documented [module contract](MODULES-TYPES.md). The development compiler accepts `.flow` and `.rf2`; older stable compilers need not understand later syntax.

## Bounded runtime and Core

From the source checkout, using an explicitly selected native runtime:

```sh
"$RF2_HOME/rf2" status
"$RF2_HOME/rf2" check examples/compact/sum.rf2
"$RF2_HOME/rf2" run examples/compact/sum.rf2 '[1,2,3]'
"$RF2_HOME/rf2" mcp
```

The sum returns 6. `rf2 run` executes bounded native IR; it is not a fresh standalone compilation per call. General Core has checked/wrapping u32 arithmetic, helpers and bounded loops. The compact profile provides four reductions. See [Core semantics](NATIVE-CORE.md).

For an explicit per-program Core executable:

```sh
sh tools/build-core.sh "$RF2_HOME/rf2" "$RF2_HOME/rf2c" examples/sum.flow sum-build
./sum-build/program '[1,2,3]'
```

This route combines checked lowered source with a trusted input harness, compiles it and signs it. No speed claim follows from the existence of a native image.

## MCP and fixed capabilities

The native service retains nine bounded tools: status, check, run, lower, attendance export, invoice totals and prepared-plan lifecycle. Stdio uses JSON-RPC lines with protocol baseline 2024-11-05. Request limits include 1 MiB, depth 32, 64 object fields and 70,000 tokens. Oversized input drains before the next line; duplicate keys and malformed UTF-8 reject. These finite checks are not an independent security certification.

The plugin uses `RF2_BIN` or its documented local path. It never silently builds or falls back to Node. The host supplies AI intelligence. Raw systems compilation, caller-controlled filesystem/network paths and firmware/device operations are not MCP permissions. Internal OS entropy only seeds process-local prepared handles.

The explicit CLI attendance export and invoice workspace have separate file contracts: named inputs and new output paths, with existing targets refused. See [attendance](../capabilities/attendance.local.v1/README.md), [prepared plans](PREPARED-PLANS.md), [invoice workspace](INVOICE-WORKSPACE.md) and [capability measurements](CAPABILITY-MEASUREMENTS.md). The graphical invoice editor uses RF2-generated loopback browser forms, not a native widget toolkit; see [Studio](GRAPHICAL-EDITOR.md).

## ESP32-C3 firmware

```sh
sh tools/dev.sh firmware examples/esp32c3/interrupt-heartbeat.flow NEW-PREFIX
```

The separately selected ESP32-C3 compiler emits `.elf`, `.bin` and `.map` files. It does not flash, enumerate or open hardware. The Mac collection analyser is not an embedded program. Read [board and compiler contracts](../examples/esp32c3/README.md) and [interrupt qualification](ESP32C3-INTERRUPTS-0.36.md). Physical board/sensor/timing verification is pending.

## Native toolchain rebuild

From a source checkout with a suitable explicit prior compiler:

```sh
"$RF2_HOME/rf2c" native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
sh tools/build-runtime.sh ./next-rf2c next-runtime
./next-runtime/rf2 status
```

The runtime's composition order is authoritative in `tools/build-runtime.sh`; compiling only `native/rf2.rf2` is not a full runtime build. The compiler emits ARM64/Mach-O directly. Shell/build/test tools may use other languages as development tooling, distinct from native user runtime dependencies. Historical Python seeds and JavaScript references remain available as developer oracles. See [release history](RESEARCH-HISTORY.md), [compiler map](../native/compiler/README.md) and [test guidance](../tests/README.md).

There is no universal speed, energy, model-token, hardware or cross-platform result implied by these tools.
