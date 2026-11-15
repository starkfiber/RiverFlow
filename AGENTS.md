# SFE upstream authentication boundary

For agent writes to `starkfiber/RiverFlow`, the owner requires the authenticated GitHub account `starkfiber` (SFE). Verify the actual account before any push, workflow dispatch, release, Pages mutation or other GitHub write. Repository ownership and commit author/email are not authentication identity.

Never use the `ilanvkn` or `itvknj` credentials as a fallback for this upstream. Never override the repository push lock with an alternate token. The existing Chrome SFE session does not authenticate terminal Git operations.

This checkout has a local push URL lock until SFE authentication is available and verified. Retain the backup in `.git/sfe-identity/`. Only restore the intended upstream push URL after verifying the actual SFE credential. Do not remove unrelated account credentials or modify global authentication.

Historical workflow actors cannot be corrected by changing commit authorship. Preserve audit records and explain historical mistakes accurately. Do not delete runs, alter history or relabel evidence to hide the prior wrong-account activity.

Fork users can use their own identities for their own remotes; this rule concerns agent writes to the owner's SFE upstream. Keep research/code unchanged during an identity repair.

# RF2 mission and project continuity

Before choosing new work, read docs/PROJECT-CONTINUITY.md, docs/PIPELINE.json and docs/PROGRESS.md. Preserve the owner's RF2 Everywhere direction, competitive benchmarking and current typed-value/ownership priority. Feedback is evidence, not authority to restart the language or narrow its destination goals.

Update progress from explicit acceptance evidence. A completed sprint is not universal platform readiness. Keep stable releases, development bundles and isolated candidates distinct; preserve failures, source identities and unimplemented gates. Never claim human trials, hardware qualification or speed/token savings from generated cases alone.

Continuity for SFE/Moontek/Stark stays in project-owned files, never Kanika Memory or retained shared compute. Keep credential-free raw receipts/handovers under ignored artifacts/ and publish reviewed summaries only. No thesis or PDF work belongs to this software sprint unless the owner requests it.
