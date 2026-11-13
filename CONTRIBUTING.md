# Contributing to RiverFlow

Start with [the codebase map](docs/CODEBASE.md). Choose a bounded capability or reproduced defect; describe the expected result, target and failure behavior before implementation.

## Change checklist

- Keep stable and development contracts distinct. Preserve public paths and old measurement receipts.
- For compiler changes, test both default and optimized modes, self-generation, actual generated execution and relevant refusal paths. Compare independent expected values, not two copies of the same implementation.
- Keep raw systems effects out of bounded MCP. A new tool or permission needs an explicit contract and separate acceptance tests.
- Measure identical tasks against retained controls. Report startup, I/O, warmup, trial count and target. Keep regressions and uncertainty visible. Shorter source is not proof of fewer billed model tokens.
- Do not commit credentials, receipt keys, private thesis content, participant records, local environment files or raw personal data.
- Document the final behavior and evidence, then run `git diff --check` and check documentation links.

Use an existing qualified native compiler. Build scripts require new output directories. Development controllers may require Python, Node or C tools; native user binaries do not inherit those dependencies.

## Review and publication

A passing test is evidence for its tested scope, not general correctness, security certification or novelty. Speculative computing approaches belong in a hypothesis with a falsifying control, not a release claim.

SFE upstream identity rules in AGENTS.md apply to maintainer automation. Fork contributors use their own identities for their own remotes. Keep attribution and audit history accurate.

Contributions use the project's MIT licence. No thesis or PDF export is required for a software change.
