# Frozen complete-app construction experiment

This experiment builds Study Rooms with CLI, browser GUI and read-only MCP. It is an **SDK reuse construction task**, not a cold language/runtime build or a universal benchmark. [TASK.md](TASK.md), [PROTOCOL.md](PROTOCOL.md) and the original [grade.py](grade.py) were frozen before four fresh attempts. The current [results](../../docs/SDK-CONSTRUCTION-0.45.md) retain failed attempts, actual CLI-reported usage and a documented post-run grader correction.

`run.py` explicitly invokes the user's installed Codex CLI four times, up to15minutes each, consuming that account's model allowance. It disables user-config plugins, uses fresh ephemeral workspaces, captures actual JSONL usage and never invokes remote Memory/shared compute. This is an opt-in contributor experiment; it is not run by installing RF2 or by normal application tests. No new service signup/key is created. Model/provider routing not emitted in the JSONL is an explicit provenance limit, not a fabricated identity.

`booking_sdk.py` supplies the conventional SQLite domain/storage starting point. RF2 starts with pinned0.45 libraries and the qualified0.44 compiler. Neither receives a complete application entry. SDKs are functionally matched for the selected task but have different internals and convenience helpers. Setup is pre-existing and excluded from the warm construction time. No language-only causal claim follows.

## Inspect and reproduce an original

The [samples](samples/INDEX.json) contain the **as-delivered original code**, including its defects, self-tests and relevant SDK diffs. No private traces, account credentials, real bookings or large executables are committed. Files/diffs are reviewed and hash-bound. Use a new output directory:

```sh
python3 experiments/development-task/rebuild.py 1-rf2 NEW-TRIAL \
  --compiler /absolute/qualified-0.44-rf2c
python3 experiments/development-task/grade.py NEW-TRIAL NEW-REPORT.json
```

The helper reads pinned source from the local Git object database, verifies SDK/entry/compiler identities, applies the recorded library diffs and reproduces the exact signed native image. It never downloads or launches a program. The original SDK commit must be present locally. For Python choose2-python or3-python and omit --compiler. Python remains a comparator runtime dependency; RF2 user applications remain native.

`--repair` explicitly applies the separately recorded one-site protocol correction. Originals are never silently repaired. The retained [review.py](review.py) creates a separate reviewed grader after all four attempts, accepting a valid stale-form message and valid input-validation tool errors, while still requiring unknown-tool protocol errors. The original grader/grades remain intact. `repair.py` operates only on copies of the raw local trial, not the published release.

No full-success token saving is established: both initial RF2 attempts needed the protocol correction, as did one Python attempt. Parent review/repair token usage was not separately metered. Do not use repaired success to invent an end-to-end usage ratio. Published0.45 Booking is a separately qualified application and was not replaced by these experimental samples.
