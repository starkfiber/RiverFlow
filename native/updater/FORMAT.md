# Experimental canonical format v1

All integers are little-endian u64. Limits: 32 records, 1 MiB per artifact or input
receipt, 16 MiB total state. Larger inputs reject. No parser accepts trailing bytes.

## Record

| Offset | Bytes | Meaning |
|---:|---:|---|
|0|8|ASCII RF2REL01|
|8|8|Schema 1|
|16|8|Contiguous sequence 1..32|
|24|8|Action 1 release / 2 authorized rollback|
|32|32|SHA256 of complete predecessor envelope, zero at genesis|
|64|32|Artifact SHA256|
|96|32|Source receipt SHA256|
|128|32|Compiler SHA256|
|160|32|Acceptance-evidence SHA256|
|192|32|Rollback target complete-envelope SHA256; zero for release|
|224|8|Rollback target sequence; zero for release|
|232|8|Artifact byte count|
|240|8|Platform 1 = macOS ARM64|
|248|8|ABI 1 = this explicit native tool profile|
|256|32|SHA256 of pinned publisher's 65-byte X9.63 public key|
|288|8|DER signature length, 8..80|
|296|variable|ECDSA P-256 SHA256 X9.62 DER signature|

Sign SHA256 of exactly 320 bytes: the 30 ASCII bytes
`RF2 release chain signature v1`, two zero bytes, then the first 288 record bytes.
Use Security's digest variant, not the message variant. A record envelope is
296 + signature-length bytes. Predecessor and rollback hashes cover the envelope,
including signature bytes. Strict DER interpretation is delegated to the P-256 verification provider;
no independent DER canonicalization or low-S restriction is imposed here.

For rollback, the target must be a release already in this client's accepted
history. Its envelope hash, artifact, source/compiler/evidence hashes, length,
platform, ABI and publisher must match exactly. High-water sequence still advances.

## State

Header: RF2CHN01 (8), count (8), high-water sequence (8), selected release sequence
(8), head-envelope SHA256 (32). Genesis has zero count/high-water/selection/head.
Then count entries, each record-length (8), record bytes, artifact-length (8),
artifact bytes. Duplicate artifact bytes on rollback are intentional in this small
prototype. Walk every record, parent, signature, length and artifact hash on read;
header claims must equal the derived values. No cached unchecked header shortcut.

## Trusted caller checkpoint

Exactly 80 bytes: RF2PIN01 (8), public-key SHA256 (32), high-water sequence (8),
head-envelope SHA256 (32). This is local trusted caller state, not a publisher
signature or a checkpoint accepted from the update payload. The caller must protect
and retain the newest one. Rewinding both this file and the whole store is outside
this prototype's protection. There is no timestamp/clock freshness claim.
