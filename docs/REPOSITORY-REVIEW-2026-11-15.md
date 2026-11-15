# Repository navigation and reporting review

15 November 2026, based on main `5802f49ea261e8ddcdf610fb8072b6a7650f71e5`. This is a documentation/developer-tool cleanup, not a compiler, SDK or binary release.

## Changes

- Added [RF2 everywhere](RF2-EVERYWHERE.md), retaining the maintainer's cross-platform ambition and competitor comparisons while naming actual target qualification gates.
- Added [documentation](README.md) and [example](../examples/README.md) entry points, grouped by task and execution profile.
- Updated the package guide and capability map for Workbench 0.38 and the source-only 0.40 experiment. Borrowed-record research remains separate from released compilers.
- Corrected an old guide's implication that `.flow` examples are exclusively Core. Extensions do not select the execution contract.
- Added [language reporting](LANGUAGE-REPORTING.md). RiverFlow is not yet recognized by GitHub Linguist; no upstream acceptance or compatibility layer is claimed.
- Regenerated the source inventory using tracked paths and actual generated attributes, with a per-area breakdown. Generated learning readers are marked accurately; real tests and reference implementations remain counted.
- Preserved existing public paths, compiler/runtime code, test controllers, frozen receipts, packages and private project boundaries. The codebase map explains where future files belong.

## Executed verification

| Check | Observed result | Scope |
| --- | --- | --- |
| Local link destinations across eleven edited/new guides | 202 destinations exist | Does not test every external URL or Markdown anchor |
| Inventory controls in a disposable Git repository | Eight controls passed | Counts, generated exclusion, untracked exclusion, paths with spaces, freshness, stale refusal without rewriting, regeneration and source-symlink refusal |
| Independent inventory sums | Every reported source size and per-language total agrees with files | File accounting, not Linguist execution or correctness proof |
| Documented lookup check/build route | Native build succeeded using the qualified 0.36 Mac compiler | No compiler modification |
| Native lookup execution | Duplicate lookup and absent-value insertion gave the documented JSON; malformed input refused with exit 1 | Three smoke cases, not a rerun of every prior compiler/application suite |
| Native runtime status | Reports 0.17.0, bounded effects and no caller-controlled MCP filesystem authority | Existing runtime; no MCP protocol expansion |
| Whitespace review | `git diff --check` passed | Changed text only |

Native lookup binary SHA-256: `371af38562e3a2783edcae5fa94af7398e4b083693870fb86d38e5be0012f307`. Timings and billed model tokens were not measured. No new speed, energy, hardware, learner-usability or platform-parity result follows from this cleanup.

Private execution receipts are retained locally under `artifacts/repository-cleanup/`. Public source paths and the inventory generator make the accounting reproducible. Future work starts with the [typed application value gates](RF2-EVERYWHERE.md#engineering-sequence), using Booking as a real integration target and preserving every known failure case.
