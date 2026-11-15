# RF2 platform research: one authoring model, explicit execution contracts

Research brief, 15 November2026. Baseline38fdd87be5dfb3e564afb468500afc70e29be966. This is a proposal and review of supplied notes, not a new compiler release, protocol standard, operating system or measured AI productivity result.

## Correct the research starting point

The supplied comparative-engine notes are architectural leads, not verified full engine investigations. Their scorecard incorrectly calls RF2 native generation unimplemented. RF2 already has direct ARM64 native output, bounded Core IR execution, a limited WebAssembly route and a separately qualified ESP32-C3 subset. Supported lesson examples have checked/native agreement tests. Those facts do not establish one portable systems IR, a general VM or every platform.

The notes' claims of a2026 top-ten ranking lack inspectable survey figures in the supplied text; treat that selection as provisional rather than a verified current ranking. Some embedded image captions are unrelated to the engine claims. Generic GitHub+1 labels are not claim-level references. Do not copy these into academic evidence. The proposed brace/var/i64 syntax is not current RF2. Recommendations to start an LLVM backend or reference interpreter must be assessed against the existing implementation, not silently adopted as a restart.

Primary references inspected for this brief:

- MCP tools specification, pinned2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/server/tools . It provides tool discovery, input/output schemas and tool calls. It does not define RF2 program semantics, database transactions or a general compiler safety proof.
- Rust compiler overview: https://rustc-dev-guide.rust-lang.org/overview.html . Useful primary architecture reference; no whole-engine runtime/reverse-engineering coverage is claimed here.
- LLVM code generator documentation: https://llvm.org/docs/CodeGenerator.html . Useful primary backend reference, not evidence that RF2 should replace its emitter.

## The actual ambition

Reduce the number of unrelated concepts a human or AI must reconstruct to deliver a useful application. Keep a coherent RF2 source/semantic model while implementing platform-specific execution honestly. Do not make one giant application-template recognizer or disguise incompatible contracts behind identical syntax.

A single language can express many domains if its type system, libraries, runtime and targets support them. It cannot remove physical memory limits, timing constraints, device differences, signing requirements or the need to specify program behavior. Languages, compilers, application frameworks, tool transports and operating systems solve related but different problems.

## Five cooperating layers

1. **Language contract:** values, numeric semantics, types, ownership, errors and effects. Current nested-owned-value and collection gaps remain prerequisites.
2. **Reusable application capabilities:** typed storage, forms, tables, queries, validation and recovery shared across interfaces. UI design tokens/components belong here, not in machine instruction selection.
3. **RF2 Contracts, working research name:** a proposed versioned execution description connecting an operation, exact implementation, input schema, requested effects, resource budget and failure policy. It must be meaningful to the runtime, not only explanatory text for a model.
4. **Adapters and tools:** CLI, Studio and MCP invoke the same admitted capability. Retain MCP interoperability initially. Build a new transport only after measuring a concrete problem existing adapters cannot address.
5. **Targets and system software:** backends and platform runtimes initially use existing OS services. An RF2 operating system would separately need boot, memory management, isolation, scheduling, drivers, storage, networking, updates and recovery. Compiling applications is not an OS replacement.

This is an architectural direction; only the current fixed capabilities and contracts documented elsewhere are implemented. The proposed general contract layer is not an installed MCP tool.

## What a proposed contract must contain

A capability name and version are insufficient. Bind the implementation/revision, exact type/schema version, input identity, principal/session, permitted effects, resource bounds and failure behavior. A cached prepared artifact must be invalidated when any semantic dependency changes. An implementation digest identifies bytes but does not prove they are correct.

The host proposes a request. A deterministic admission step checks the actual permissions and target. Pure operations can execute with supplied data. Stateful operations need concurrency and transaction rules, an idempotency policy and explicit confirmed/failed/uncertain outcomes. A preview must not be assumed still valid at commit time: bind it to the relevant state revision or revalidate atomically.

A receipt records observed outcome and artifact identities. It is not automatically a proof, signature or external attestation. Deterministic computation may be replayed; replaying an external effect must not duplicate it. Retries after uncertain saves require state reconciliation, not optimistic success text. Existing evidence-contract and Booking mechanisms provide examples within narrower domains, not a general implementation of this proposal.

## Five falsifiable research hypotheses

