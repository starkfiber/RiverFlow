# RF2 implemented acceptance and useful-output SDK

Read ../../docs/ACCEPTANCE-USEFUL-OUTPUT-20261117.md for the reviewed result and
EVIDENCE.json for source-bound local receipt hashes. This directory contains
usable source candidates and the exact acceptance controllers, not a release.

- `ship/`: fixed uncertain-mutation retry behavior; prepared/build-only candidate
  uses the verified optimized guest and fixed peer. Full implemented suite passes.
- `net/`: source-bound DHCP/DNS/durable and public network regressions. Padding
  wins verified; small timing intervals are inconclusive, so optimization is opt-in.
- `sdk/`: R3 fixes small-field regressions. `sdk/r4/` retains a rejected hypothesis
  and reusable checked monotonic benchmark; it is not the default candidate.
- `ai/`: typed CLI/report callback library, independent complete-task and boundary
  oracles, capped/frozen source-proposal studies and exact model observations.

Create a new persistent reviewed development SDK with `python3 package.py NEW_DIR`
(from this directory). The package adds R3 + Report + CLI, preserves checksums and
refuses replacement. Use an explicitly qualified native 0.50 compiler and
`--sdk-root NEW_DIR`. `ai/reference-cli-A.flow` and B are runnable examples; the
actual first-call model proposals are under ai/model-observations. Source and
unique receipts stay persistent; only reproducible binaries use the guarded local
work cache. No shared company Memory/Chain/retained compute job is used.

Stable/default SDK, public release files, active owner checkout and live systems
are unchanged. Thirteen broader firewall gates remain pending. Two useful model
trials do not establish a general token-savings percentage. Negative controls,
failed transport usage and timing losses remain explicit.
