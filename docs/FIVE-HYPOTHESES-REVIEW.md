# Five RF2 evidence-contract hypotheses: independent review

Reviewed 12 November 2026 against baseline `b6fae621368f16e4d23cb37975b6b122bb961e39` (0.17). This document is a prior-art and experiment-design review. It does not report new implementation results or certify the compiler.

The useful research direction is an RF2 workflow in which a compact operation contract declares authority and work limits, a candidate computation is checked against a reference, state changes are published only after agreement, and evidence can be independently replayed. These are five testable integration hypotheses. They are not five newly discovered laws of computation. There is no evidence here that existing language designers missed a fundamental Boolean gate, transistor operation or universal optimization.

## Existing foundation and boundaries

[Storage and results](STORAGE-RESULTS.md) describes bounded growable byte vectors with fixed virtual reservations, scalar error results, and success records of one to four scalar fields. Owners remain local: they cannot be copied, passed, returned or converted to raw pointers. The recorded release checks are finite software tests, including injected syscall failures. They are not physical memory-pressure measurements or a whole-language memory-safety proof.

[Native Core](NATIVE-CORE.md) provides a separately bounded, read-only computation profile. Its work limit counts abstract operations, not elapsed time, joules or instructions retired. The trusted systems compiler permits capabilities outside that Core profile. A new contract runner therefore has to enforce its own closed operation vocabulary; a declaration cannot confer safety on arbitrary raw systems code.

The following hypotheses apply to the proposed runner and its explicitly admitted operations. MCP must expose only the corresponding validated schema and effects. Merely calling unrestricted RF2 code from MCP would not establish these properties.

## H1: An executable authority and work contract

**Hypothesis.** For a finite set of byte or word transformations, RF2 can reject disallowed operations and over-budget plans before publishing state, while retaining a short, readable contract.

