# RF2 Documents

A local, read-only document workspace written in RiverFlow. Its native server loads an explicit list of UTF-8 text files, catalogues their contents in memory, searches that snapshot and renders an ordinary HTML/CSS reading interface. There is no browser script, external asset, embedded AI model or Node/Python user runtime.

`text-lines.flow` is a separate CLI application using the **same physical text and collection modules**. It reports the 1-based lines containing a supplied phrase. The verification controller mutates one shared library at a time in a disposable copy and confirms that both apps change, rather than merely containing similarly named helpers.

## Use the native bundle

Download the [Documents 0.37 development bundle](../../dist/documents-0.37/README.md), compare its published SHA-256, extract with Finder and enter the extracted folder in Terminal:

```sh
./workspace examples/documents/fixtures/documents.txt --serve
```

Open the printed `http://127.0.0.1:PORT/` address. Search document text, optionally ignore ASCII letter case, open a matching document and inspect its original source path. `Export catalogue` downloads JSON describing this loaded snapshot. Stop the server in Terminal with Ctrl+C. The executable does not open a browser automatically.

The included files are explicitly supplied programming examples, not recovered manuscripts or measured research findings. To use your own files, create a UTF-8 manifest with one path per LF-separated line:

```text
/absolute/path/to/notes.txt
/absolute/path/to/another document.md
```

Then run `./workspace your-list.txt --serve`. Relative paths resolve from the process's working directory, not the manifest directory. Paths are literal: no shell expansion, globbing, recursive scanning or URL downloading. A final newline is permitted; blank lines and repeated literal paths refuse. The same file reached through different parent-directory aliases is not deduplicated by inode. The final path component may not be a symlink; this is not a directory-containment sandbox.

The process reads all requested files before listening. An import error prevents serving a partial catalogue. It copies bytes into a bounded in-memory snapshot; it neither writes the originals nor automatically tracks later edits. Restart to load changed files. There is no guarantee of an atomic filesystem snapshot if another process changes a file while initial loading is in progress.

## Build from source

Select the existing 0.36 native compiler bundle as explained in [the first-app guide](../../docs/FIRST-APP.md):

```sh
sh tools/dev.sh build examples/documents/workspace.flow workspace-build --opt
sh tools/dev.sh build examples/documents/text-lines.flow lines-build --opt
./workspace-build/program examples/documents/fixtures/documents.txt --serve
./workspace-build/program examples/documents/fixtures/documents.txt --catalog
./lines-build/program examples/documents/fixtures/tamil.txt தமிழ்
```

The final command reports `{"bytes":166,"lines":3,"matching_lines":[1]}` for the current included fixture. `--fold` adds ASCII-only case-insensitive matching to text-lines. It does not implement Unicode case folding, normalization or semantic search.

The 0.37 bundle adds libraries and applications, using the unchanged qualified Mac compiler from the 0.36 bundle and unchanged 0.17 MCP runtime. It does not imply a new compiler backend or more MCP authority. Native execution remains qualified on Apple Silicon macOS. Binaries are ad-hoc signed, not notarized.

## Data and error contract

| Item | Current limit or behavior |
| --- | --- |
| Documents | 1 to 64 explicitly listed regular files, including empty files |
| Source path | At most 1,023 UTF-8 bytes, no C0 control bytes inside a path |
| Manifest | At most 32 KiB; LF or CRLF separators |
| One document | At most 64 KiB |
| Corpus | At most 1 MiB of loaded file content |
| Text | Strict UTF-8; NUL and C0 controls except TAB, LF and CR refuse |
| Search | At most 256 UTF-8 bytes; exact nonoverlapping byte matches, optional ASCII folding |
| Lines | LF boundaries; CR removed from CRLF lines; no phantom line after a final LF |
| Word count | Groups separated by ASCII space/TAB/CR/LF, not linguistic word segmentation |
| Preview | Complete selected file with HTML escaping; Unicode scalars are not grapheme counts |
| Catalogue | JSON source paths and snapshot statistics; no content hash or provenance authentication |
| CLI outcomes | 0 success, 2 invalid invocation, 1 operation failure with a numeric error on stderr |

The text-lines result can hold up to 4,096 matching line numbers. Exceeding that collection limit refuses before JSON output. A CLI write failure can leave a partial output stream; stdout is not transactional. File reads handle short reads, close their acquired descriptor on ordinary paths and preserve primary errors. Cleanup-only close errors use `65536 + errno`. Signals and fatal traps remain outside language cleanup; OS process reclamation is separate.

## Browser boundary

The listener binds only to `127.0.0.1` on an OS-selected port. It accepts read-only GET requests with the exact listener Host. An Origin header, when supplied, must match that local origin. The routes are `/` with bounded `q`, `doc` and `fold` fields, and `/catalog.json`. Unknown fields, duplicate fields, malformed escapes, invalid UTF-8 queries, out-of-range IDs, unsupported methods, ambiguous framing and extra initial request bytes refuse. No HTTP field is a file path, shell command, RF2 source or outbound URL.

Headers are bounded to 4,096 bytes, the request line to 2,048 bytes and individual header lines to 1,023 bytes. Eight client slots prevent idle preconnections from blocking a ready request. A ready request shares one two-second monotonic receive budget; each response has a two-second write budget. The sequential controller handles at most 4,096 processed requests, then closes its sockets. It is not a concurrent public internet service. A slow ready client can occupy the controller until its budget expires; a full client table may evict a waiting connection.

CSP disallows scripts, external assets, frames and foreign form actions. No-cache and MIME-sniffing headers are supplied. The application is not authenticated against another local process, which can reach the listener. Only load documents appropriate for that local session. Source paths appear in the local catalogue and source details; export them deliberately.

The interface uses visible search labels, keyboard focus, native controls, a responsive document list and an explicit empty-search state. It has no decorative animation or external font dependency. General UI/UX searches suggested marketing layouts; those were rejected for this reading workspace. The applied guidance is functional minimal layout, visible labels, contrast, keyboard access and useful no-result feedback. Actual browser acceptance is recorded separately from HTTP tests.

## Shared libraries

[API contracts](LIBRARIES.md) describe text validation/search/line iteration, bounded form decoding, HTML escaping, checked sorted unique items and structured row tables. They are trusted systems libraries, not generic language types, a package registry or a complete memory-safety proof. Raw byte ranges must be valid and meet their documented aliasing/lifetime rules.

## Verification and remaining work

```sh
RF2_TEST_COMPILER=/absolute/path/to/rf2c python3 tests/standalone/documents_verify.py
```

The developer controller builds both compiler modes, compares actual native results against independent byte/integer/UTF-8 oracles and tests malformed data, source/size limits, file types, closed output, descriptor balance, shared-library mutation, HTTP failures and snapshot behavior. Inputs are generated locally and contain no participant records. Keep failed prototypes and subsequent corrections in local artifacts; passing checks are finite evidence, not independent security certification.

See [the verification record](../../docs/DOCUMENTS-0.37-VERIFICATION.json). PDF/DOCX extraction, OCR, persistent indexes, edits/undo, watched updates, accounts, collaboration and broader platforms are not implemented by this app. No runtime-speed, model-token or learner/productivity advantage is claimed.
