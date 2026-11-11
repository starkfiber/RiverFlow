---
name: rf2
description: Write, check and run RiverFlow RF² Core programs and develop its language specification, compiler and evidence. Use for .flow programs and RF² work.
---
# RiverFlow RF²

Read the repository docs/SPEC.md for syntax and current semantics. The supported profile is RF2_U32_CORE_V0, distinct from the historical BOUNDED_U32_V2 prototype. Never silently accept another dialect.

Use rf2_status to inspect capabilities, rf2_check to check source and rf2_run for bounded arithmetic. If MCP is unavailable, use `node bin/rf2.mjs check file.flow` or `node bin/rf2.mjs run file.flow '[1,2,3]'` from the repository. CLI accepts an explicit local source file; MCP takes source text and never reads paths.

Translate intent into explicit typed source. Unsupported requests need a proposed versioned extension and tests, not an invented working operation. No networking, filesystem, raw instructions or device effects exist in Core 0.1. Model intelligence belongs to the host; a valid program does not confer OS privileges.

Keep checked and wrapping arithmetic explicit. Test known outputs, overflow, invalid input and termination limits. Describe measured speed only with matched evidence. Existing thesis names are research directions, not proof of integrated runtime functionality. Keep private engineering data and participant records outside public releases.
