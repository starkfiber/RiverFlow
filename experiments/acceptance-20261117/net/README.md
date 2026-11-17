# RF2Net implemented public acceptance

This is an isolated source snapshot and reusable acceptance runner, not a complete
Internet firewall or a change to the active owner checkout. The candidate removes
the redundant post-END option-dispatch branch, validating the remaining padding
in one checked loop. The exact same transformation is applied to the original
and durable-reservation parsers. No lease policy, DNS behavior, persistence format
or network binding changes. `PARSER-PATCH.diff` targets the source-bound owner
branch; do not apply it to a changed baseline without review.

## Executed correctness

Both baseline and candidate pass these existing suites in plain and optimized
native compiler modes:

| Suite | Scope and executed controls |
|---|---|
| DHCP | 2,078 payload/state cases and 312 stream controls per variant/mode; exact replies and 176-byte lease/clock snapshots |
| DHCP negative controls | Three known-wrong native variants detected: expiry, duplicate type and wrong owner |
| DHCP UDP/time | 32 actual loopback datagrams, five ordinary clients plus one negative client, idle refusal/rebind cleanup; 1,024 divider and 1,024 time-conversion cases per mode |
| Durable leases | 42 named controls plus 255 partial-tail cases per mode: reservations, explicit init, reopen, real process kill after ACK, exclusive lock, file-size failure and explicit fsync/write/rollback hooks |
| DNS | 1,686 exact query/reply cases and 38 stream controls per mode; three deliberately wrong native variants detected |
| Combined services | 32 DHCP datagrams, restart, another 32 preserving five bindings/reservations, then 32 DNS datagrams across five loopback sockets per mode |
| Core authority | Existing nine-tool runtime, successful bounded sum, refusal of Systems source; runtime unchanged |

Additional exact parser controls cover every admitted length 244–576 and each
single nonzero post-END padding position: 55,611 cases with code **and all nine
metadata fields** per probe, eight probes total (both families/variants/modes).
Four native bad-tail mutants are detected. Overlapping cases are not added into
a unique test-population claim.

The self-contained public offline regressions also pass in both native modes:
IPv4, Ethernet/VLAN/PPPoE-shaped frame classification, UDP checksum, explicit
MAC/session binding, bridge exact output/state/stream behavior plus four native
mutants, owned queues, packet queues v2 and single-slot Intent admission. These
are modeled/static input profiles, not WAN session establishment or physical
network qualification. See the local result summaries for exact counts.

The full 16-call service campaign was replayed successfully after the runner
output-path amendment (`artifacts/acceptance-20261117/net/run-2/RESULTS.json`).
No candidate or oracle changed between the two successful service campaigns.

## Reproduce without changing live systems

One reviewed baseline set is stored under `snapshot/`; `public-regressions/`
contains only the required self-contained public-role kernel fixtures.
Generated baseline/candidate source copies are ignored, not duplicated in Git:

```sh
python3 experiments/acceptance-20261117/net/materialize.py
```

Use `--check` to verify an existing materialization. This performs source identity
checks only and refuses to overwrite existing variant directories. Sources stay
on persistent project storage. The runners require the exact qualified native
0.50 compiler and stable runtime paths recorded in their headers/receipts; their
SHA identities are checked. There is no toolchain download or fallback.

The explicitly opt-in experiment builds from the **candidate** source directory.
This is not a change to any ordinary service, default SDK or stable release. Its original and
durable DHCP parsers contain the optimized implementation that passed the full
service/padding suites; `baseline/` is only the retained comparison. For example,
after materialization, explicitly build the journal-backed stream processor:

```sh
/qualified/rf2c experiments/acceptance-20261117/net/candidate/dhcp-durable/main.flow /new/lease-service --compact --opt
codesign -s - /new/lease-service
```

To build the already-tested bounded local UDP adapter instead, select
`candidate/dhcp-durable/loopback.flow`. It binds only a dynamically selected
unprivileged loopback port and exits at its declared packet/timeout budget; it
does not become a LAN DHCP server. Select `candidate/dns/main.flow` for the
local-zone DNS stream processor. No compilation starts a service. Journals and
their initial reservation inputs belong on persistent protected storage, never
the disposable cache. The caller must explicitly initialize a new journal;
missing/corrupt state is not automatically reset.

Run `bank.py status` before substantive jobs, then use the guarded local work-cache
runner with stable label `rf2-net-accept`. Pass unique persistent `--out` paths:

```sh
python3 experiments/acceptance-20261117/net/run.py --out /new/service-evidence
python3 experiments/acceptance-20261117/net/public_regressions.py --out /new/public-evidence
python3 experiments/acceptance-20261117/net/padding_verify.py --out /new/padding-evidence
```

