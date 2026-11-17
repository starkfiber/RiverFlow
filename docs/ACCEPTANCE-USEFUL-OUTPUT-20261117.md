# RF2 acceptance and useful AI output — 17 November 2026

This sprint changes source and reusable developer libraries. It does not replace
stable Core/runtime downloads, default SDK v1, release archives, a company gateway
or a live RF2Net/RF2Ship deployment. Read the source-bound evidence index under
`experiments/acceptance-20261117/`; raw receipts remain project-local.

## Changes that work

- **RF2Ship:** observation retries remain allowed, but an uncertain mutation now
  raises `UnknownOutcome` before its first timeout can retransmit it. The original
  bug was reproduced on actual PC/Q35 guests; the fixed path passes 94 loss
  controls. The full fresh implemented acceptance passes 31/31 stages. Prepared
  candidate/build-only routes use the same verified optimized image and fixed
  helper, not an unrelated test-only implementation.
- **RF2Net:** original and durable DHCP parsers share the checked post-END padding
  optimization. Full implemented DHCP/DNS/durable/restart/loopback suites and
  public frame, checksum, binding, bridge, queue and admission regressions pass.
  All 55,611 padding cases plus metadata checks pass per probe across eight
  family/variant/compiler combinations; overlapping counts are not summed as
  unique features. No real LAN DHCP server is started.
- **JSON reports:** R3 uses the original scalar writer directly through 256 input
  bytes. This removes alias/density/wrapper overhead on small fields while retaining
  the large-value span route. All 12 small performance gates pass in the frozen
  31-pair campaign. Original alias, boundary-alias, 8,040 correctness and Passage
  Desk controls pass. Optimized ordinary/mixed inputs of at least 1 KiB show
  **1.391–1.771×** native-region gains. This is a different measurement scope from
  the earlier launch-inclusive 1.27–1.42× figures.
- **Useful AI library:** `text-report-cli.flow` owns exact argument/mode validation,
  bounded regular-file input, text validation, typed JSON/HTML composition and
  checked output. An application supplies the actual calculation in one typed
  callback. Shared plumbing is implemented and tested, not merely shortened in
  an AI answer. See `CLI-API.md` for the trusted synchronous Systems boundary.

## More reliable measurement, including failed ideas

The R3 optimized 16 KiB escape-heavy case remains **2.78% slower**, paired 95%
interval 1.32–6.37% slower. It is not universally regression-free.

R4 tried a leaf eligibility helper and direct scalar fall-through. Its correctness
passed but four small confidence gates and its targeted improvement gate failed.
It is **not promoted**. The complete once-only campaign retained all 26 profiles,
806 paired trials and 2,418 comparative processes. It also delivers checked
monotonic native timing: tick subtraction before rational timebase conversion,
overflow/backward/zero-timebase guards, exact output checks, source/binary pins
and comparison against an enclosing controller clock. See `sdk/r4/REPORT.md`;
negative results remain alongside gains.

The first Net timing attempt exposed a benchmark framing defect: a 584-byte
buffer could not hold a 576-byte packet plus its 10-byte test header. This was a
correct baseline rejection, not evidence of parser failure. The amended bounded
reader fills to EOF, admits 586 bytes and rejects extra/short input; 152 independent
framing controls pass. The original failed campaign and both retained timing rows
are preserved. The revised campaign completes all 20 profiles, 1,240 measured
processes and 80 warmups without checksum errors. Optimized normal/max/malformed
padding gains are 1.21/1.37/1.36× for the original parser and 1.21/1.36/1.46× for
its durable sibling. The small-case promotion gate remains **inconclusive/not
passed**: durable optimized short is 1.0146 candidate/baseline, 95% interval
[0.9781,1.0547]; early refusal is 1.0074 [0.9718,1.0548]. The candidate stays opt-in,
with no blanket zero-overhead or live-network promotion claim.

The TCP fixture also assumed an already-resolved neighbor could never expire.
Its correction admits only the exact expected ARP solicitation after a proved
three-second guest-cache expiry, then checks the original exact TCP output/state.
Seven independent admission/negative controls and a forced actual PC/Q35 expiry
replay pass; no guest timeout or guest code was relaxed.

## AI cost to correct software

| Condition | Actual outcome | Provider-reported tokens including repairs |
|---|---|---:|
| Manual line-report task | Initial + one repair fail compilation | 12,585 |
| Manual overlapping-search task | Initial + one repair fail compilation | 20,514 |
| New CLI library, line-report task | First call compiles; 46/46 complete-task checks | 6,887 |
| New CLI library, search-report task | First call compiles; 160/160 complete-task checks | 7,241 |

New calls used **14,128 tokens total**, 100.565 seconds of observed request time
and 2.462 seconds build/test time. This is descriptive evidence from two later,
nonrandomized trials, **not a general causal savings percentage**. The initial
smaller completion budget consumed another 7,274 tokens without complete source.
Two Report-condition transports have unknown usage; unknown is not zero. Total
known historical + new usage is 54,501 tokens, plus those unknowns. Reasoning and
cached tokens are subsets of their reported totals, never added twice. Shorter
source/answers are not used as productivity or billing proxies.

Actual generated apps additionally pass 16/16 exact-mode and 40/40 boundary/fault
controls. Golden A/B checks pass in plain and optimized modes, repeated against
the combined R3 + Report + CLI source package. These repeated controls overlap;
they do not establish 1,000 independent capabilities. APFS rejects creation of an
invalid-UTF8 filename (EILSEQ); that existing-path fixture is unavailable and
explicitly excluded, while malformed mode/query/input bytes are tested.

## Use the reviewed source package

```
python3 experiments/acceptance-20261117/package.py /new/persistent/sdk-directory
/qualified/rf2c APP.flow /new/rebuildable/app --compact --opt --sdk-root /new/persistent/sdk-directory
```

The package refuses an existing destination or changed pinned inputs, includes
per-file provenance and checksums, and does not overwrite default SDK/release
files. Compile only with the qualified 0.50 native compiler pinned by the runners;
place generated binaries in the guarded disposable cache. Unique source, Git,
inputs and receipts remain persistent. Shared-job retention is not approved for
SFE material, so no KHC/Memory/Chain offload is claimed.

The Ship 24-gate firewall ledger still has **11 tested subsets, 13 pending, and
zero fully qualified gates**. WAN/HA, complete TCP/IP, IPv6, guest-service adapters,
physical reliability and independent crypto review do not pass by implication.
The prior 5.11× matching-Oz authentication result is a host component benchmark,
not whole-network throughput. No new release or universal hardware claim follows.
