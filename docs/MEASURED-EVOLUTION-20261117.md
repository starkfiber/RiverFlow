# RF2: measured SDK, Net and Ship improvements

17 November2026. Based on `73bf1a6c1cbb7c0d6b84c40aa2e4a184d528a292`.
This sprint changes executable source, not just the audit report. Three agents
implemented isolated candidates; the parent integrated and independently checked
the report package, provider outputs, source identities and regressions.

## What changed and what became faster

| Component | Actual change | Observed result | Boundary |
|---|---|---|---|
| SDK | JSON ordinary-byte spans; preserve alias behavior and scalar fallback | Optimized ordinary/mixed1–256KiB document serialization1.27–1.42× | HTML conversion performed once before repeated serialization; tiny escape-heavy values lose5% optimized/~9.4% plain |
| RF2Net | Scan bytes after DHCP END in a dedicated checked loop | Optimized normal300B1.20×; max576B1.35×; malformed tail1.43× |150k parses/process,15paired trials; shortest packet~0.9% slower; not network throughput |
| RF2Ship | Replace bit-serial Poly1305 multiplication with bounded44/44/42-bit limbs | Existing72B/40B envelope5.11× with both `-Oz`,10.80× with both `-O2` | Full bounded native AEAD calls, not entire firewall; actual x86 guest correctness tested separately |
| Shared report API | Typed text/u64 fields emit JSON or HTML with common escaping/state/error checks | Complete file-summary app passes37controls in each compiler mode | Useful composition library; no separate application-runtime speed claim |
| Authoring context | Source/manifest-bound API card plus native-checked syntax example |2029byte context emitted after native admission | No embedded model, signing attestation or demonstrated token savings |

The opt-in source package is built by
`python3 experiments/evolution-20261117/package.py NEW-DIRECTORY`.
Use its absolute path as `--sdk-root` with the qualified0.50 source compiler.
Original SDK0.50B, downloaded/stable releases, nine-tool Core runtime and external
active development tree are unchanged. New package edition is
`0.50C-measured-candidate`, not a newly released compiler.

## What was executed

- SDK:8760controls; unchanged Passage Desk80checks per mode;73728alias states per
  mode;30benchmark profiles with11shuffled pairs. Four additional escape
  distributions across both modes pass208capacity controls; measured complete
  serialization speedups1.15–1.35× on those particular distributions.
- Net:2078state/payload cases,312stream controls and55611padding cases per
  implementation/mode, with exact reply/176-byte state oracle. Incorrect-padding
  mutation detected in both modes. Rejected initial unroll remains in evidence.
- Ship:15348CryptoKit checks;12024exact-integer arithmetic cases per implementation;
 10000ASan/UBSan comparisons. Baseline and candidate each pass40PC+40Q35 encrypted
 transport checks in actual local QEMU x86 guests. No live VM/network testing.
- Reports:1356controls across both modes with original SDK, then1356with the
 accelerated SDK;37complete-task checks per compiler mode. Independent review
 reproduced12helper-state failures in the first revision and verified their
 refusal after the state fix; exact1024/1025field boundary checked.
- WhatIF: bounded source heuristics review Python controllers only. Seven `exec`
 leads refer to deliberate reviewed oracle-definition loading, not demonstrated
 command injection. `.flow`, native images, C and actual protocol behavior require
 the separate native/oracle/guest controllers; no false whole-native coverage.

Do not sum overlapping cases into a unique test-population claim. Timing is one
shared Mac with local competing work; no energy or hardware-wide claim follows.

## DeepSeek: real usage, failed attempts and successful repair

The four frozen A/B/B/A attempts used `deepseek-flash` with thinking disabled and
the same complete file-summary task. Manual composition and report-API conditions
both failed2/2 initial compilations. All original source, errors, prompts and
provider receipts remain local. API documentation alone did not solve authoring.

| Attempt | Condition | Input tokens | Output tokens | Total | Initial compile |
|---|---|---:|---:|---:|---|
|1|Manual|1962|1225|3187|Failed|
|2|Report API|2307|1087|3394|Failed|
|3|Report API|2307|648|2955|Failed|
|4|Manual|1962|825|2787|Failed|

Report-condition total6349vs manual5974: about6.3% more tokens, with no successful
initial app in either condition. Lower completion tokens alone are not useful-task
savings. No RF2-versus-Python conclusion is possible from this comparison.

One separate `deepseek-v4-pro` thinking/low repair received actual compiler feedback
and a correct RF2 syntax example. It compiled and passed37/37complete-task checks,
including invalid files, FIFO, symlink, read-only stdout and broken-pipe controls.
It used3234input+4340output=7574tokens (3786reasoning tokens included in output).
This changes model, feedback and context together; it does not isolate a causal
benefit or establish a matched repaired-success token ratio.

A sixth V4-Pro reasoning call supplied skeptical hypotheses and ten proposals,
not executed findings. Total provider-reported usage across six calls:34070tokens.
No further calls or automatic retries were made. Six calls are an observed bounded
campaign, not a hard dollar cap. Current model identities follow the
[official API](https://api-docs.deepseek.com/api/create-chat-completion/); this is
not a claim that the original R1 weights were served.

Actual orchestration was three Codex agents, native controllers and direct
DeepSeek calls. Existing OpenClaw/DeepClaw shared sessions were not used because
their retention route was not verified for excluded project material. No KHC
offload is claimed: native Darwin execution was required and shared retention was
not approved for this project. No Kanika Memory/Chain writes.

## Integration, failures and next gates

`experiments/evolution-20261117/net/PATCH.diff` and `ship/PATCH.diff` are exact
source-bound patches for the concurrently developed Net/Ship tree. Their snapshot
sources are not silently relabelled as tracked Git history. Do not overwrite that
active tree or its guest artifacts. Reconcile those changes with the owner branch,
then rerun the full relevant acceptance suite before promotion. Cryptographic
side-channel/register-erasure review remains open; a non-significant timing test
cannot certify constant-time behavior.

Preserved failures: rejected Net unroll; first JSON dense-escape regression;
initial report helper-state bug; one3second optimized-process timeout (same binary
later returned0in2.2ms, but exact interruption cause unknown); first grader used
Linux-only `/dev/full` on Mac and was corrected to real descriptor/pipe failures;
guest harness Path-expression correction; four original provider compile failures.
No failed attempt was rewritten as successful.

See [ten practical intelligence layers](EVOLUTION-NEXT-TEN-20261117.md),
[review disposition](MODEL-REVIEW-DISPOSITION-20261117.md),
[machine-readable summary](MEASURED-EVOLUTION-20261117.json), and
[full374-commit history before this branch's publication](EVOLUTION-COMMITS-20261117.tsv).
Raw source-bound receipts are under `artifacts/evolution-20261117/` locally.
The fixed owner delivery ledger remains11/12; this sprint creates no extra score.
