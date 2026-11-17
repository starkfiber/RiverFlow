# Stage-aware single-POST transport candidate

This new opt-in transport addresses the diagnostic gap exposed by the actual
136-second errno110 failure. The earlier v1 receipt could not distinguish DNS,
connect, TLS, request write or response timeout. This candidate changes actual
connection behavior: one chosen resolved address gets an explicit eight-second
TCP-connect/TLS socket timeout before any HTTP POST. It never retries another IP.
The provider hostname, TLS certificate/hostname verification and SNI stay intact.
The API credential remains on the explicitly selected host.

The existing transport and every frozen campaign remain untouched. No live
authenticated call has been made with this candidate. Changing a controller to
use this transport requires a separately reviewed protocol/configuration identity.

`provider_transport.remote_command(180)` returns the explicit SSH command.
`call_transport.invoke(payload_bytes,http_timeout=180,outer_timeout=420)` returns
`(receipt,response_or_None)` and recognizes the new safe v2 error schema.
All command/env selection remains explicit. Importing either module is inert.

The helper resolves only api.deepseek.com:443, selects its first IPv4/IPv6 answer,
connects once, verifies TLS, then sends exactly one fixed HTTP/1.1 POST. It does
not use proxy environment configuration or follow redirects. This direct socket
route is explicit; a proxy-only deployment is not supported. DNS still uses the
OS resolver and has no separately proven hard timeout; the caller's outer process
deadline bounds its observation. The post-connect socket timeout is180seconds,
not a total request/billing bound.

Safe failures include `phase`, numeric peer IP/family, `requestMayHaveBeenSent`,
status/type/errno, elapsed time, retry=false and usage=unknown. The may-have-sent
flag becomes true immediately before sendall, so a partial write is never labelled
safe to retry. Headers/body/read/output failures retain true. Pre-send failures
are not automatically retried either. No raw exception/config/header/error-body
is logged. Responses are bounded UTF8 JSON objects; incomplete declared content
length, excess body bytes and credential reflection refuse. All response/socket
objects close on success and failure. A caller must still reject a nonzero exit
even when stdout bytes were written before an output-flush failure.

Twelve offline unittest methods pass with fake DNS/socket/TLS/HTTP/output seams:
one POST, no address fallback, phase-specific timeout observations, conservative
partial-send marking, redirect/HTTP errors without retries, certificate policy,
invalid/incomplete response, credential reflection, malformed input/config and
v2 supervisor sanitation. No credentials or provider connections were used.
Source-bound receipts are in `artifacts/ai-transport-phases-20261117/controls-3`;
earlier ten/eleven-method qualification receipts remain retained. These controls
prove the injected call path, not a live provider SLA or the historical cause.
