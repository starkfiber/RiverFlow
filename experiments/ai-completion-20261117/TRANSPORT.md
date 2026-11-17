# Bounded completion transport

The new campaign explicitly selects `provider_transport.py`, an exact copy of the
qualified opt-in helper (SHA256
`ee0607ae3e221e510848cbffd4c69304a530d328e861f5cbefa4b0c83b586743`).
The previous frozen studies and their unknown failures remain unchanged.

`call_transport.invoke(payload_bytes, http_timeout=180, outer_timeout=420)` returns
`(receipt, response_or_None)`. The caller persists request, response and receipt.
It makes exactly one request; no transport retry or hidden model fallback exists.
The inner timeout remains a socket budget, while the outer timeout bounds the
local SSH subprocess observation. Neither proves provider cancellation or zero
billing on failure. No old timeout is retroactively explained by this change.

The supervisor accepts a response only after a zero transport exit, bounded UTF8
JSON-object validation, and complete delivery. Partial stdout is not treated as a
successful answer. Model output, finish reason and source validation remain the
campaign controller's separate responsibility. Reported usage is known only when
all three nonnegative integer totals are present and arithmetically consistent;
missing/malformed usage remains unknown. The raw complete provider response is
available to the caller even when usage is unknown.

Only strictly selected typed helper error fields survive to the receipt. Raw SSH
stderr, exception text and partial timeout output are not copied to it. The API
key stays on the explicit credential host. No Memory or KHC retention is used.

Offline qualification: 63 helper controls in 14 unittest methods and 10 supervisor
methods pass. These use fake openers, responses and subprocess results, never real
credentials or network calls. Raw evidence is project-local under
`artifacts/ai-completion-20261117/provider-controls-1` and
`supervisor-controls-1`. These tests do not establish live provider readiness.

One initial combined discovery run failed because the copied historical payload
test referred to a builder beside the new transport. The test now explicitly
references the unchanged historical builder. It is a historical reproducibility
control, not the new campaign payload. The failure occurred before any provider
call, and did not indicate a transport product failure.