The commands above must execute through the guarded runner, not directly: they
put only reproducible native images in the supplied TMPDIR and keep source,
source-hook programs, expected/actual stream bytes, logs and receipts persistent.
No packet capture, physical interface, port53/67, LAN, guest or remote host is used.
Native checks run locally because they require Darwin ARM64 and the shared route's
retention is not approved for this project. No KHC/Memory/Chain use is claimed.

## Timing is a separately controlled experiment

`benchmark.py prepare --out /new/preparation` compiles eight source-bound probes
without timing. After every other native worker is quiet, root may grant exclusive
timing using `RF2_EXCLUSIVE_TIMING=1` and `benchmark.py run --out /that/preparation`.
The fixed plan uses 31 randomized paired process trials per family/mode/profile,
two warmups per variant, exact input/checksum oracles on every run, and 10,000
paired bootstrap resamples for 95% intervals. Short valid batches use 1.5 million
parses to reduce startup noise. All observations and any inconclusive results
remain. The small-case gate is candidate/baseline point ratio at most 1.03 and
upper 95% bound at most1.05, not a claim of universal zero regression.

This runner reports launch-inclusive repeated parser work, not whole network
throughput, energy or CPU-cycle certification. The first exclusive campaign stopped after two rows because the benchmark probe
allocated/read 584 bytes while a 576-byte packet plus 10-byte header needs 586 bytes.
The baseline correctly returned framing error 2 before the product parser. Exact
failure input and the original controller are retained in `timing-prepared-1`.
Its measured candidate/baseline ratios remain: original/plain short-valid 0.9673
(95% interval 0.8712–1.1910, inconclusive under the strict gate), and normal 300
0.9684 (0.8377–1.0221). These are partial results, not a completed speed claim.

The amended benchmark-only reader fills a 587-byte bounded buffer to EOF, accepts
at most 586 bytes and rejects extra bytes. `benchmark_io_verify.py` independently
checks valid whole/fragmented frames, early EOF, oversize and repetition limits.
Product parser sources, fixed workload counts and oracles are unchanged. A new
source-bound campaign is required; the original is never overwritten/replayed.
No timing is implied merely by preparing probes.

## Completed revised timing: promotion gate not passed

The revised campaign completed all 20 profiles:31 randomized pairs per profile,
1,240 measured processes plus 80 separate warmups. Every checksum passed; every
measured invocation exceeded 57 ms. The same exact original/durable parser hashes
were verified across service replay, exhaustive padding and timing probes.

| Family / mode | Short-valid ratio [95% CI] | Early-reject ratio [95% CI] |
|---|---|---|
| Original plain | 0.9788 [0.9253, 1.1279] | 1.0010 [0.9627, 1.0635] |
| Original optimized | 1.0048 [0.9864, 1.0475] | 0.9682 [0.8431, 1.0846] |
| Durable plain | 0.9952 [0.9036, 1.1428] | 0.9796 [0.9545, 1.0172] |
| Durable optimized | 1.0146 [0.9781, 1.0547] | 1.0074 [0.9718, 1.0548] |

Ratios are candidate/baseline; lower is faster. Only two of eight small-case
profiles meet the frozen point <= 1.03 and upper 95% <= 1.05 gate. Therefore the
**performance promotion gate is inconclusive / not passed**. Correctness does not
establish zero overhead. The optimized parser stays an opt-in isolated experiment,
with no default service or stable promotion and no retry to obtain narrower CIs.

Optimized-mode normal 300 / max 576 / malformed-final-byte work improves respectively
1.21x/1.37x/1.36x for the original parser and 1.21x/1.36x/1.46x for durable DHCP.
Those six 95% intervals exclude slowdown, but they do not cancel the incomplete
small-case qualification. All 20 rows, individual orders, input hashes, warmups
and paired observations remain in `timing-prepared-2/TIMING.json`.
The first failed campaign remains separate; the second was required by the proven
benchmark framing defect, not by a timing outcome. Framing controls passed 152/152
before the revised exclusive timing grant.

## Scope that does not pass by implication

The 24-gate firewall ledger remains broader: guest storage/time/packet adapters,
real OS DHCP clients, DNS forwarding/TCP, WAN/HA, IPv6 and other unimplemented
features cannot close from these tests. Older health/recovery controllers that
require private recovered company code are explicitly excluded, not silently
reconstructed or sent upstream. No company records, credentials or private
source were copied here. Original owner-tree hashes were rechecked after runs.

Preserved instrumentation failure: the first public-regression adaptation loaded
a nested oracle definition using its old relative path. It failed before the
checksum oracle ran. The second campaign uses reviewed support-source copies with
only explicit path substitutions; the oracle expectations were not relaxed.
The failed controller/log remains separate in `artifacts/.../net/public-1/`.
