# Reusable RF2 source SDK

`v1/` is the ready-to-use, versioned source package for the qualified 0.50 source compiler. Applications share this directory; they do not need copied `lib/` folders. Existing downloadable 0.46 compilers predate this package interface.

```flow
profile RF2_SYSTEM_A64_V1
use "@rf2/v1/text.flow"
fn main(argc,argv)
 let info=TextInfo(0,0,0,0)
 do text_measure("hello",5,info)
 return info.words-1
end
```

Build with an explicitly selected qualified compiler and absolute SDK path:

```
rf2c /path/to/application/main.flow /path/to/new-program --sdk-root /absolute/path/RiverFlow/sdk/v1 --opt
codesign -s - /path/to/new-program
```

The native compiler verifies the manifest and every imported module. No network install or runtime SDK lookup occurs. Package hashes establish byte identity, not publisher authentication; the selected directory and parent paths remain trusted. There is one supported source package version, not a dependency solver or registry.

[Package format, APIs and limits](../experiments/sdk-packages/README.md) · [Exact source provenance](v1/PROVENANCE.json) · [Native diagnostics](../experiments/diagnostics-050/README.md)

The development packager `python3 experiments/sdk-packages/package.py NEW-DIRECTORY` reproduces these source bytes. Python is only preparation tooling; the compiler and compiled apps do not require it. A source-package update requires a deliberately reviewed manifest/provenance update and new qualification. Preserve old versioned receipts rather than silently replacing tested identities.

To reproduce the qualified compiler, use `python3 experiments/sdk-packages/build.py /absolute/public-046/rf2c /new/compiler-directory`. The helper checks the public baseline hash, retains failed-step logs, and verifies exact signed self-generation. It never downloads a compiler or falls back to another account/runtime.

Current SDK edition **0.50B** adds explicit `io_write_no_sigpipe` and recoverable MCP transport failures with ordinary descriptor-policy restoration. [Passage Desk](../examples/passage-desk/README.md) demonstrates the shared package. The timed comparison used the preserved earlier SDK A; [the measurements](../docs/SDK-PACKAGES-0.50.md) give no retroactive time/token credit to this repair.

Optional measured candidate: `python3 experiments/evolution-20261117/package.py NEW-DIRECTORY` builds the shared JSON-span/report SDK without replacing this0.50B package. See [results and regressions](../docs/MEASURED-EVOLUTION-20261117.md). New report text/u64 fields support JSON and HTML; native-checked authoring context is available. This is an opt-in candidate, not a new stable release.
