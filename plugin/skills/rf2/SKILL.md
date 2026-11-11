---
name: rf2
description: Write, check and run RiverFlow compact native computations, inspect exact profile boundaries, and develop its compiler and evidence.
---
# RiverFlow RF²

Use rf2_status first. The default 0.4 server is a standalone Apple Silicon macOS executable. Read docs/STANDALONE.md for its exact contract.

## Native compact profile

Use an explicit five-token program, for example:

```text
rf2 v1 checked
sum input
```

Arithmetic is `checked` or `wrap`; operation is `sum`, `squares`, `bits` or `nonzero`, followed by `input`. General Core helpers, arbitrary statements, service plans and machine-profile source are not admitted by this server. Unknown syntax/effects reject. Do not invent working operations.

Use rf2_check for the compact plan and rf2_run for bounded u32 data, with an optional prefix count. The tools have no arbitrary file, network, process or phone access. The CLI can read an explicit source file and print its exact Core expansion. A connected host supplies intelligence; the binary has no embedded Astra or SLM model.

The launcher selects RF2_BIN or output/bin/rf2. It never builds code, installs npm or silently falls back to Node. A source checkout needs an explicitly built native binary. If unavailable, explain the missing native target rather than claiming a working native tool call.

## Compiler truth

The runtime/MCP implementation is native/rf2.rf2, profile RF2_SYSTEM_A64_V1. The historical bootstrap/seed.py emits ARM64 instructions and Mach-O using build-time Python. Native compiler 0.5 now reproduces the documented systems subset without Python; macOS signing remains explicit. Read the native-compiler section below for the tested scope. Systems source has trusted pointers/syscalls and is never a Core sandbox or MCP input. No C/C++ compiler, assembler or linker is invoked by this build.

## Reference compatibility

The retained Node implementation accepts RF2_U32_CORE_V0 and has ten tools, including C emission, batching and the SFE public repository catalog. Those are reference-development capabilities, not features of the three-tool native server. Never silently route an unsupported native request into that server. Read docs/SPEC.md before using it explicitly for differential development.

## Evidence

Test outputs, work counts, checked overflow, exact wrapping and refusal/recovery. Use docs/STANDALONE-VERIFICATION.json for actual native cases. No speed, energy, phone integration, self-hosting or token-saving ratio is established by a dependency change. Old C-backend benchmark results are a separate experiment. Keep private engineering data and participant records outside releases. Source hashes bind local artifacts, not human peer review or academic approval.


## Native compiler 0.5

The separate rf2c CLI, written in native/compiler/compiler.rf2, now reproduces itself for its bounded RF2_SYSTEM_A64_V1 subset and builds the unchanged 0.4 runtime. Read docs/NATIVE-COMPILER.md and NATIVE-COMPILER-VERIFICATION.json. Native builds require no Python/C++/Node; the historical Python seed is retained for initial bootstrap and testing. macOS signing is explicit. Output paths must be new. This developer compiler has trusted raw pointers and OS calls; never expose arbitrary machine-source execution over MCP or treat it as the compact computation sandbox. General Core migration and service capabilities remain open. Runtime MCP version 0.4 is intentionally unchanged; plugin release 0.5 adds compiler guidance.