**Prior art.** Effect types already express computational effects. The [Koka book](https://koka-lang.github.io/koka/doc/book.html) explains effect typing and handlers. This does not make an RF2 contract a novel effect system. RF2's contribution would be the integration of an enforced operation plan with native execution and an evidence record.

**Acceptance tests.** Enumerate every admitted operation and authority bit. Reject unknown operations, unknown or insufficient authority, malformed operands, excessive plan size, arithmetic overflow in cost calculation, and boundary-plus-one budgets. A refusal must preserve the original state. Test exact-boundary successes separately. If an operation is executed in a backend, account for it in preflight; no hidden unrestricted callback is permitted.

**Falsifier.** A plan exceeding an enforced limit executes, an undeclared effect occurs, or cost arithmetic wraps into an accepted budget.

**Limit.** This is closed-vocabulary enforcement, not inferred effects for all RF2 programs, CPU-time control or an operating-system sandbox. Readability and token reduction require a separate human/task study or measured tokenizer corpus.

## H2: Publish all state or preserve all state

**Hypothesis.** Within the runner's in-memory state, staging and validation allow an ordinary recoverable failure to leave externally visible bytes, length and metadata unchanged.

**Prior art.** Transactions long predate RF2. [SQLite's atomic commit documentation](https://www.sqlite.org/atomiccommit.html) explains all-or-nothing changes, its hardware assumptions and crash testing. An RF2 scratch buffer followed by publication is a much narrower property than SQLite's durable database transactions.

**Acceptance tests.** Capture full input state, including metadata. Trigger a failure at the first, middle and last operation of multi-step plans, and after a valid prefix. Compare full state byte for byte after refusal, rather than comparing only a fingerprint. Test empty and maximum-sized states, alias attempts, arithmetic errors, invalid indexes and insufficient capacity. Successful publication must match an independent expected full state.

**Falsifier.** Any ordinary refusal exposes a partial mutation or changes metadata while leaving old bytes apparently intact.

**Limit.** Do not claim power-loss durability, filesystem transactions, concurrent-reader linearizability or rollback of network and other external effects without their own implementation and fault tests. The runner must state exactly when its commit point occurs.

## H3: Independent execution before publication

**Hypothesis.** A reference computation and a separately written candidate computation can detect injected defects in the candidate before its output is published.

**Prior art.** [Alive2](https://github.com/AliveToolkit/alive2) provides LLVM translation-validation tools and explicit unsupported transformation boundaries. [Proof-Carrying Code](https://homes.cs.washington.edu/~mernst/teaching/6.893/readings/necula-popl97.pdf) uses a machine-checkable proof of a safety policy. Agreement between two executions is neither an SMT equivalence proof nor proof-carrying code.

**Acceptance tests.** Compare complete result state, status and relevant metadata. Use independent algorithms or code paths, not two calls to the same transformation. Inject wrong arithmetic, wrong index, omitted step, wrong error status and corrupted output. Each scoped mutation must be detected, and mismatch must refuse publication. Retain a test where an unchanged fingerprint would conceal different full state if the test harness can construct it.

**Falsifier.** A knowingly divergent candidate publishes output, or comparison omits an observable field that differs.

**Limit.** Shared parsing, specifications and compiler components can share bugs. Agreement on one input does not establish universal equivalence. Running both computations may cost more than one computation; report that overhead rather than promise speed.

## H4: Evidence tied to the exact computation

**Hypothesis.** A canonical, versioned SHA-256 receipt can detect changes to the plan, input, result or identified implementation when a verifier independently reconstructs the receipt.

**Prior art.** [Reproducible Builds](https://reproducible-builds.org/docs/definition/) defines artifact reproducibility in terms of specified inputs, environment and bit-identical results. [SLSA build provenance](https://slsa.dev/spec/v1.2/build-provenance) records how artifacts were produced and identifies a trusted builder. These are established provenance approaches, not RF2 inventions.

**Acceptance tests.** Specify byte encoding, integer widths, endianness, field order, length prefixes and domain separation. Bind semantic/schema version, plan, input, output, result status and actual runner identity. Change each field independently, including embedded zero bytes and ambiguous field boundaries; verification must refuse. Compare the native hash against an independent trusted implementation and standard SHA-256 vectors. Recompute output independently: a self-consistent invented result and digest is insufficient.

**Falsifier.** An evidence record verifies after a bound field changes, or two distinct allowed encodings are accepted for one canonical identity.

**Limit.** A digest provides identity and tamper detection relative to a trusted expected digest. An unsigned local receipt does not authenticate its author, prove correct execution, attest hardware or provide a cryptographic signature. FNV-1a from the 0.17 buffer example is not a substitute for SHA-256.

## H5: Reproduce the failure and expire stale evidence

**Hypothesis.** A bounded failure capsule can reproduce a runner discrepancy in a fresh process, and changed semantics or inputs cannot silently reuse its old successful evidence.

**Prior art.** [rr](https://rr-project.org/) records and deterministically replays real application executions. RF2's proposed plan/input capsule is narrower: replay of a deterministic admitted computation, rather than a general recording of operating-system scheduling and effects.

**Acceptance tests.** Store exact input, operation plan, semantic and implementation identity, reference/candidate results and failure category. Replay an injected mismatch in a fresh process. Reject tampered capsules, unsupported versions, changed inputs and changed implementation identities. If minimization is provided, verify that each reduced capsule retains the same original failure predicate; do not label an unrelated refusal as a minimized mismatch. Keep a permanent regression case after the defect is repaired and require the repaired result to agree with the reference.

**Falsifier.** A capsule reports a different outcome on the same supported identity, or stale evidence remains accepted after a bound dependency changes.

**Limit.** A deterministic replay does not independently confirm that the reference specification is correct. It does not capture arbitrary files, network behavior, concurrency or device state unless those are explicitly part of the contract.

## Experiment and publication requirements

Pin the baseline, runner/compiler sources, exact host target, test commands and generated artifact hashes. Use reviewed fixed cases plus fresh seeded cases; preserve seeds and failures. Keep a simple 0.17 implementation as a behavioral control where the feature is expressible. Record negative controls by deliberate defect injection. Report tested cases and refusal categories, not a percentage implying universal safety.

For usefulness, use one real bounded application, such as a local document transformation, that benefits from refusal without partial state and a replayable explanation. Measure successful and failing jobs, including verification overhead. Performance comparisons require equal semantics, outputs and failure behavior, warm-up policy, repeated timings and distribution summaries. Actual provider token usage, a named tokenizer count and source character count are different measurements and must be labelled separately. No speed or token gain follows automatically from this design.

The stronger contribution is a coherent developer experience: explain the intended action, enforce its limited authority, compare independent executions, publish a complete result and preserve enough evidence to challenge it later. Whether that integration is easier or more reliable than existing tools remains a falsifiable research question. This review provides no basis for claims of global novelty, top language ranking, complete security, a new transistor mechanism or proven superiority over general-purpose languages.
