# Standalone RiverFlow 0.8

Experimental native tools for Apple Silicon Mac. Users need no Node, npm, Python or C++ runtime. The minimum encoded OS target is macOS 14; actual execution is qualified on the recorded local Apple Silicon Mac, not every OS version or device. Binaries are ad-hoc signed, not notarized.

## Use the runtime

```sh
./rf2 status
./rf2 check examples/sum.flow
./rf2 run examples/sum.flow '[1,2,3]'
./rf2 run book/examples/example-4.flow '[2,3,4]'
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
./rf2 mcp
```

General Core, scalar helpers, forward calls, named arguments, checked/wrap arithmetic and bounded loops are supported by the native parser/runtime. Compact V1's four short reductions remain available. `NATIVE-CORE.md` distinguishes native IR execution from per-program machine-code emission and records the exact compatibility boundary.

## Build directly from Core

```sh
./tools/build-core.sh ./rf2 ./rf2c examples/sum.flow sum-build
./sum-build/program '[1,2,3]'
```

`rf2 lower` returns a checked systems-profile kernel fragment. The script combines it with the trusted input harness, invokes the native compiler and signs the resulting ARM64 program. It creates a new directory rather than overwriting an old build. The same effect/work/error contract is tested against the reference. No new speed claim follows from compilation.

## Application export

```sh
./rf2 attendance capabilities/attendance.local.v1/test-records.json register.csv
```

See the versioned capability's README. CLI export reads the explicit input file and writes only the explicit new CSV path. Through MCP, `attendance_export` returns CSV text/counts and accepts no filesystem path. Its counts use a compiled Core helper program. Tests use fictional programming inputs, not real student study data.

## Native rebuild

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
./next-runtime/rf2 status
```

The runtime is composed from native/rf2.rf2, core.rf2, attendance.rf2, the generated attendance-kernel.rf2 and fingerprint.rf2. Compiling only the first module is no longer a complete runtime build. The systems compiler emits ARM64/Mach-O directly without invoking Python, Node, C/C++, an assembler or a linker. The shell scripts use OS file utilities and signing. Historical Python and JavaScript implementations remain development oracles/initial-bootstrap routes.

## MCP

The native server exposes nine tools: status, check, run, lower, attendance export, invoice totals and three prepared-plan lifecycle tools. stdio uses JSON-RPC lines and protocol baseline 2024-11-05. Source/data are supplied directly. There is no arbitrary path, network, process-launch or machine-source execution tool. The client provides AI intelligence.

The launcher uses RF2_BIN or output/bin/rf2. It never auto-builds, installs dependencies or falls back to Node. Fresh source/plugin checkouts need an explicit native binary. Use one registration route per client.

Request limits: 1 MiB, nesting depth 32, object fields 64, tokens 70,000. Oversized requests drain before the next line. Duplicate object keys and malformed UTF-8 reject. This is a bounded native implementation, not an independent security audit or process sandbox.

## Evidence and history

Read the native Core, direct-kernel, attendance, compact and compiler 0.7 verification reports in docs/. Release 0.4 established four native reductions; release 0.5 established bounded systems-compiler self-reproduction. Their frozen release artifacts remain separate. The JavaScript server retains research catalog, batch execution and C emission not all migrated to native tools.

No speed, energy, token-saving, fieldwork or phone claim is established by this release.

RF2_APP_V1 is a separate fixed application-plan profile. `rf2 app plan.rf2 lines.json` reads only those explicit inputs and returns invoice totals on stdout. It is not a general Core source accepted by check/run/lower. See capabilities/invoice.total.v1/README.md and docs/CAPABILITY-MEASUREMENTS.md for the exact contract and measured limitations.

Release 0.8: nine runtime modules; 256-function systems compiler; explicit CLI invoice document/edit/PDF operations. See INVOICE-WORKSPACE.md and PREPARED-PLANS.md. MCP has no caller-controlled file access; internal OS entropy is used only to initialize process-local handle numbering.
