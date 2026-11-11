# Capability measurements, release 0.7

These measurements describe one local Apple Silicon Mac and the exact source/binary fingerprints retained in CAPABILITY-MEASUREMENTS-0.7.json. They are observations, not a universal speed or token-saving claim.

## Execution experiment

Three fresh process pairs, seven rotated trials per pair and workload size, five warmups, 50 requests per small-workload batch and 10 per 1000-line batch. Each timed request checks its full result. The Python controller measures persistent JSON-lines request round trips, including controller serialization, IPC, parsing, validation, calculation, output and controller result checking. Process launch, discovery, compilation and model inference are excluded. Times are medians of 21 batch averages, not individual request percentiles or statistical confidence intervals. All raw trials are retained.

The native invoice capability is compared with a straightforward JavaScript BigInt implementation using explicit currency/tax fields. Both use the same lines and produce identical totals. The comparator does not have the native transport's duplicate-key rejection; these timing inputs are valid canonical JSON, so the experiment does not compare adversarial parser guarantees. Both sources are available for inspection. A separate pair compares exactly the same general Core subtotal program in native 0.6 and 0.7, including identical abstract work counts.

| Lines | Native invoice, µs | JavaScript explicit config, µs | Core 0.6, µs | Core 0.7, µs |
| --- | ---: | ---: | ---: | ---: |
| 1 | 18.53 | 26.73 | 68.14 | 68.07 |
| 32 | 57.22 | 32.03 | 84.26 | 83.96 |
| 1000 | 1195.59 | 301.58 | 593.24 | 587.50 |

The native invoice path is faster on the one-line input and slower on the larger inputs. Core 0.6 and 0.7 remain close in this experiment; small timing differences do not establish a compiler improvement. Large-input native parsing, generated frame traffic and repeated work checks need profiling before choosing an optimization. This experiment does not isolate any one of them as the cause. There is no energy, phone or multicore result.

## Encoded interface counts

The exact serialized tool schemas, 20 requests with the same two-line data and 20 corresponding responses are retained in INTERFACE-TOKEN-FIXTURES.json. Schemas were read from the running native and reference processes. tiktoken 0.14.0 counts these exact strings using two named public encodings. The plan has 19 tokens, but its repeated request representation is longer than direct currency/tax configuration.

| Encoding | Plan alone | Native schema + 20 round trips | Explicit schema + 20 round trips |
| --- | ---: | ---: | ---: |
| o200k_base | 19 | 3193 | 3010 |
| cl100k_base | 19 | 3128 | 2945 |

The table includes only the selected tool schema, not the whole native six-tool catalog. That full catalog is counted separately in the JSON report. The native request includes a readable plan; the reference request supplies currency and tax_bps directly. Both perform the same calculation and return the same result fields. A small standalone plan does not establish a cheaper complete interface.

These are actual encoded fixture counts, not billed inference usage, hidden reasoning tokens, model-specific framing or a measured AI coding conversation. No inference API was invoked. Prompt caching, capability construction, failed model proposals, tool selection and repairs remain unmeasured. A defensible task-level saving claim requires matched complete model runs and their actual usage receipts, including unsuccessful runs.

## Reproduce

Use the release's native binary with RF2_TEST_BINARY and an extracted 0.6 binary with RF2_BASELINE_BINARY. Development measurement requires Python, tiktoken and Node 22; the user runtime does not.

```sh
RF2_TEST_BINARY=/path/to/rf2 RF2_BASELINE_BINARY=/path/to/0.6/rf2 \
  python3 tools/measure-capability.py
```

The comparator uses exact integer arithmetic. The native kernel is separately compared with 0.6 Core and independent Python arithmetic in tests/standalone/invoice_verify.py. Repeated cases and these comparisons are software tests, not independent peer review.
