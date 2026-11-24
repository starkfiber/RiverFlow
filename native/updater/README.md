# Managed RF² Workbench updates

This macOS ARM64 candidate adds `rf2 update` to the installed Workbench command.
Other commands delegate to the packaged native runtime, including stdio MCP.
The installed `rf2c` command verifies and launches the selected compiler.
Both entry points are native executables built from the same Swift source. The package is assembled directly from the checked-in, hash-pinned Workbench archive.

## Provision and run

The release administrator provisions an owner-only state directory outside
the bundle. Keep that directory authoritative across bundle replacement.
Build into a new installation path. Python and the Swift toolchain are
needed to assemble the package. The resulting CLI does not require either.

```sh
mkdir -m 700 /absolute/owner-managed/rf2-trust
python3 tools/package-managed-workbench.py /absolute/new-install /absolute/owner-managed/rf2-trust
cd /absolute/new-install
./rf2 update enroll /publisher/public-key "$INDEPENDENT_PUBLISHER_SHA256" /release/genesis /release/rf2c
./rf2 update status
id=$(./rf2 update prepare /release/next-record /release/next-rf2c)
./rf2 update activate "$id"
```

Provide the first publisher fingerprint through an independent trusted
administrator channel. The package contains no enrollment key or default
publisher identity. Owners must explicitly provision the key even if the
release transport already supplied a public key. The actual signing provider
remains upstream of the installer and supplies an RF2REL01 record plus its
exact artifact. A signed rollback is a new record in the same chain and goes
through the same two commands, `prepare` and `activate`.

Prepare snapshots and verifies the inputs under the updater lock. Activate
reopens the current checkpoint and verifies again before materializing the
compiler. It flushes the generation before atomically publishing a single
active record digest. Repeating an interrupted activation can reuse an
identical unpublished generation. A stale record fails authentication against
the current release history. Previously published generations remain readable.
The journal uses its ordinary location and has its own lifetime.

`rf2c` opens the selected generation once, checks its release signature,
checkpoint and executable digest, then invokes it directly. `rf2 update status`
also audits the complete native history. The [shared RF2REL01 format](FORMAT.md) limits artifacts to 1 MiB and the chain to 32 records.

## Scope

The current qualification covers one local Mac installation, cooperative
writers and a separately retained owner-controlled trust directory. Restoring
the bundle alone preserves the checkpoint. A privileged or same-owner actor
with access to the trust directory can also restore the checkpoint. The
directory is no substitute for an independently protected monotonic anchor.
Production publisher enrollment and rotation, shipped integration, verified
upstream delivery, and physical power-loss testing are still open. The
package uses macOS ad-hoc executable signing and independent release record
authentication. There is no production signing identity in this test.

## Qualification

On macOS ARM64 with Xcode command-line tools, Python 3 and OpenSSL, choose a
persistent local test evidence directory outside disposable build output. The
runner generates test-only signing keys in a private temporary directory, uses
them through an independent publisher process, and automatically removes them.
Neither Python nor OpenSSL is part of the installed updater or compiler command.

```sh
mkdir -p "$RF2_TEST_EVIDENCE"
python3 -B experiments/typed-requests/prepare.py "$RF2_TEST_EVIDENCE/compiler-source"
python3 -B tests/managed-workbench/qualify.py \
  "$RF2_TEST_EVIDENCE/compiler-source/compiler.flow" "$RF2_TEST_EVIDENCE"
```

A working Node executable enables the additional JavaScript wire check in
Document Audit. Set `DOCUMENT_AUDIT_NODE` explicitly if multiple versions are
installed. The runtime tests cover Sensor Audit and Document Audit in plain and
optimized modes, normal MCP, Text Search, Text Audit, Booking journal persistence,
concurrent activation, trust refusals, restoration and signed rollback.
