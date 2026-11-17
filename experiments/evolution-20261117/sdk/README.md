# Native JSON serialization candidate — 17 November 2026

This is a real `.flow` SDK implementation candidate, not a changed compiler or an AI-inference service. The production SDK and stable releases are untouched.

## Reproduced bottleneck and implementation

`sdk/v1/text.flow::writer_json` calls `writer_bytes` once for each ordinary byte. Every call rechecks the writer error/capacity and enters a scalar copy loop. `json_spans.flow` scans ordinary bytes as a run and submits that run once. It keeps the existing escape spellings and per-escape atomic behavior. If a run exceeds remaining capacity it writes exactly the prefix the original byte-at-a-time writer would write, then reports the same error/used count. Source/output overlap delegates to the original implementation, preserving its forward-copy behavior rather than assuming `memmove` semantics.

R1 exposed a real loss on escape-heavy content: roughly 7–14% slower in the complete report task. R2 retains that receipt and adds a bounded 32-byte escape-density probe: short or densely escaped values use the original scalar writer. This probe is a heuristic, not a guarantee for arbitrary distributions. An ordinary prefix followed by dense escapes can still miss the scalar fallback. Tiny calls can still regress. Do not describe this candidate as universally faster.

`stage_sdk.py` creates a fresh complete SDK directory with the same `writer_json` and `writer_html` exports and a newly hashed manifest. Only `writer_json` behavior is implemented differently; `writer_html`, descriptors, partial transport, and no-SIGPIPE restoration remain unchanged. It refuses a changed baseline or an existing destination. No existing SDK directory is edited.

## Complete runnable job

`task.flow.in` is compiled twice from one source template, changing only the JSON function/import. It reads a bounded regular file, validates text for document mode, creates HTML-escaped text, and emits a JSON document containing the byte count, original text, and escaped HTML. The command runs native serialization repeatedly and writes the final result once. Input parsing, HTML construction, native startup, and final checked output occur in both versions. HTML is constructed once before the repeated JSON portion; the result measures repeat serialization throughput, not network/disk throughput or end-user startup improvement.

`qualify.py` pins the native compiler and SDK source identities, compiles/signs plain and optimized native images, validates the exact emitted bytes against a separate Python oracle, and runs 11 shuffled AB/BA process pairs per size/density/compiler-mode combination. It retains each trial/order, image/source/output hashes, and measured elapsed times. Failed oracle checks stop the run and retain the receipt. `integrate.py` qualifies the drop-in SDK against the unchanged Passage Desk acceptance and native source/output alias states.

```sh
python3 experiments/evolution-20261117/sdk/qualify.py \
  /Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program \
  artifacts/evolution-20261117/sdk/NEW-RUN
python3 experiments/evolution-20261117/sdk/integrate.py \
  /Users/ik/Projects/RiverFlow/artifacts/sdk-050-builder-final/program \
  artifacts/evolution-20261117/sdk/NEW-INTEGRATION
python3 experiments/evolution-20261117/sdk/stage_sdk.py \
  artifacts/evolution-20261117/sdk/NEW-SDK
```

Native task invocation (generated `program`):

```text
program MODE INPUT REPEATS CAPACITY INITIAL_USED INITIAL_ERROR RAW_CONTROL
```

Normal document: mode1, capacity16777216, initial/error0, raw0. Raw JSON writer controls: mode0, raw1. A normal document never outputs a capacity-failed buffer. The raw test path deliberately emits the partial buffer to compare exact historical failure behavior; do not treat that test mode as a production response API.

## Executed evidence

Credential-free receipts are ignored, local artifacts:

- `artifacts/evolution-20261117/sdk/run1/RESULTS.json`: first candidate, all 8,760 checks passed; escape-heavy runtime losses retained.
- `artifacts/evolution-20261117/sdk/run2/RESULTS.json`: R2, all 8,760 checks passed, including build/output/error/oracle controls and 660 paired native timing executions over 30 benchmark cases.
- `artifacts/evolution-20261117/sdk/integration2/INTEGRATION.json`: both compiler modes pass the unchanged Passage Desk 80-check oracle and each passes 73,728 native alias-state comparisons.
- `artifacts/evolution-20261117/sdk/FAILURE-HISTORY.json`: the initial two compilation mistakes, their preserved sources/logs, corrections, and R1 performance loss.

Controls include every byte value, NUL/C0 escape spellings, Unicode bytes, empty/random/mixed input, many capacities and initial writer states, preexisting errors, invalid text, missing files, invalid repeat/capacity arguments, closed stdout and an actual pipe with its reader closed. Raw byte JSON emission preserves baseline bytes; text validation belongs to document mode. These finite tests are not a memory-safety or platform-wide proof.

### R2 optimized complete-report results

Times are median process milliseconds at the recorded iteration count. Larger cases serialize about 1 MiB of source text per process. All output bytes match the independent oracle.

| Source bytes | Content | Repeats | Scalar ms | Span ms | Speedup |
| ---: | --- | ---: | ---: | ---: | ---: |
| 32 | ordinary | 2000 | 3.512 | 3.368 | 1.043× |
| 32 | mixed | 2000 | 4.111 | 4.140 | 0.993× |
| 32 | escape-heavy | 2000 | 3.976 | 4.185 | 0.950× |
| 1024 | ordinary | 1024 | 12.468 | 8.774 | 1.421× |
| 1024 | mixed | 1024 | 16.016 | 12.006 | 1.334× |
| 1024 | escape-heavy | 1024 | 22.591 | 22.648 | 0.997× |
| 16384 | ordinary | 64 | 12.710 | 8.972 | 1.417× |
| 16384 | mixed | 64 | 15.873 | 12.035 | 1.319× |
| 16384 | escape-heavy | 64 | 23.179 | 22.752 | 1.019× |
| 262144 | ordinary | 4 | 16.973 | 12.429 | 1.366× |
| 262144 | mixed | 4 | 18.535 | 14.573 | 1.272× |
| 262144 | escape-heavy | 4 | 25.951 | 25.981 | 0.999× |

Empty cases range around 0.95–1.01×; startup dominates and small ratios should not be interpreted as proven gains. Plain-mode large ordinary/mixed values improve about 1.18–1.39×; the 32-byte escape-heavy case loses about 9.4%. The escape-heavy fallback removes the large R1 loss in this workload, not all possible workloads.

These are local Darwin ARM64 results with a qualified 0.50 native compiler; no C/Python comparator is presented as the old RF2 baseline. This is actual native RF2 versus the unchanged native RF2 SDK. There is no measured reduction of billed AI tokens, no new cross-hardware claim, no stable-release replacement, and no remote execution.

Next gate: combine this source-bound SDK with the independent typed report-composition candidate, repeat its complete task and refusal controls, and only promote with explicit tiny/escape-heavy tradeoffs retained. AI authoring effort needs its own separately frozen comparison.
