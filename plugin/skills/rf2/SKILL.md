---
name: rf2
description: Check and execute RiverFlow Core/compact programs, lower checked kernels, use the versioned attendance exporter, and develop native compiler evidence.
---
# RiverFlow RF² 0.6

Use rf2_status first. Read docs/NATIVE-CORE.md and STANDALONE.md for current profiles/effects. Five native tools exist: rf2_status, rf2_check, rf2_run, rf2_lower and attendance_export. Users require no Node/npm/Python/C++ runtime. The host provides AI intelligence; the executable has no embedded model.

## Core and compact source

RF2_U32_CORE_V0 supports ADD, MUL, LOAD, POPCOUNT, NONZERO, acyclic named scalar helpers, forward calls and bounded non-nested main loops. All functions are checked. Parameters/indices are immutable; loop-local values do not escape. Checked and wrapping u32 semantics are explicit. Core can only read the supplied array. Unknown effects, types, recursion and exceeded limits reject.

Compact V1 remains `rf2 v1 checked` or `wrap`, followed by `sum input`, `squares input`, `bits input` or `nonzero input`.

Use rf2_check/rf2_run with supplied text/data. Native run executes bounded IR; do not label every run as a separately compiled kernel. rf2_lower returns systems-profile kernel source only. It neither compiles nor writes a file. The explicit tools/build-core.sh route combines a trusted harness, native compiler and OS signing to create an ARM64 executable. General systems source is never admitted as Core or executed over MCP.

## attendance.local@1

attendance_export takes at most 1,000 records, each exactly student_id/date/status. IDs are constrained ASCII identifiers, dates canonical valid Gregorian YYYY-MM-DD, state present/absent/late. Duplicate student/date records reject. The tool returns CSV, counts and a byte fingerprint; no filesystem path or permission argument is accepted.

The CLI `rf2 attendance records.json new.csv` performs an explicitly requested file export, refuses existing paths/symlinks and validates before creation. Do not invent student records or field results. Included TEST fixtures are programming inputs only. Counts are computed through the versioned compiled Core kernel. Read the capability README before use; do not claim an authentication system or a full school app.

## Native builds and evidence

The systems compiler reproduces its own bounded source without Python. tools/build-runtime.sh composes the five runtime modules; compiling native/rf2.rf2 alone is no longer a complete build. The historical Python seed and JS/C references remain development oracles, not user runtime dependencies. Source hashes establish byte identity, not independent approval or process isolation.

The plugin uses RF2_BIN or output/bin/rf2 and never silently builds/downloads/falls back to Node. Fresh checkouts need an explicit native binary. Current qualification is on Apple Silicon Mac; normal OS signing remains required. No speed, energy, token-saving, phone or fieldwork claim is established. Preserve failed tests and private data locally; do not put participant records in public releases.