| ID | Hypothesis | Minimum experiment | Failure criterion |
| --- | --- | --- | --- |
| P1 | Versioned capability reuse reduces complete AI development work | Same frozen app requirements, available libraries and acceptance suite; clean baseline/candidate attempts; count all usage and repairs | Savings disappear when setup/tool schemas/tests and failed attempts are included |
| P2 | One semantic implementation reduces interface drift | Exercise the same validation/storage cases through CLI, GUI and bounded adapter | Any interface admits behavior another should refuse, or diverges after restart |
| P3 | State-bound preparation makes mutations easier to recover | Competing writers, stale previews, lost responses and retry after uncertain commit | Duplicate effects, unauthorized writes or false success |
| P4 | A reusable UI kit reduces repeated layout/accessibility work | Same app with three layouts/themes, keyboard/narrow-screen/long-text/error-state tests | Components require duplicating business logic, or usability fails despite shorter source |
| P5 | RF2-written system components improve one specified failure mode | Select a concrete isolation/recovery defect, reproduce in a controlled fixture, implement candidate and compare fault outcomes/costs | Failure still occurs, required behavior is omitted, or unmeasured protection is claimed |

These mechanisms have precedents: type/effect systems, capability interfaces, transactions, incremental compilation, prepared plans and replay. Their integration can be valuable without a world-first claim. Establish novelty only through a scoped literature/implementation comparison.

## The90-percent token hypothesis

Define usage saving S =1 - T_RF2/T_baseline for matched successful outcomes. T includes actual provider-reported input/output usage across discovery, planning, source generation, tool results, tests, repair and delivery. Report cold setup separately from warm reuse, cache-hit/miss paths and failures. Do not compare a prebuilt RF2 app with a comparator required to invent all its libraries. Report pass rate and effort of failed attempts alongside successful-attempt usage; lower tokens achieved by omitting features is not a saving.

A90-percent reduction is a target, not current evidence. Existing docs/REUSE-MEASUREMENTS.md actually records higher encoded lifecycle counts for prepared reuse at one and20 calls, with a benefit at100 calls. Those are tokenized fixtures, not billed AI development usage. This is evidence that schema/setup overhead and reuse frequency matter, not proof that the target is impossible or achieved.

Fewer model tokens, shorter compilation, lower runtime latency and lower energy are separate outcomes. A compact plan can still execute slowly. A fast executable can still take a long model conversation to construct. Measure each independently with target/version and repeated trials.

## First concrete experiment

Use a small multi-room booking application as the shared task, not another sum benchmark. Freeze room/customer/reservation fields, overlap rules, input validation, restart behavior, concurrent submissions, failed saves, accessible UI and distribution requirements. Current one-room Booking is a starting artifact, not completion of the new task.

Compare a reviewed conventional stack with an RF2 capability route using equivalent pre-existing functionality. Phase1 establishes the RF2 typed data/collection and storage prerequisites. Phase2 implements shared CLI/GUI behavior. Phase3 adds one bounded adapter with explicit permissions; no arbitrary systems source is admitted as Core. Phase4 runs matched clean AI development trials under a declared resource budget, storing actual usage. API inference spend and external workloads require separate concrete execution authorization; none ran for this brief.

Keep the current compiler/transport working throughout. No speculative OS rewrite is a prerequisite for proving this first application-level benefit.

## OS research track

For a fourth platform, select one actual machine/emulator and one boot/recovery/security acceptance suite. Identify a specific failure instead of calling Linux generally broken. Pin hardware assumptions and competing systems versions. Distinguish host-model evidence, emulator evidence and physical execution. RF2 can be the implementation language for a future kernel/runtime; it is not itself the driver stack. Work on existing hosts can bootstrap the new platform without becoming its permanent architecture.

SFE can maintain an official upstream, signed release policy, compatibility contract and transparent review process. Governance and release stewardship should not be confused with technical exclusivity or preventing every independent implementation.

## Current status

This brief corrects the supplied status claims and specifies hypotheses. No new protocol implementation, model-usage trial, Linux replacement, hardware redesign, energy saving or90-percent token result is claimed. Next authorized engineering work should strengthen typed values/collections and shared capabilities, followed by the frozen application experiment. New results belong in version-bound receipts and the learning edition only after execution.
