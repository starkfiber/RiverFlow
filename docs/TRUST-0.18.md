# RF2 0.18 development edition: verification and trust

Status: working native development candidate, 13 November 2026. Stable 0.17assets remain unchanged. This edition adds applications and an optional contract MCP service using the existing native compiler; it does not claim new general language syntax or complete ecosystem parity.

## What is working

* A separate native `rf2-verify` executable, built without importing the production engine or its plan parser. It follows each original byte through operations and tracks its changing position, rather than using the engine's array-pass reference or fused-output path.
* RF2A1 authenticated receipts using full 256-bit HMAC-SHA256 tags and 32-byte shared keys. The issuer independently checks complete output and report fields before computing a tag.
* Three bounded native stdio tools: `contract_status`, `contract_run` and `contract_verify`. The original nine native tools are retained in the original server.
* A guarded fast path composes uniform XOR maps, reversals and identity ADD0. Any nonzero ADD retains the ordered candidate loop. Checked semantics and abstract work counts remain unchanged.

## Build and use

The development builder needs Python standard library and the already built RF2 compiler. Resulting native programs need no Python, Node, npm or C++ runtime.

```sh
python3 tools/build-trust.py output/trust-0.18
mkdir -p "$HOME/.config/riverflow"
output/trust-0.18/rf2-trust keygen "$HOME/.config/riverflow/receipts.key"
output/trust-0.18/rf2-trust issue "$HOME/.config/riverflow/receipts.key" examples/evidence-contract/demo.plan > demo.auth
output/trust-0.18/rf2-verify "$HOME/.config/riverflow/receipts.key" demo.auth
```

Choose a new build directory if that output already exists. Key generation refuses existing files and symlinks. Preserve earlier keys for their intended historical verification; rotation requires an explicitly managed new key and server restart. Never reuse the public test fixtures as operational keys. The local administrator-created key is read at startup, not chosen by a tool call.

## MCP setup

The 0.18 development plugin configuration includes the existing `rf2` server and the new `rf2-contract` launcher. A previously installed 0.17 cache does not automatically change during this coding chat. Reload/reinstall the updated development plugin to load the new configuration. The launcher uses `RF2_TRUST_BIN` or `output/trust-0.18/rf2-trust`, and `RF2_TRUST_KEY_FILE` or `$HOME/.config/riverflow/receipts.key`. It fails closed if setup is missing and never generates a key or falls back to another runtime.

```json
{"name":"contract_run","arguments":{"plan":"RF2E1 allow 7 budget 6 input 3 1 2 3 steps 1 xor 2\n"}}
```

Only an 8192-byte RF2E1 plan or 18000-byte RF2A1 capsule is accepted. Unknown argument fields, paths, key overrides and systems source refuse. `contract_run` returns output, code, work and capsule. A nonzero program code is an authenticated refusal witness, not a successful transformation; clients must inspect code. `contract_verify` authenticates and reconstructs semantics. Tool calls do not open caller files or create network connections. Startup reads the administrator-selected key; normal stdio descriptors and OS memory remain part of the host. Host access/consent governs which clients can ask this signing service to issue admitted results.

## Format and threat boundary

RF2A1 is eleven whitespace-separated tokens: `RF2A1 source SOURCE64 key KEYID32 receipt RECEIPT64 tag TAG64 plan PLANHEX`. All hex fields are lowercase. Source is the expected bundle identity; key ID is the first 16 raw bytes of SHA256(`RF2-KEY-ID-1` ASCII || 32 raw key bytes), hex encoded. The receipt remains the defined RF2E1 result digest.

The HMAC message is ASCII `RF2-AUTH-CAPSULE-1`, source identity as 64 ASCII hex bytes, 32 raw receipt bytes, 32 raw SHA256 of exact plan bytes, then 16 raw key-ID bytes. The fixed 32-byte key is used with the standard HMAC-SHA256 construction. There are no separators or terminators; every field has a fixed width. Source-version mismatch, key mismatch, changed fields or changed tag refuse. A valid tag with an incorrect semantic result also refuses in the separate verifier.

This is shared-key authentication under trusted key custody. Anyone holding the key can create valid tags. It is not a public-key digital signature, exclusive author identity, nonrepudiation or authenticated hardware execution. Replay is intentionally permitted; no timestamp, expiry or replay counter exists. Keys are plaintext local files, required to be regular, no symlink, exactly 32 bytes, owner-held and mode 0600, checked on the opened descriptor using Darwin stat64. Key creation uses OS entropy and exclusive create. ACLs, privileged processes, compromised hosts, secret backups and physical memory attacks are not qualified. Best-effort zeroing is not proven secure erasure. The MAC construction has finite conformance tests, not an independent cryptographic audit or sidechannel certification.

