# Opt-in structured provider transport

`provider_transport.py` is a new candidate, separate from every closed study's
frozen transport and controller. It is not installed as the default or used for a
real request in this refinement. Importing it reads no configuration and performs
no network action. A caller must explicitly select the authorized SSH host and
remote configuration-file reference before asking for its command. The helper
keeps the API credential on that host and sends one HTTPS POST to the fixed
provider endpoint. TLS verification is unchanged; redirects are refused before
forwarding the Authorization header. There are no retries.

The complete request is bounded to 120,000 bytes and must be a UTF8 JSON object.
The response is bounded to 2 MiB and validated before output. A reflected credential
causes refusal rather than being copied to stdout. The remote configuration read
is bounded; it requires one well-formed API-key entry and never prints the file,
its path or its other entries. A successful response is returned unchanged and explicitly flushed before the
helper reports success. Write and flush exceptions are classified as output
failures, with safe reason/errno fields; already-written bytes cannot be revoked.

A failed helper emits one short `rf2.provider.transport.error.v1` JSON line on
stderr. Its allowlisted fields are category, type, httpStatus, reasonType, errno,
elapsedSeconds, retryPerformed=false and usage=unknown. It does not serialize an
exception's message or traceback, request, headers, configuration or error body.
HTTP401/429/500 remain distinct status values; DNS, timeout, TLS, network,
configuration, input and output failures have explicit categories and safe
reason types. An error-stream failure is contained. Provider-error usage remains
unknown; no zero-billing assumption follows from a failed response.

The HTTP timeout is a socket observation budget, not a proof that every system
DNS operation finishes within it. Callers must retain a separate bounded outer
transport deadline (the previous studies used 195 seconds). If a process is killed
before it can emit an error, usage and cause can still remain unknown. SSH-layer
errors are outside the helper's sanitized-error contract. Short/failed stdout can
already contain written bytes; consumers must require successful transport and
parse a complete response before accepting it.

## Offline evidence

`provider_transport_tests.py` injects fake HTTP openers, configuration readers,
responses and streams. The qualified third run passes 63 controls in 14 stdlib test
methods: success bytes and request construction, 401/429/500, direct/wrapped
timeout and DNS, TLS/refused connections, opaque exception reasons, bad payloads,
configuration cases, response bounds, literal/escaped credential reflection,
write/flush failures and explicit success flush, explicit host/config reference
validation and redirect refusal.
A secret marker in synthetic credentials, paths, exception messages and bodies
never appears in the observed stdout/error records. No real credential file or
provider connection is used. These controls do not establish a live provider SLA
or recover the unknown causes of the historical transport failures.

`prepare_prompt_contract.py --out NEW_PERSISTENT_DIRECTORY` recreates the exact
reviewed initial pilot payload 014d18a700642dab98a1f71da790af16d8eead7ae10d327f143e6c30b88ef442.
It makes no provider call and refuses drift or an existing output directory.
The previous frozen payload/controller identities remain untouched.

The output controls qualify function-level write/flush failure handling only.
They do not prove every interpreter-shutdown or operating-system pipe behavior.
A consumer must reject nonzero transport status even if partial or complete bytes
were written before a flush error. The prior 61-control receipt and source are
preserved before this correction; its old output-category gap is not hidden.
