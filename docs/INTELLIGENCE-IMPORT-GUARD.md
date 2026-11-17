# Compiler import liveness and source-bound intelligence

Explicit maintenance candidate based on **0.50 / 34c29bc**. The installed plugin,
stable0.17, SDK B sources and published archives are unchanged. This is not an
upgrade of the runtime to0.51 or a new hardware claim.

[Reproduce the source/build](../experiments/intelligence/README.md) ·
[Source-bound receipt](INTELLIGENCE-IMPORT-GUARD.json) ·
[Audit of the prior paper](PAPER-AUDIT-20261117.md)

## Reproduced failure and actual correction

The 0.50 compiler already opens SDK imports nonblocking and checks regular files.
Its local-import path still used blocking `open`. An owned idle FIFO imported as
`helper.flow` waited until the test controller's one-second cutoff in **both
compiler modes**. The candidate opens local imports with Darwin O_NOFOLLOW |
O_NONBLOCK and checks fstat before reading. It closes and refuses nonregular
files, retains existing SDK refusal messages and does not change source budgets.

The fixed FIFO refuses promptly with no executable publication. Positive regular
and nested imports produce exactly the baseline executable bytes in both modes.
There is no general filesystem timeout or containment claim; trusted parent
paths and concurrent regular-file mutation remain outside this correction.

## Fresh acceptance evidence

| Surface | Executed result |
| --- | --- |
| Import/liveness controller | 24 checks passed; baseline FIFO hang and fixed replay retained |
| Native signed self-generation | Exact byte match with identical flags and basename |
| Existing SDK package controls | 96 passed |
| Existing structured diagnostics | 169 passed |
| Existing typed request/ownership controls | 354 passed with their actual0.48 negative baseline |
| Native structured storage red team | 82 passed |
| Stable Core regression | 317 admission checks and1095 execution comparisons passed |
| New host harness | 21 unittest methods passed; subcases are not a separate headline total |
| Actual runtime discovery | Nine schemas read from hash-bound native0.17 binary |
| RF2-aware context inventory | 233 tracked RF2/flow files; lexical only, no SAST verdict |
| WhatIF3.1 source scan | Five Python controllers covered, no heuristic leads; RF2 not covered by its scanner |

Counts overlap in purpose and are not summed into one invented unique coverage
number. All tests use synthetic owned files/local native processes. No network
probe, board flashing or provider call ran in this sprint.

## Intelligence layers implemented

1. **Actual capability context:** selected runtime status plus MCP tool schemas,
   bound to executable bytes. The host receives actual authority instead of
   inventing language/platform support.
2. **RF2 source context:** explicit Git-index coverage, bounded regular-file reads,
   line/hash references and lexical effect leads. Untracked/skipped files and
   unsupported analysis remain visible.
3. **Review acceptance gate:** complete stop reason, strict structured content,
   exact source/context identities, bounded findings and valid line references.
   Truncation, duplicate keys, stale context and injected command fields refuse.
   Accepted output is still only a hypothesis; no patches/commands execute.
4. **Measured build advice:** derive paired medians/wins, require matching image
   hashes, reject nonfinite/insufficient data, retain clean unless a material
   reproducible reuse advantage exists. It does not dispatch a compiler.

These are dependency-free Python **developer controllers**, not user-runtime
requirements, an embedded model or expanded MCP effects. No SFE source/data was
sent to Kanika Memory, Chain, shared KHC jobs or retained harness sessions.

## Fresh optimization evidence

Eleven randomized-order paired trials per workload using the **new current
candidate**, with identical source/options, clean-byte comparisons and independent
arithmetic/execution checks. Compilation includes process launch and output;
signing and executing the generated program are excluded from timed samples.

| Helpers | Clean median ms | Warm reuse median ms | Current observation |
| --- | ---: | ---: | --- |
| 1 | 5.512 | 6.477 | 17.5% slower |
| 80 | 6.122 | 7.293 | 19.1% slower |

The new advisor recommends **clean** for both. This is a route-selection result,
not a machine-code speed improvement. Cold-cache setup and all raw pairs remain
in the receipt. It does not negate historical SHA40 gains on a different workload.
Do not reuse the older paper's~25% number as a current0.50 measurement.

## WhatIF and external references

WhatIF's review/replay discipline is applied to native controllers; its built-in
HTTP/backend engines do not execute RF2 compiler tests. The Python source scan
is separate from actual native test evidence. No libFuzzer engine was installed
or claimed. The next mutation work should retain fixed seeds, minimized failure
fixtures and bounded replay, as described in the primary
[LLVM libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html) and
[LLVM testing policy](https://github.com/llvm/llvm-project/blob/main/llvm/docs/DeveloperPolicy.md).
These are referenced practices, not copied licensed implementation.

## Preserved corrections and next work

Guard preparation initially refused the old snapshot's patch against the new
SDK-composed source. The builder initially used different self-output basenames,
which alter ad-hoc signing identity. Two synthetic unit fixtures were corrected
for Git staging rules; a historical negative-baseline misconfiguration was
corrected before the request suite rerun. Original failures remain private under
`artifacts/intelligence-051/`. No test oracle was relaxed to hide a product defect.

Next: bounded grammar-aware mutation/minimization and independently checked
resource-state transitions; real provider-to-new-schema acceptance if separately
selected; a held-out build selector trial. Typed JSON/HTML/report composition
remains the main product effort. The fixed11/12 delivery ledger is unchanged.
