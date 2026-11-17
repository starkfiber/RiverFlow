# R5: direct byte emission, with R3 dispatch retained

R3's escape-heavy large fallback delegates to the original scalar writer. Each quote/backslash/newline/carriage-return/tab escape pays `writer_text → io_size → writer_bytes → io_copy`. General C0 controls additionally append two hex bytes through separate writer calls. R4 only rearranged the large fallback's call frame; its frozen campaign failed promotion and did not establish that this dispatch caused the slowdown.

This candidate changes the work performed per escape. A leaf `json_emit_byte` checks sticky errors, `used <= capacity`, and remaining capacity, then directly stores the bytes. It performs no string sizing or copy calls. The dense loop still loads each source character at the original scalar iteration boundary. The span scanner uses the same emitter when it encounters an escaped byte.

The <=256-byte scalar body, alias checks, 32-byte density threshold and ordinary span copying remain R3's implementation. All aliases still delegate to the unchanged original scalar writer. This avoids using a fast disjoint emitter where a forward source/output overlap may modify the next source character.

Two-byte escapes remain atomic. General C0 output preserves three legacy commits: `\\u00` as one four-byte unit, then high hex, then low hex. If only four or five bytes remain, the same prefix is committed and error28 becomes sticky. No whole-six-byte reservation silently changes partial output. Bounds are checked before pointer stores; `used > capacity` and extreme unsigned used values are covered separately.

Existing oracle, alias and Passage controls are unchanged. Extra tests target every C0 byte in a 257-byte dense input, quote/backslash runs, mixed-density dispatch boundaries, capacities around each partial prefix, sticky errors and invalid unsigned Writer states. A harness input-limit error is preserved separately from code failures.

The coordinator granted one exclusive sprint timing slot. The frozen, repeated shuffled campaign used the previously qualified monotonic clock and complete output/consumption validation for scalar baseline, R3 and this candidate. All six large escape-heavy targets improve against both references; one small row fails the fixed minimum-duration gate. Consequently the candidate remains unpromoted. See README.md and EVIDENCE.json for all26 profiles and the preserved refusal. Passing correctness or these finite timing controls does not establish universal compatibility, Core/MCP admission or production readiness. Stable/default SDKs remain unchanged.
