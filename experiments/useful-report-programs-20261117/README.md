# Four verified RF2 report utilities

These are experimental native Mac ARM64 source programs, all separately reviewed
and tested. They are Codex-agent-engineered implementations, not successful
DeepSeek raw-source generations. Each reads one selected regular nonsymlink file
up to 4096bytes, validates strict UTF8/C0 and prints a complete JSON or HTML report.
The application command is `program json|html PATH`.

| Source | Purpose | Both-mode checks |
| --- | --- | ---: |
| [C-manual/main.flow](C-manual/main.flow) | Log severity counts, direct application plumbing |172 |
| [D-cli/main.flow](D-cli/main.flow) | Duplicate identifier audit, shared CLI |232 |
| [C-cli/main.flow](C-cli/main.flow) | Log severity counts, shared CLI |172 |
| [D-manual/main.flow](D-manual/main.flow) | Duplicate identifier audit, direct application plumbing |232 |

Build with the qualified 0.50 compiler, an explicit reviewed SDK containing the
Report/CLI modules, fresh output path, `--compact --sdk-root SDK` and optional
`--opt`. Sign the generated image on Mac before running it. The compiler SHA is
`4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c`.
Do not silently use an older published compiler or replace the stable SDK.
The SDK staging/qualification recipe is in
`experiments/refinement-20261117/ai/validate_goldens.py`; its golden sources are
controller controls and were never provider prompts.

The independent acceptance command is
`experiments/ai-completion-20261117/verify_results.py --manifest REVIEWED_JSON --out NEW_DIRECTORY`
through the guarded Mac disposable bank. The manifest explicitly supplies compiler,
SDK hashes and the four reviewed source hashes; it must declare actual origins.
Generated binaries are disposable; source/provenance and unique receipts persist.

[Full results and all failed costs](../../docs/AI-OUTPUT-RECOVERY-20261117.md).
The finite AI catalogue selects these existing implementations; it does not
invent algorithms or execute provider commands. Default/stable release unchanged.
