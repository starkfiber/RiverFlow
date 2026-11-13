# A developer experience worth choosing

The next milestones are acceptance contracts. They are not a claim that RF2 replaces established platforms today. Preserve the implemented behaviour and failing cases before increasing scope.

| Milestone | A developer can do | Required proof |
| --- | --- | --- |
| Check before creating artifacts | Run `rf2c --check SOURCE`; receive an honest nearby error or successful validation | Full validation, unchanged-workspace manifests, nonexecution canary and refusal cases |
| Reuse a native library | Call bounded byte search with caller-owned workspace | Independent output oracle, typed-call checks, boundary/guard-page cases, simple complete CLI |
| Store useful structured data | Construct larger local arrays without spending one scalar slot per element | Implemented within explicit 0.32 bounds; see [storage and frame qualification](STRUCTURED-STORAGE-0.32.md). General allocation and ownership transfer remain further work |
| Build readable application logic | Use standard text/collection/JSON/error interfaces rather than repeating pointer and formatting code | Several applications sharing the same implementations; module/version contracts and meaningful error paths |
| Deliver an application | Install and operate a package on an explicitly supported platform | Fresh-target build/sign/install/use/cleanup receipts; no hidden developer-runtime requirement |
| Give an AI dependable tools | Discover and compose bounded capabilities with inspectable failures | Stable schemas, exact permissions, refusal/state tests and actual recorded complete tasks |
| Demonstrate an adoption advantage | Complete matched application tasks with less effort or cost | Predeclared comparator/task/oracles, repeated attempts, actual usage receipts, defects and human intervention retained |

The first two have scoped development evidence in the 0.31 reports, and the fixed-array storage row has 0.32 qualification. The remaining rows still require implementation or qualification. A checked source program can fail when run. A small CLI does not supply a framework, database, GUI toolkit, security certification or cross-platform ecosystem.

## Keep the stack understandable

Begin with a task, inputs, outputs, limits and expected failures. Keep native machine-level control in the compiler and reviewed libraries, so routine application authors do not have to repeat it. Preserve explicit access to systems operations for qualified low-level work. High-level convenience and low-level control need clear contracts; they do not require every application to manipulate raw pointers.

Build profile-specific examples around real jobs. A learner needs visible feedback and a short walkthrough. A developer needs libraries, useful diagnostics and predictable tooling. An AI tool author needs schemas and testable authority. A business owner needs working features, support costs and recovery. These are distinct acceptance journeys, not a claim that one demonstration serves everyone.

## What further optimization must preserve

Compare outputs and failure behaviour first. Measure complete tasks separately from kernel loops, compiler rebuilds and startup. Include optimized libraries as comparators, retained fallbacks, periodic/adversarial inputs and regressions. Account for added selection/checking cost. Record source, compiler, binary and workload identities. Keep losing cases; do not train the headline on a favourable workload alone.

## Development 0.33 checkpoint

Owned u64 heap growth, local moves, typed mutable borrows and two shared-library `.flow` applications are [implemented and qualified within explicit bounds](HEAP-COLLECTIONS-0.33.md). Cleanup failures, pending retirement and partial release remain part of the public contract. Next allocation work: structured element types, maps and ownership transfer across function boundaries with independent failure tests. An [ESP32-C3 target](EMBEDDED-DIRECTION.md) is proposed and unimplemented. Neither host collections nor a new filename extension supply firmware support.
