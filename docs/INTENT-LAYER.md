# RF² direction: compact intent, explicit execution

Author direction clarified 11 November 2026: RiverFlow is intended as a compact human/AI interface for expressing useful work through reusable, versioned capabilities and MCP. The arithmetic Core is an execution foundation, not the final user interface.

## Product contract

People express the outcome, important constraints and acceptance checks. The AI resolves that request to a short inspectable plan. The runtime expands known capability implementations, validates types/effects, executes admitted operations and returns a concise receipt. The AI should not regenerate an entire known implementation for each request.

Human-readable does not mean verbose, and compact does not mean ambiguous. Keep intent words meaningful. Reuse versioned names for established behavior, not unexplained one-letter commands. A novel task still needs design and implementation; a short request cannot supply missing software or permissions.

## Layer boundaries

1. Human request: ordinary language and explicit constraints.
2. Compact intent: capability versions, bound inputs, required effects and acceptance checks.
3. Deterministic expansion: inspectable typed plan/graph and reusable modules.
4. Execution: Core/native code where applicable and explicitly granted service adapters.
5. Receipt: outputs, versions, checks, failures and evidence references.

MCP is a transport and tool interface around these capabilities, not an embedded model or authority to operate arbitrary systems. The current SFE repository bridge only reads catalog/documentation. It is not yet a service execution registry. Unknown operations must be rejected or proposed as new work, not mapped to a superficially successful fallback.

## Syntax exploration, not implemented

A possible future intent document could read:

```text
rf2 intent/1
use attendance.local@1
make "Class register"
keep offline
allow teacher
check one_mark_per_student_day, export_roundtrip
```

This is a proposed design shape. The attendance.local@1 backend is now shipped through attendance_export and an explicit CLI export in 0.6. The proposed intent syntax shown here is not implemented. The original reference profile is RF2_U32_CORE_V0. Native 0.4 now implements RF2_COMPACT_V1 for four reductions; this application-service draft is still unimplemented. Do not feed this draft to the Core checker or claim it creates an application.

A useful first adapter should reuse one real existing application module, define observable success/failure behavior, and prove that the compact plan selects the intended version and checks. It must not use generated UI screenshots or static templates as proof of a working application.

## Token-economy experiment

Treat “hundreds rather than millions” as a research target, not a measured result. Compare ordinary generation and compact-capability composition on the same task and acceptance suite. Predeclare the task, provided starting code, model/version, capability library, context and success criteria.

Record total input/output tokens, schema/document context, tool outputs, clarification and repair rounds, setup costs, latency, monetary accounting where available, functional outcomes and failures. Separate first-use capability creation from repeated use. Record actual model tokenizer/usage receipts; character counts are not token counts. Cached billing and logical context tokens are different quantities.

A short intent only earns a saving if its expanded implementation passes equivalent checks. Include unsupported and ambiguous requests to measure refusal and correction. Do not reduce token totals by omitting required behavior, hiding context or excluding failed attempts.

## Current implementation versus next milestone

Implemented in the reference: checked Core, prepared evaluation, C11 emission, bounded sum optimization, ten MCP tools and public documentation catalog. Native 0.4 separately implements four compact reductions, deterministic Core expansion, direct ARM64 execution and three built-in MCP tools. Its initial 0.4 build used an explicit Python seed. Native compiler 0.5 now reproduces its systems-profile source and the unchanged runtime without Python, within the documented bounded subset. The revised book and executable-level evidence cover that exact subset.

Next milestone: one versioned executable service capability, a compact intent parser/planner, deterministic expansion, concise receipts, negative/permission tests and a matched end-to-end token experiment. Keep existing Core semantics stable. The next book edition should foreground this intent workflow once it works, retaining the first edition as an implementation foundation.

## Inspected historical anchors

The local recovered FLOW_ARCHITECTURE.md describes FLOW plans, service libraries, route mappings and cached plans. Its completion and performance slogans were not independently revalidated in this review. The local CompilerX RUOS_BRIDGE.md separately describes typed intent/effects and bounded validation, with explicit limitations. These references motivate the design; they do not establish that historical integrations or token savings are operational in the public release. Private recovered contents are not redistributed.


## Implemented service checkpoint in 0.6

General Core helpers run in the native runtime and can be lowered/compiled to ARM64. attendance.local@1 uses a generated Core kernel for counts, validates record/date/duplicate rules, and exports CSV. Its MCP interface accepts supplied records and returns data only; filesystem output is an explicit CLI action. No teacher authorization system, classroom UI, unrestricted intent planner, model inference or token-saving result is claimed. See capabilities/attendance.local.v1/ and the native verification reports.
