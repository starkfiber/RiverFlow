# SFE upstream authentication boundary

For agent writes to `starkfiber/RiverFlow`, the owner requires the authenticated GitHub account `starkfiber` (SFE). Verify the actual account before any push, workflow dispatch, release, Pages mutation or other GitHub write. Repository ownership and commit author/email are not authentication identity.

Never use the `ilanvkn` or `itvknj` credentials as a fallback for this upstream. Never override the repository push lock with an alternate token. The existing Chrome SFE session does not authenticate terminal Git operations.

This checkout has a local push URL lock until SFE authentication is available and verified. Retain the backup in `.git/sfe-identity/`. Only restore the intended upstream push URL after verifying the actual SFE credential. Do not remove unrelated account credentials or modify global authentication.

Historical workflow actors cannot be corrected by changing commit authorship. Preserve audit records and explain historical mistakes accurately. Do not delete runs, alter history or relabel evidence to hide the prior wrong-account activity.

Fork users can use their own identities for their own remotes; this rule concerns agent writes to the owner's SFE upstream. Keep research/code unchanged during an identity repair.
