# Studio 0.9 measured comparison

Final binaries, raw trials and exact encoded transcripts are in STUDIO-MEASUREMENTS-0.9.json and STUDIO-TOKEN-FIXTURES-0.9.json. Frozen 0.8 and final 0.9 were run on the same host in three fresh process sets, seven rotated trials per size after five warmups. MCP batches contain 50 small or 10 large operations. The table reports median trial times, not independent hardware populations or confidence intervals.

| Lines | MCP 0.8 µs | MCP 0.9 µs | Prepared 0.9 µs | Editor HTTP µs |
| --- | --- | --- | --- | --- |
| 1 | 55.99 | 57.42 | 52.60 | 938.04 |
| 32 | 143.39 | 142.89 | 135.73 | 1577.17 |
| 1000 | 2718.92 | 2733.86 | 2742.59 | 19174.67 |

Editor timing includes form encoding, POST, redirect, GET, complete HTML generation/transfer and checked result. It excludes browser layout/paint and is different work from MCP. No GUI existed in 0.8. The unchanged MCP operation performs similarly; broad acceleration is not established.

All nine discovered schemas are byte-identical. Matched prepared lifecycles include the catalog plus prepare, apply and release requests/responses. Across three 100-call samples the transcripts encode to 14,583 to 14,685 o200k_base or 14,260 to 14,362 cl100k_base tokens. Two samples match; in the other, 0.9 uses 102 more tokens. Twenty-call samples also vary by random handle spelling, including one older transcript 22 tokens shorter. This does not establish token reduction. Tokenizer: tiktoken 0.14.0. No model API was called for the experiment; these are exact text encodings, not provider billing or complete AI development costs.

The final run used runtime SHA256 35a5a4ab5bfcd8462598474562ee41c77a427da0de497a7d61fe0e1256f182d4. Background host load and power state were not experimentally controlled. Absolute timings differ from earlier development runs; retain the final raw trials and compare versions within this run, rather than selecting the lowest historical number.
