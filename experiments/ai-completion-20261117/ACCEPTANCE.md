# Independent acceptance for the four-program completion campaign

The programs are the two original complete tasks under two library conditions:
C/manual, D/CLI, C/CLI and D/manual. They are four implementation arms, not four
different task definitions. Correctness is measured against the unchanged prior
oracle, not a newly weakened success rule.

## Required gates

1. The campaign records a new fixed plan before any provider call. Prompt-bound
   task and guide copies must remove literal solution placeholders, while retaining
   every original behavior and making the complete exact output shape explicit.
   No controller golden program enters a model prompt.
2. Every returned program is data until a separate reviewer checks its imports,
   effects and complete source. Review approves an exact source SHA256. No model
   command, binary or claimed test result is trusted.
3. Actual unchanged compiler, SDK and condition-boundary checks precede native
   testing. Compiler failure, wrong condition or incomplete source is a failed
   attempt. Feedback repairs are new preserved attempts, never edited history.
4. An implementation passes only after both plain and optimized builds pass all
   original cases: C86 or D116 cases per mode. Across four arms this is808 tests.
   Symlink/FIFO input refusal, strict text/identifier validation and real stdout
   failures are included. The original eight-second per-process timeout remains.
5. Independent final verification rebuilds all four accepted sources from a
   source-review manifest. The manifest is prepared by the orchestrator, never
   by the provider, and lists exact SDK and source bytes. `verify_results.py`
   creates a fresh run and refuses reuse. Generated binaries use MacSpaceGuard;
   raw unique receipts remain project-local.

## Verification command and manifest

Run `verify_results.py --manifest REVIEWED.json --out NEW_OUTPUT_DIRECTORY`
through the local guarded bank. `REVIEWED.json` contains:

- `schema`: `rf2.ai-completion.reviewed-sources.v1`
- `sourceReviewConfirmed`: `true`, set only after actual separate review
- `compiler`: qualified original0.50 native compiler path
- `sdk`: exact shared staged SDK directory
- `sdkFiles`: map of every regular SDK filename to its SHA256
- `arms`: ordered C/manual, D/cli, C/cli, D/manual records, each with `task`,
  `condition`, absolute `source`, and exact `sourceSHA256`

Original oracle SHA256:
`f481949423fcfaa62da6e7084b7b39320ac898b9bb501ef0db23ea9524f1ab8e`.
Original compiler SHA256:
`4e47ea8be4bfd81ba12eae606f3ea9321f940957a33d67a88559c1f99f65597c`.

This synthetic Mac ARM64 acceptance is not universal hardware support, a human
usability study, a sandbox proof or a stable-release qualification. Stable/default
libraries, compiler releases and the active owner worktree remain untouched.

## Before/after accounting

Preserve the old0/4 study separately: six requests,37,690 known provider tokens,
one unknown-usage request and564.001 observed request seconds. Preserve the
separate failed contract pilot with unknown usage; do not hide it in a successful
arm or call unknown usage zero. The new campaign reports every request, including
failed/length/transport responses, reasoning/cache subsets and full provider
totals. Subsets are not added twice. A transport request that lacks usage makes
total provider spend a lower bound. Correct programs per declared arm is the
primary result; cost per success is undefined where required usage is unknown.

Any hand-authored repair must be distinguished from unmodified model output.
New prompts, multiple repairs or changed transport prevent a causal claim that
one isolated intervention produced the difference. Completion proves the stated
tasks within these bounds, not a general token-saving percentage.
