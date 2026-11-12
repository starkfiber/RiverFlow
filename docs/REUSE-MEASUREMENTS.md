# Release 0.8: measured reuse and native workspace

The final measured native binary is bound by SHA-256 in REUSE-MEASUREMENTS-0.8.json. Frozen 0.7 is the comparison, alongside the same JavaScript exact-integer comparator. Three fresh process sets, seven rotated trials per size/variant, five warmups and 50 small or 10 large requests per trial. Results are medians of 21 batch averages. Controller JSON encoding, pipe transport, parsing, calculation and result checking are included. Startup, schema discovery and plan preparation are excluded from latency. One local host, no isolated kernel speed, statistical confidence interval, energy or universal advantage claim.

| Lines | Native 0.7, µs | Native 0.8, µs | Prepared 0.8, µs | JS, µs |
| --- | ---: | ---: | ---: | ---: |
| 1 | 18.99 | 18.84 | 17.27 | 25.12 |
| 32 | 57.95 | 50.43 | 49.03 | 32.48 |
| 1000 | 1187.25 | 962.26 | 959.95 | 294.88 |

The 1000-line unprepared 0.8 request is about 19% shorter in this local round-trip measurement than 0.7. JavaScript remains substantially faster on larger inputs. Prepared-plan latency helps most on small inputs; reusing a plan does not remove validation of new lines.

Batched development phase probes retain raw process times, including first-launch variation, in INVOICE-PHASE-PROFILE-0.8.json and INVOICE-PHASE-PROFILE-OPTIMIZED-0.8.json. They suggest validation was a useful target. The phases use cached bytes/tokens/words as appropriate; their medians cannot be added to reconstruct a full request. The changes avoid repeated field lookups, fast-path ordinary u32 decimal integers with unchanged exact-number fallback, and borrow unescaped JSON string bytes only for the active request. Escapes, malformed UTF-8, control characters and duplicate decoded keys retain refusal checks. This is not an independent parser audit.

## Complete reuse interface experiment

Prepare, inspect the returned currency/tax rules, apply fresh lines repeatedly, then release. Counts include all nine discovered 0.8 schemas versus all six 0.7 schemas and every request/response in the lifecycle. Three independently issued handles per workload expose spelling variability. Exact fixtures and both encodings are retained in REUSE-TOKEN-FIXTURES-0.8.json and REUSE-MEASUREMENTS-0.8.json.

| Calls | Reuse, o200k | Unprepared, o200k |
| --- | ---: | ---: |
| 1 | 1119 to 1122 | 689 |
| 20 | 3703 to 3725 | 3577 |
| 100 | 14685 | 15737 |

Reuse costs more at one and twenty calls in these fixtures. At 100 calls it costs fewer encoded tokens. The observed crossover is between the tested 20 and 100 calls, not an exact break-even estimate. These are tiktoken 0.14.0 text counts, not billed model usage. Shared initialization, model-specific framing, prompt caching, capability construction, failures/repairs and hidden reasoning are not measured. No inference API was invoked; no actual AI-task usage receipts are claimed.

## Reproduce

Development controllers use Python and the Node comparator. End users do not need them.

```sh
RF2_TEST_BINARY=/path/to/0.8/rf2 RF2_BASELINE_BINARY=/path/to/0.7/rf2 \
  python3 tools/measure-reuse.py
```

This release also adds explicit CLI-only saved invoice documents, new-file edits and direct native PDF export. See INVOICE-WORKSPACE.md. It is a file-based application; a graphical editor is still future work. Saved plan handles are not durable documents or user authentication; see PREPARED-PLANS.md.
