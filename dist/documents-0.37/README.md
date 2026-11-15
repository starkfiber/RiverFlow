# RF2 Documents 0.37 native development bundle

A read-only local document workspace and a separate line-search CLI, built in RiverFlow and using the same reusable text/collection modules. Host: Apple Silicon macOS. Ad-hoc signed, not notarized. The included compiler is unchanged from the 0.36 bundle; the unchanged MCP runtime reports 0.17.0 and exposes nine bounded tools. This package version identifies the new libraries/applications, not a new compiler backend.

[Download the ZIP](RF2-Documents-0.37-dev-macos-arm64.zip) · [SHA-256](RF2-Documents-0.37-dev-macos-arm64.zip.sha256) · [File manifest](MANIFEST.json)

Extract with Finder, enter the extracted folder in Terminal, then run:

```sh
./workspace examples/documents/fixtures/documents.txt --serve
```

Open the printed local URL. Stop with Ctrl+C in Terminal. To use your own text files, supply a manifest with one literal file path per line. Paths resolve from the current working directory. The app neither scans unrelated folders nor writes original files. Limits: 64 files, 64 KiB each, 1 MiB total, strict UTF-8; search up to 256 UTF-8 bytes. The snapshot stays in memory until the process ends. Other local processes can reach the unauthenticated loopback listener.

```sh
./workspace examples/documents/fixtures/documents.txt --catalog
./text-lines examples/documents/fixtures/tamil.txt தமிழ்
./rf2 mcp
```

The ZIP includes native workspace/text-lines/compiler/runtime executables, source, example inputs, the existing developer build helper and a checked file manifest. No Node/Python/C++ user runtime is needed. Test controllers are separate developer tools. PDF/DOCX extraction, editing, persistent indexes, accounts, collaboration and additional OS targets are not implemented here. No new performance, AI-token or independent security certification result is claimed.

[Full application and source-path contract](../../examples/documents/README.md) · [Reusable APIs](../../examples/documents/LIBRARIES.md) · [Functional verification](../../docs/DOCUMENTS-0.37-VERIFICATION.json) · [Package checks](../../docs/DOCUMENTS-0.37-PACKAGE.json)
