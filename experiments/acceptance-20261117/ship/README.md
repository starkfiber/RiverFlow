# RF2Ship local acceptance and uncertain-outcome correction

This folder extends the measured AEAD candidate with all applicable implemented
RF2Ship 0.18 local regression suites and seven additional authenticated transport
fault cases on each QEMU PC/Q35 model. It does not qualify all 24 firewall gates.
No live VM, company network, physical target, service or stable package is changed.

## Actual behavior fixed

The research peer `Client.call` retried a first TimeoutError before checking whether
the operation was safe to replay. When a preserve/completion request reached the
guest but its reply was lost, the client sent it again and returned a later status 7
instead of reporting uncertainty. This was reproduced against the actual guest
on both PC and Q35. `intent_client.py` moves the unsafe-operation check before
the first retry. It raises `UnknownOutcome` immediately; observation/latest
semantics retain bounded retry with fresh durable nonces.

This changes the Python research peer, not guest machine code or a general native
RF2 network library. `CLIENT-TIMEOUT.patch` targets the exact original source.
Original helper SHA256 086385b6595bc6e821b09bdf965a876ab3c3946e88fbd5b592c15ab19affe2f6;
fixed ba26053fd5453235fa1161094dfa5cefacd5f7f642e632f36523950a729e74a2.
The optimized guest image stays
4ac4f627c82f403865facf94235bf58ea4952c1ce4d9c594f0c20f659d9e2450.
The default prepared candidate includes this fixed helper, not just a test overlay.
Baseline preparation keeps the original helper for comparison and expected-red
policy reproduction. Full acceptance, expanded loss tests and build-only output
all use the same prepared candidate source/helper/crypto identities.

## Fresh results

For each original/optimized crypto guest, the existing applicable local corpus
passes: secure 80, TCP 134, pending ownership 80, multiflow/ARP 12, boot recovery 11,
IRQ 6, startup 2, clock/fault 18, DMA 4 plus BIOS refusal, MMIO 4, and new-page/NX 16.
Host reference differential is 900 checks and peer/credential checks 304 per crypto
implementation. The unchanged native runtime still exposes nine MCP tools,
executes the supplied sum and refuses raw Systems source.

Expanded optimized guest tests pass 47 per model / 94 overall, including the original
40 per model and seven new cases: request loss, reply loss, delayed older reply,
bounded exhaustion, uncertain preserve completion, preserve submit timeout, and
latest-value reply loss. Each case checks actual guest effects/counters/state;
intentional dropping/delay is owned by the local controller. It is not physical
link-loss evidence. Original-vs-fixed replays use the same fixture and guest image.
Do not add overlapping counts into a unique population or security certification.

The existing 0.18 snapshot includes historical plaintext and older TCP tests that
are not the current encrypted/FIN contract. Those are not silently counted as
applicable 0.18 acceptance. Guard/fault suites use explicit debug-enabled local
variants; secure default guest tests separately prove debug commands refuse.
Boot/IRQ/guard suites retain their originally declared CPU/model coverage, rather
than claiming every fault test ran on both PC and Q35.

## Reproduce without a live source tree

The single reviewed `snapshot/original/`, `snapshot/guards.flow` and source
manifest are sufficient. No VM/SSH/provisioning scripts from the active owner
checkout are packaged. `--prepare` verifies this manifest, then derives isolated
baseline/candidate and normal/debug source copies under a new persistent
`--prepared-root` (default `prepared/`). `RF2_COMPILER` can select the
qualified 0.50 Mac compiler, whose exact hash is enforced; no compiler download.

```
RF2_COMPILER=/qualified/rf2c python3 -B experiments/acceptance-20261117/ship/run_acceptance.py --prepare
python3 '/Users/ik/Library/Application Support/Kanika/MacSpaceGuard/bank.py' status
python3 '/Users/ik/Library/Application Support/Kanika/MacSpaceGuard/bank.py' run rf2-ship-accept -- python3 -B experiments/acceptance-20261117/ship/run_acceptance.py --out /new/persistent/acceptance
python3 '/Users/ik/Library/Application Support/Kanika/MacSpaceGuard/bank.py' run rf2-ship-accept -- python3 -B experiments/acceptance-20261117/ship/run_loss.py --out /new/persistent/loss
```

For development without running guest tests, the same prepared fixed candidate
has an explicit build-only route:

```
python3 '/Users/ik/Library/Application Support/Kanika/MacSpaceGuard/bank.py' run rf2-ship-accept -- python3 -B experiments/acceptance-20261117/ship/run_acceptance.py --build-only --out /new/persistent/development-build
```

This emits the normal optimized guest plus a receipt binding the fixed peer,
crypto, compiler and image. It does not boot QEMU, install anything, contact a
server, change live networking or replace a stable artifact. Guest images are
rebuildable cache outputs and can expire; keep the persistent source/receipt.

Use fresh output paths. Prepared derived source copies are intentionally not
overwritten; start in a fresh checkout for another full reproduction. Dependency
requirements are existing Clang/Swift CryptoKit, xorriso, QEMU x86, Python and the
qualified compiler. These are developer dependencies, not the RF2 guest runtime.
The guarded runner uses an explicit bank path for reproducible native objects,
images and emitters. Unique receipts, serial logs, source/hook fixtures and traces
stay project-owned/persistent. Binary symlinks can expire when completed cache
jobs are reclaimed; hashes and source/commands remain, not a claim they stay live.
Synthetic temporary credential fixtures use normal private system temp paths;
real credentials, source, Git and unique evidence never belong in the cache bank.

`run_loss.py --original-policy` is the explicit expected-red policy test. It fails at
unsafe retransmission; preserve that failure rather than treating it as a broken
acceptance runner. Default is the fixed prepared candidate; `--fixed` remains a
compatibility alias. `--host-only` is the path-corrected host differential replay.
`qualify_evidence.py` checks the retained full suite, host replay, matched red/green
and MCP receipts; that integrity check is not independent cryptographic approval.

## Preserved failures and remaining gates

Initial full-run host comparisons passed their 900 assertions each but receipt
creation used an old relative source path. The path-only adapter correction and
fresh 900-per-implementation replay are separate evidence. The first green loss
fixture shadowed its outer `error` variable; Python deleted that exception binding
after handling, so receipt generation failed. Only fixture variable names changed;
fresh matching red/green runs preserve the original expectations and pass/refuse
as required. Neither failed run is overwritten or counted as a clean success.
The first final replay also exposed a reused disposable cache subdirectory. The
runner now allocates a fresh subdirectory per invocation under the stable bank
label; its failure is preserved under `run-final-cache-collision/`.

The original 24-gate ledger has 11 tested subsets, 13 pending and 0 fully qualified
gates. Missing WAN/VLAN/PPPoE, complete TCP/IP, IPv6, storage/guest services, HA,
authenticated management, physical reliability and independent crypto review
cannot be passed by rerunning this subset. No production cutover, firewall parity,
general x86 RF2 backend, verified constant time or complete erasure is claimed.

## TCP fixture correction

A fresh paired acceptance run exposed a real test assumption: a resolved WAN
neighbor can expire after its calibrated three-second lifetime while the TCP
session remains valid. The guest then correctly emits a new ARP solicitation.
The previous fixture assumed the next frame must always be TCP; the failure is
retained under `run-final-neighbor-expiry/`. The shared baseline/candidate adapter
now permits exactly one renewal only when the solicitation matches every byte
of the expected destination probe, the captured previous neighbor is resolved,
and guest clock age is at least its configured lifetime. It answers that ARP,
requires the guest's expected reply status and exact original TCP packet, and
keeps all existing TCP/state assertions. Wrong, unrelated, premature, or repeated
control frames still fail. Guest timeout values and guest code are unchanged.
`TCP-NEIGHBOR-REFRESH-*.json` preserves pre/post neighbor data, guest times and
exact wire frames whenever this branch is exercised.

The independent admission checks can be rerun without native tools:

```
python3 -B experiments/acceptance-20261117/ship/tcp_fixture_controls.py --out /new/persistent/controls.json
```

For guaranteed actual-guest expiry coverage, `run_tcp_expiry.py` accepts the same
`--prepared-root`, the built candidate `--image` and a fresh persistent `--out`.
Run it through the guarded cache runner. It delays only the host peer after
inbound data refreshes TCP, never modifies guest memory or timeout values, and
requires both PC/Q35 to exercise the exact renewal branch. Final verification
used this route for 134 existing TCP controls with one proved renewal per model.
These overlap full acceptance rather than adding unique feature coverage.