## Failure evidence

The trust suite passed 520 checks, including wrong keys, altered tag nibbles, stale source/receipt/plan fields, key file policy, malformed plans, 180 fresh seeded plans, forbidden MCP arguments, duplicate/escaped JSON keys, oversize requests and recovery. The independent SDK also exercised native tools with server PATH=/nonexistent. HMAC matched all seven RFC 4231 cases and 90 seeded cases in both native modes: 194 checks. The separate plan verifier matched 131072 one-byte ADD/XOR cases in each mode: 262144 observations. Full output, tail sentinel and error fields were checked within that domain.

An executed mutation control changed XOR to OR in both engine paths. The separate verifier stopped issuance. Another deliberately introduced the same defect into the verifier; all three then agreed on the wrong result and accepted it. This permanent negative control prevents an independence claim from becoming an absolute correctness promise. The algorithms share compiler, cryptographic helpers and specification. A separately implemented toolchain/model is still a research gate.

## Matched engine measurements

The frozen baseline is commit 525cc6d, using the same native compiler and optimization option. Each of six eligible XOR/reversal workload shapes has two warmups and 21 randomized-order trials for reference-only, previous dual and candidate dual execution. Repeated in-process transformations include initialization, observation and process launch. This is the engine experiment; it excludes the new parser, independent verifier, hashing, MAC and MCP transport.

| Bytes | Steps | Previous dual median ms | Candidate median ms | Candidate/previous |
| --- | --- | --- | --- | --- |
| 8 | 1 | 25.268 | 23.613 | 0.934 |
| 8 | 8 | 11.031 | 8.158 | 0.740 |
| 8 | 32 | 10.220 | 6.656 | 0.651 |
| 128 | 1 | 27.728 | 25.593 | 0.923 |
| 128 | 8 | 10.385 | 7.824 | 0.753 |
| 128 | 32 | 17.568 | 10.643 | 0.606 |

The confirmation medians were 6.6% to 39.4% lower for the candidate on these six eligible shapes. Both initial and confirmation runs are retained; the confirmation table is not a universal speedup or an isolated CPU-cost estimate. Nonzero ADD uses fallback. Correctness and mutation tests remain necessary. [Raw engine measurements](TRUST-0.18-ENGINE-MEASUREMENTS.json).

## Complete local MCP measurements

| Bytes | Steps | Run median ms/call | Verify median ms/call |
| --- | --- | --- | --- |
| 8 | 1 | 0.0648 | 0.0607 |
| 128 | 8 | 0.2429 | 0.2469 |
| 128 | 32 | 0.2707 | 0.2617 |

These are 11 trials of 20 calls per tool after 3 warmups in one local stdio session. They include Python host JSON encoding/decoding, pipes and the full native operation. They are not pure engine timings, network service latencies, AI task costs or billed token measurements. No previous authenticated MCP baseline existed. [Raw MCP observations](TRUST-0.18-MCP-MEASUREMENTS.json).

## Cleanup and the next gates

The source inventory counts developer tests and publishing tools alongside RF2. It is not a runtime dependency or performance chart. Generated copies retain explicit derivation and are marked accurately rather than relabelled as another language. Refresh it with `python3 tools/source-inventory.py`; retain the reference oracles.

Next gates: independently reproduce on another host/toolchain; inspect the protocol and cryptographic implementation externally; establish a signing/key-rotation threat model if public signatures are required; test whole developer repair tasks; broaden language capabilities with real target qualification. The stable release and published download assets remain 0.17 until their own release qualification and packaging are completed.

Primary references: [HMAC construction, RFC2104](https://www.rfc-editor.org/rfc/rfc2104), [HMAC-SHA256 test vectors, RFC4231](https://www.rfc-editor.org/rfc/rfc4231). Tests support scoped implementation behavior, not degree approval or claimed new cryptography.

## Hosted qualification and application continuation, 13 November

A second hosted ARM Mac exposed a macOS 15 loader-container defect, now corrected in the native emitter and retained development encoder. The failed bootstrap and intermediate repairs are preserved. The final hosted run passed the finite suites, including 245 additional key/protocol checks. This is another environment of the same architecture and toolchain lineage. Rotation requires service restart. See [deployment and compatibility record](STACK-LAB-0.18.md) and [final hosted evidence](SECOND-HOST-0.18-FINAL.json). The final exact candidate archive also passed hosted qualification; see EXACT-PACKAGE-0.18-SECOND-HOST.json. Stable downloads remain 0.17.
