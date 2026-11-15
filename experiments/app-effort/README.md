# Application effort source candidate 0.47

The candidate fixes measured RF2 construction friction. Published 0.46 binaries and stable 0.17 remain unchanged. This directory is developer source, not a new binary release or a claim of Python parity.

- `try` propagates matching scalar errors; `return operation()` forwards a matching scalar result. Both use ordinary cleanup.
- `lib/mcp.flow` supplies a bounded one-tool legacy MCP dispatcher; the app supplies its reviewed read-only callback. Framing, compact JSON, input rejection and error classification are shared.
- [API.md](API.md), source-extracted signatures and 29 native API cards reduce source hunting. Cards can be queried together: `./rf2-doc app_form store_operation mcp_serve`.
- Explicit journal/server policies replace edits to implementation literals. Defaults remain 1 MiB and 4096 processed connections; apps can choose a journal budget before use and serve-until-terminated explicitly.
- Shared JSON escaping, capacity errors, standalone UI dependencies and private Writer replies are corrected. The actual Booking browser app uses shared form admission.

## Build the developer kit

Use the public, checksum-qualified 0.46 Mac ARM64 compiler as the bootstrap. Python 3 and the normal macOS signing tool are developer prerequisites; emitted programs need no Python, Node/npm or C++ runtime.

```sh
python3 experiments/app-effort/prepare.py /new/path/candidate
sh tools/build-program.sh /path/to/qualified-0.46/rf2c /new/path/candidate/compiler.flow /new/path/build --opt
python3 experiments/app-effort/stage.py /new/path/app/lib
python3 experiments/app-effort/build-docs.py /new/path/build/program /new/path/app/lib /new/path/api-tool
python3 experiments/app-effort/api-index.py /new/path/app/lib /new/path/app/SIGNATURES.md
```

Read API.md; write your entry beside its staged lib/. `status.flow` demonstrates a generic callback, `booking-read.flow` reads a launch-selected journal, and `try-demo.flow` demonstrates propagation. Copy a chosen example into the app directory before compiling. Compile/sign explicitly with a new output name. Compilation never executes the app. The compiler's current 8-parameter, function-scope-record and final-return constraints remain; the guide states them.

## Evidence and construction experiments

Read [executed results and limits](../../docs/APP-EFFORT-0.47.md). Both corrected RF2 apps passed 55/55 frozen checks and byte-identical clean rebuilds. Python still required less authoring time and reported usage in this task. A lower input count against the first revised SDK is not a billing or runtime-speed result.

[PROTOCOL.md](PROTOCOL.md) preserves the failed six-attempt round. [PROTOCOL-V3.md](PROTOCOL-V3.md) freezes the four-attempt follow-up. `run.py`/`run-v3.py` perform actual Codex calls using an existing account and retain every failure; they are not ordinary unit tests or automatic installation steps. They expect the source-pinned artifact layout named in their constants; rebuild those versions or use the source-only evidence archive before reproducing. No API key, installation or remote shared-compute job is created by this kit.

`qualify.py` runs 15 native suites and self-generation with explicit historical reference compilers. `report.py` binds real JSONL usage/grades and assembles reviewed public source evidence. `audit-apps.py` rebuilds final sources and replays fresh applications without repairing or replacing their original scores. The archive excludes native images, databases and private account/session traces. No human learner study, universal platform readiness, new hardware result or GitHub Linguist acceptance is claimed.
