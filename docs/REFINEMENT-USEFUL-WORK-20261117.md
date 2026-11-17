# RF2 dense JSON, diagnostics and complete-work refinement

17 November 2026. Base: verified SFE main `53ec2577a04f3b3c5ecf71b1316add3d3671a245`. Explicit experiments only; default compiler/SDK, stable downloads and the active owner Net/Ship checkout are unchanged. The fixed delivery ledger stays11/12; external Linguist acceptance remains pending.

## Implemented code and executed acceptance

| Change | Result | Boundary |
| --- | --- | --- |
| Checked direct JSON escape-byte emitter | All6 large escape-heavy targets beat scalar and R3;1.55–2.00× vs scalar |26 profiles,31 triplets each;7/8 small gates,one minimum-duration failure; R5 unpromoted |
| Source-context compiler diagnostics |40 focused controls +169 existing diagnostics; exact signed self-generation |Two advisory hints only; no syntax or successful app lowering change |
| Complete source SDK composition |8 manual/CLI plain/optimized builds,808/808 independent app checks |Experimental R5 + unchanged Report/CLI + diagnostic compiler, not stable replacement |
| Net measurement refinement |4/4 optimized small profiles pass;7/8 all-mode small profiles pass |One plain durable early-reject interval inconclusive; larger short-duration loss retained |
| Destination safeguards |14root protected-path controls;17post-guard composition controls; 37direct-stage controls |Ordinary resolved local paths, not concurrent hostile-filesystem isolation |

## Why the JSON implementation is different

R5 removes repeated string-length/copy calls for escapes in large disjoint fields. Its checked leaf emitter writes the exact bytes directly, preserves atomic two-byte escapes and legacy4+1+1 C0 partial commits, and retains sticky errors. R3 small-field and overlapping-source routes stay intact. Existing8,040oracle controls, full alias/boundary matrices, Passage controls and6,384additional dense/C0 checks pass; no new speed claim comes from counting tests or calls.

| Escape-heavy input | Mode | R5/scalar paired median (95% interval) | Speed vs scalar | Speed vs R3 |
| --- | --- | --- | --- | --- |
| 1,024 bytes | plain | 0.50955 (0.50725–0.51132) | 1.96× | 1.96× |
| 1,024 bytes | opt | 0.61715 (0.61308–0.62495) | 1.62× | 1.65× |
| 16,384 bytes | plain | 0.49894 (0.49549–0.50064) | 2.00× | 1.98× |
| 16,384 bytes | opt | 0.63163 (0.62026–0.64664) | 1.58× | 1.58× |
| 262,144 bytes | plain | 0.50531 (0.49095–0.52321) | 1.98× | 2.01× |
| 262,144 bytes | opt | 0.64523 (0.63906–0.66588) | 1.55× | 1.53× |

Every target passes the frozen confidence/duration rules against both comparators. However,32-byte escape-heavy/plain includes 42,602 µs, below the required 50,000 µs. Its ratio 0.99410 and 95% interval 0.99096–0.99702 show no measured slowdown, but the duration gate still fails. No recalibration, trimming or comparative rerun was used to turn that failure into promotion. Native elapsed includes scheduling/background load on this shared Mac; it is not CPU cycles, power, network throughput or a universal hardware comparison.

Full26-profile intervals, process-secondary measurements, failures and hashes: [serializer evidence](../experiments/refinement-20261117/serializer/EVIDENCE.json), [rules](../experiments/refinement-20261117/serializer/PROMOTION-PROTOCOL.json), [results](../experiments/refinement-20261117/serializer/RESULTS.md). Prior R3 and rejected R4 evidence remain unchanged.

## Actual AI usefulness: failed trials remain failures

The fresh balanced C/D study finished0/4 complete programs, both manual 0/2 and shared CLI 0/2. Six calls produced three literal placeholder proposals, two completion-length failures and one transport timeout. Five requests have 37,690 reported tokens; one request has unknown usage. Observed request time 564.001 seconds. No actual model source reached native compilation; invalid placeholders were rejected by the condition controller. There is no tokens-per-passing-task value and no SDK productivity advantage established.

The independent controller goldens pass808/808 cases after an initial preserved pair of 8-second empty-input timeouts. Forty exact empty-case replays and one fresh full qualification pass; the original timeout cause remains unresolved. No timeout was relaxed.

A separate prose-only output-contract pilot removes the literal schema placeholder while holding the task/guide/compiler/SDK/model fixed. Its single request failed in transport after 134.978 seconds, with no source or known usage. No retry occurred. The instruction change is implemented but its effect remains untested; it is not another arm or replacement of the failed matched study. Earlier successful/failed studies remain separate historical records.

## Implemented provider diagnostics, separately qualified

A new opt-in transport candidate now emits bounded structured errors instead of a truncated traceback: HTTP status, DNS/timeout/TLS/network/configuration/output category, safe reason type/errno and elapsed time. It keeps credentials on the selected host, refuses redirects and reflected credentials, bounds input/configuration/response sizes, flushes successful output explicitly and never retries. Write/flush errors remain output failures rather than being mislabeled network failures.

All **63 offline controls across 14 test methods pass**, using fake configuration/HTTP/streams with zero real requests or credential reads. Earlier 56/61-control evidence and the output-category correction remain preserved. This helper is not wired into the closed studies; live connectivity and interpreter-shutdown pipe behaviour remain unqualified. Historical unknown causes cannot be recovered from the old truncated errors. The exact pilot payload is now reproducible from a tracked pure builder. Read [transport contract and evidence](../experiments/refinement-20261117/ai/PROVIDER-TRANSPORT.md).

## Use and reproduction

Read the [experiment entry](../experiments/refinement-20261117/README.md). `package.py NEW_DIRECTORY` builds a pinned experimental source SDK; protected defaults/releases and existing outputs are refused. `verify_package.py` composes the compiler/library changes against the independent complete-task oracle. Generated source and unique receipts stay persistent; reproducible native images use the guarded local work cache.

The direct staging guard was added after timing. Its original bytes/evidence are preserved; allowed SDK output is byte-identical to the frozen candidate. Root guard refinements likewise reproduce every source SDK byte from the808-check composition. These are packaging changes, not a new measured writer or retrospective timing alteration.

Compact source-bound evidence: [compiler](../experiments/refinement-20261117/compiler/EVIDENCE.json), [Net](../experiments/refinement-20261117/net/EVIDENCE.json), [composition](../experiments/refinement-20261117/COMPOSITION.json), [AI](../experiments/refinement-20261117/ai/EVIDENCE.json). Raw local evidence lives under ignored `artifacts/refinement-20261117/`. No project content was written to Kanika Memory, KHC jobs or Chain events.

## Next decisive work

Qualify the remaining short-duration Net/serializer cases with a new predeclared measurement design on a quieter host; do not rerun the same frozen campaign to select a winner. Make provider failures diagnostic before spending more inference budget, then test the corrected output contract separately. Broader13 firewall gates and actual platform/backend acceptance remain open; these experiments do not complete them.
