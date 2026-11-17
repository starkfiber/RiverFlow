# RF2 useful AI output recovery — 17 November 2026

**Four working native programs now pass 808/808 unchanged acceptance cases.**
The usable AI route selects these reviewed implementations from a closed
catalogue:3/4 initial choices,4/4 after one declared logical repair. Raw DeepSeek
source generation still passes 0/4. The implementations were corrected or written
by Codex agents, reviewed separately, then rebuilt and tested. Stable is unchanged.

[Machine-readable evidence](AI-OUTPUT-RECOVERY-20261117.json) ·
[Every current request, including failures](AI-OUTPUT-RECOVERY-20261117.csv) ·
[Working source](../experiments/useful-report-programs-20261117/README.md)

## Before and after, without mixing different tasks

| Engineering phase | Measured result | Calls | Reported DeepSeek tokens | Unknown usage calls | Request observation |
| --- | --- | ---: | ---: | ---: | ---: |
| Prior matched raw-source study |0/4 complete programs |6 |37,690 |1 |564.001s |
| Current raw-source completion/repairs |0/4 complete programs |7 |50,041 |1 |324.223s |
| New finite capability selection, including its rejected first choice |3/4 initial;4/4 after one logical repair |5 |4,488 |0 |17.686s |
| Current combined provider work |Raw generation and finite selection kept separate |12 |54,529 |1 |341.908s |
| Codex engineering plus actual resolved-source replay |4/4 native implementations;808/808 cases |No additional DeepSeek calls |Codex usage unavailable |Not included in DeepSeek totals |Build/test receipts retained |

The prior separate output-contract pilot also failed in transport after 134.978s,
with unknown usage. It stays separate from the prior matched study and current
run. Known totals are lower bounds where any request lacks usage; they are
provider-reported tokens, not billing. Reasoning and cache counts are subsets,
not extra tokens. Codex orchestration/engineering usage is unavailable, so no
whole-development cost or causal token-saving percentage is established.

The catalogue routing task is easier and different from implementing algorithms.
Its low usage is not evidence of cheaper arbitrary code generation. It supports
exactly two known algorithms and two plumbing variants, not unseen application
synthesis or general task correctness.

## What changed in code

1. **Output contract:** removed literal `complete main.flow` placeholders from
   both task prompts and system instructions, supplied the exact HTML structure,
   and clarified library permissions. The original study remains frozen.
2. **Four functioning RF2 implementations:** log severity summary and duplicate
   identifier audit, each with application-owned plumbing and shared CLI plumbing.
   Source provenance distinguishes repaired proposals from independently written
   implementations. No golden implementation or test solution entered a prompt.
3. **Repair context:** a bounded source-hashed advisory collector identifies
   duplicate locals, unsupported breaks/boolean words/inline else-if, reserved
   local names and untyped try. It found 18 advisories in the actual initial C/CLI
   proposal.23 offline test methods pass. It never rewrites or executes source,
   resolves imports, or replaces compiler/type/effect/runtime acceptance.
4. **Transport:** structured failures now preserve safe categories and unknown
   usage. A later phase-aware candidate distinguishes DNS, connect, TLS, send,
   headers, body and output. TCP connect and TLS each use an eight-second socket
   timeout; post-connect operations retain180s and the outer observation420s.
   TLS/SNI verification stays enabled. Exactly one selected address and one POST;
   no redirects, automatic retries, proxy fallback or credential transfer.
5. **Grounded routing:** strict JSON enums resolve only to reviewed source hashes.
   Wrong task, wrong implementation, duplicate keys, unsupported values and
   missing/incomplete responses refuse without execution. Call starts consume
   budget even when final receipts are missing; usage and duration remain unknown.

The phase-aware transport passes 12 offline test methods and received all four
actual responses sent through it. These are finite observations, not an SLA.
The136-second timeout occurred on the earlier transport; fresh Mac/credential-host
DNS/TCP/TLS probes were healthy. Its historical cause remains unresolved. No
router, firewall, address or company service was changed to make the tests pass.

## Native acceptance

| Program | Plain | Optimized | Origin |
| --- | ---: | ---: | --- |
| Log severity / manual |86/86 |86/86 |Codex-agent correction of failed proposal |
| Identifier audit / shared CLI |116/116 |116/116 |Codex-agent implementation after capped provider response |
| Log severity / shared CLI |86/86 |86/86 |Codex-agent correction after source/transport failures |
| Identifier audit / manual |116/116 |116/116 |Codex-agent composition of its reviewed implementations |

A separate reviewer rebuilt all eight variants. After actual provider selections,
the coordinator checked every resolved source hash and performed another fresh
native rebuild:808/808 again. The unchanged independent oracle checks exact
JSON/HTML, Unicode/escaping, physical LF/CRLF semantics, identifier boundaries,
invalid arguments/modes,4096-byte admission, missing/directory/symlink/FIFO input,
read-only stdout and broken pipes. No oracle or timeout was loosened to pass.
Qualification is Apple Silicon Mac with the pinned0.50 compiler and reviewed
experimental Report/CLI SDK. It is not Linux/Windows/device qualification.

## Preserved failures and explicit amendments

The first C/manual repair repeated the failing source. A later repair removed
`break` by moving the cursor to line end, breaking classification while leaving
untyped try. The D/CLI response reached 16,384 completion tokens with repetitive
source. C/CLI's reasoning repair timed out with unknown usage. D/manual remained
invalid; further raw-source repairs were explicitly declined once agent-engineered
programs passed and the remaining request budget was allocated to finite routing.

Initial routing selected `cli` for a manual request. The strict guard rejected it;
nothing executed. A separate reviewed amendment supplied implementation meanings
and the trusted caller's plumbing choice, then allowed exactly one logical repair
after all four initial selections. The first rejection stays in both costs and
initial3/4 scoring; the repaired result is reported separately as4/4. The global
12-call limit was unchanged and reached. **No further provider calls are pending.**

Original freezes, unamended and amended requests, failed sources, feedback,
receipts and all usage remain project-local. The early unused context-amendment
wrapper snapshot is retained; a review correction limits diagnostic excerpts to
actual source locations. D/manual fallback was prepared in parallel before its
provider arm closed; this was engineering preparation, not an AI-alone result.
The frozen native verifier's old 'model proposals' scope wording is explicitly
corrected by the reviewed manifest and source-kind audit.

## Boundaries and continuation

All 47 protected release/default files match their before hashes. The stable
runtime, default SDK/compiler, downloads and owner's active checkout were not
changed. Existing R5 promotion failure, broader Net/Ship gates and fixed11/12
requirements remain unchanged. No Memory writes or retained KHC jobs were used.

This phase produces verified experimental source and developer tooling. It does
not establish reliable unrestricted DeepSeek authoring. Next qualify a genuinely
unseen utility against the same strict output/IO rules and grow the catalogue
only from independently verified implementations. Reopen inference only with a
new reviewed budget; do not restart these closed runs.

Raw evidence: `artifacts/ai-completion-20261117/`, including `FINAL-REVIEW.json`,
`ROUTED-REVIEWED-SOURCES.json`, `routed-native-1/RESULTS.json`, original freezes,
amendments, per-request receipts, and stable hashes. These measurements do not assert release deployment; verify the actual Git
history and separate publication receipt before claiming a published release.
