# Document Audit: native corpus fingerprints, lookup and agent summary

A small useful RF2 application for checking whether a selected text collection has
changed, finding an exact byte phrase, and giving an agent a bounded integrity
summary. CLI and MCP use the same native snapshot and SHA-256 implementation.
This is a working application experiment, not evidence that RF2 is universally
better than Python, a document database, semantic search or an authenticity service.

## Build and run

Use the corrected Mac ARM64 source compiler candidate 0.49 for new builds.
Earlier 0.48 compatibility results remain historical. From the repository root:

```sh
rf2c examples/document-audit/main.flow /new/path/document-audit --compact --opt
codesign -s - /new/path/document-audit
cd /path/to/your/documents
printf 'notes.txt\nchapter.txt\n' > selected.txt
/new/path/document-audit catalog selected.txt
/new/path/document-audit search selected.txt 'a phrase'
/new/path/document-audit check selected.txt LOWERCASE_CORPUS_SHA256_FROM_A_TRUSTED_BASELINE
/new/path/document-audit mcp selected.txt
```

The example manifest creation is an explicit user action. The native application
only reads files and writes its response to stdout/stderr. Existing documents and
the manifest are never changed. `check` succeeds only when the current corpus
fingerprint matches the supplied 64-character lowercase value. A mismatch returns
nonzero and `{"error":409}` on stderr, with no partial successful stdout.
Read/validation/output failures also return nonzero. Missing/invalid CLI modes are
refused; no operation is selected from environment variables.

The final MCP command speaks the legacy `2025-11-25` newline JSON-RPC subset over
stdio. Initialize it, notify `notifications/initialized`, then call the one tool
`audit_snapshot` with exactly empty arguments. The manifest is selected at launch;
the caller cannot supply paths, a new manifest, source or network authority.
Its result contains `schema:"rf2.document-audit.v2"`, counts, `corpus_sha256` and `index_via_cli:true`. The full file
index stays in the CLI catalog, avoiding the MCP library's 65,536-byte payload
limit for a valid corpus with long escaped names. Each tool call rereads the
selected manifest and documents; a later missing source yields `isError:true`,
never the previous successful snapshot. This is not a general MCP framework.

## Exact input/output contract

- Manifest: UTF-8, at most32,768 bytes,1..64 LF/CRLF-separated nonempty paths,
  each at most1,023 bytes. A final newline is optional. Duplicate textual paths,
  controls and malformed UTF-8 refuse. Paths resolve relative to **process cwd**,
  as the reused corpus library specifies. Absolute paths and traversal are not
  contained by a sandbox; only select a trusted manifest for a local agent.
- Each file: a readable regular nonsymlink UTF-8 file at most65,536 bytes; empty
  files are valid. Total content must be at most1,048,576 bytes. No PDF/DOCX/OCR
  or arbitrary binary parsing is claimed.
- Search:1..128 UTF-8 bytes, exact and case-sensitive, nonoverlapping matches,
  with original UTF-8 byte offsets. The v2 wire contract has
  `schema:"rf2.document-audit.v2"`: missing `first_byte` is JSON `null`; present
  offsets are small nonnegative integers, safe for JavaScript clients. It is not
  a grapheme offset. The earlier documented v1 u64 sentinel and its original
  results remain in the experiment history; they are not relabeled as v2 passes.
- The corpus hash is SHA-256 over ASCII `RF2-DOCUMENT-AUDIT-V1`, followed in
  manifest order by little-endian u64 path-byte length, exact path bytes,
  little-endian u64 content length and32 raw SHA-256 bytes of that file.
  Order, names and contents are therefore part of identity. It does not encode
  permissions, timestamps or provenance. A hash is not a signature; a malicious
  party able to replace both files and the expected digest can defeat a check.
- A snapshot means the application has completed a bounded sequential load before
  reporting. It is **not** an atomic filesystem snapshot across concurrently
  changing documents. Originals can change after a response. Shared static
  buffers and this stdio loop are sequential, not a concurrent server API.
- Catalog output is bounded to131,072 bytes. No database, persistent index,
  directory recursion, write tools or remote network service exists here.

## Test and reproduced correction

```sh
DOCUMENT_AUDIT_BIN=/path/to/document-audit python3 examples/document-audit/test.py
DOCUMENT_AUDIT_BIN=/path/to/document-audit DOCUMENT_AUDIT_NODE=/path/to/working/node python3 examples/document-audit/test.py
```

Python is test/oracle tooling only. The executable uses RF2 and normal Darwin
APIs; it requires no Python or Node runtime. The test suite uses an independent
`hashlib` framing oracle, exact byte search, controlled files and finite stdio
requests. It covers canonical hashes, content changes, immutable originals,
invalid/missing/symlink inputs, document/query/aggregate limits, agent argument
rejection, long escaped paths and source disappearance across live MCP calls.

Epoch1: native compile succeeded; the first Python controller had a spacing
syntax error, retained in its build evidence. After correcting the controller,
the initial app passed40 controls. The harder epoch then exposed an application
integration failure:32 valid long quoted paths produced a66,985-byte CLI catalog,
but sending that entire index through the generic MCP cap returned error28.
The original executable/source and failed oracle are retained. The corrected app
returns a bounded MCP summary while preserving the same fingerprint and full CLI
index. All 50 original controls passed in both native compiler modes. Those v1
reports and source hashes remain retained under their original identities.

Before publication, cross-track review requested an explicit v2 wire refinement:
JSON `null` replaces the intentionally documented u64 missing-offset sentinel,
with a schema marker. It is a disclosed output-contract change, not a new finding
against the documented v1 behavior. The independently computed corpus fingerprint
still uses the unchanged `RF2-DOCUMENT-AUDIT-V1` framing. Both native modes pass
53 controls when the working Node runtime is supplied, including schema checks
and a JavaScript parse/stringify/parse test with absent and present offsets.
The negative control confirms the former sentinel is not a safe JavaScript
integer. Without `DOCUMENT_AUDIT_NODE`, the Python/native tests still execute,
but the JavaScript check is unexecuted and recorded as such. No runtime app
dependency on Node is introduced.

The `lib/` files are unchanged internal RF2 SDK snapshots from public commit
`20dcf1d35dd13cc1adb24381b972c25536f59573`, under the repository MIT license.
`PROVENANCE.json` records their original locations and hashes. Copying these
internal modules exposes a remaining platform gap: package/import-root support
is still needed to avoid application-specific SDK snapshots drifting. These are
not newly recovered third-party sources. `artifacts/` keeps local receipts and
executables and is excluded from ordinary source publication.
