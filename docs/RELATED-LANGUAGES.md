# Related language review, 0.10

Scope: selected public source/document inspection at pinned commits. No third-party compiler, runtime or model was executed. Project README claims are not benchmark receipts. No imported implementation code, new third-party runtime or assertion of world-first novelty is involved. Retained local source files and SHA256 values are indexed in the project-owned Reverse Lab case; public provenance is in RELATED-SOURCE-REVIEW-0.10.json.

| Project | Evidence inspected | What RF2 can learn | Boundary |
| --- | --- | --- | --- |
| [BoundaryML/baml](https://github.com/BoundaryML/baml/blob/3edc5e158e68be4d63849e917c47341ca7a76969/README.md) | README, record fixture and MCP connection cleanup test | Types and lifecycle tests belong beside the interface | Claimed compiler speed is not independently measured here |
| [Sowiedu/Edict](https://github.com/Sowiedu/Edict/blob/2dbed48beda84d43e746ebec8bc3d98bcdcc63b0/README.md) | MCP pipeline handlers, minimal-schema transformer, record and module examples | Structured diagnostics, explicit effects and optional compact interfaces | Selected static source is not execution coverage or an audit of its verifier |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy/blob/398396012371a95471c8e7be24a70e6660e87aa4/README.md) | README and linked documentation | Separate module composition, evaluation metrics and model optimisation | A model-programming framework is different work from a native compiler kernel |
| [ziglang/zig](https://github.com/ziglang/zig/blob/738d2be9d6b6ef3ff3559130c05159ef53336224/doc/langref.html.in) | Language reference sections for types, imports and system interfaces | Define ABI, resource and package semantics before broad capability claims | No Zig executable performance comparison was run |

## Findings and changes

Observed: the selected Edict handler source connects validation, checks, multi-module handling and code generation to typed result objects. Its minimal-schema helper removes descriptions from copied schemas. This review does not establish that every stated type/effect/verification path works at runtime. RF2 adopts a different compact boundary: an explicit output option removes a redundant successful summary while preserving all discovery schemas, structured results and errors.

Observed: the selected BAML test encodes expected behavior for closing subprocess-owned MCP pipes, including repeated close. It is a useful testing pattern; the presence of a test is not proof we executed or passed it. RF2's own subprocess cleanup and independent SDK checks are separate executed evidence.

Derived design direction: RF2 should retain readable source, explicit local modules, nominal type checks and a separate bounded agent interface. A terse program is useful only if the complete setup, result and correction cost is measured. New record declarations and borrowed typed parameters are now executed in RF2; broader strings, enums, arrays, ownership and diagnostics remain further work.

Unknown: relative full-application speed, security, compiler maturity and AI code-generation success across these projects. Their features and test counts are not interchangeable benchmark units. RF2 does not yet claim Java/C++ ecosystem parity, general AI inference, x86 output or every Python library.

## Benchmarks kept separate

RF2 0.9 versus 0.10 is an executed version comparison. Three scalar kernels additionally compare matched checksums with Clang -O2 and a Python reference. Those small deterministic kernels do not measure the third-party agent languages above. The optional compact MCP session measures complete encoded exchanges; it does not measure model quality or billed tokens. See LANGUAGE-MEASUREMENTS.md for raw timing interpretation and retained limits.
