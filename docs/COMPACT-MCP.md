# Opt-in compact MCP output

`rf2 mcp` retains the existing result format and nine schemas. `rf2 mcp --compact` changes only successful rf2_check/rf2_run responses: the redundant readable summary is omitted and content is an empty array. The complete structuredContent remains. Error messages, bounds, discovery schemas, status, lowering source and application tools retain their contracts. This mode is for clients that read structuredContent; text-only clients should retain the default.

The option does not allow module imports, trusted systems source, compilation, files or raw platform calls over MCP. Compact output does not change what a program is permitted to do. Rejected requests and successful recovery after an error are tested.

The measured session contains initialization, discovery, 100 actual POPCOUNT requests/results and one checked overflow error. Exact tokenizer counts include complete retained exchanges. The comparison is a reduction in encoded text, not an inference-speed experiment, model bill, guarantee of better code generation or full-task productivity result. See LANGUAGE-MEASUREMENTS-0.10.json and LANGUAGE-TOKEN-FIXTURES-0.10.json.
