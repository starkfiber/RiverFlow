# RF2 owner vision and engineering contract

Owner clarification,18 November2026. Read this before choosing another local sprint. This governs direction; it is not a statement that the capabilities below already exist.

## Purpose

RF2 is intended to be one coherent programming and creation system: human intent to useful, checked execution across applications, websites, services, firmware, devices, kernels and operating systems. Beginners should start with meaningful actions; specialists should retain precise machine control in the same language/toolchain. AI hosts should reuse established capabilities and project knowledge instead of repeatedly rebuilding the stack.

The owner describes RF2 as Reverse Flow / complete flow: work backward from the desired outcome to the necessary components, contracts and machine execution. Existing RiverFlow repository/product names, `.flow` source and compatibility paths remain unchanged by this note. This clarification is not authorization for a disruptive rename.

The destination includes phones/RU’OS, x86/ARM computers and servers, Raspberry Pi, Arduino/ESP32-class boards, TVs, appliances/fridges, fans, cameras, kiosks/coin-operated devices and other explicitly supported hardware. A report SDK or a single benchmark is a component, never the definition of RF2.

## Meaning and intent

The owner's Tamil analogy is semantic economy: shared concepts and context let a short expression convey a substantial goal. RF2 should carry reusable meaning through recipes, APIs, specifications and tests. Byte counts, model token counts, semantic content and execution cost are distinct measurements; shorter wording alone proves none of the others.

Proposed creation path:

intent → explicit acceptance contract → reusable capability plan → typed program/IR → target lowering/adapters → executable/package → verified operation and updates.

This is an architectural objective, not a currently implemented universal intent compiler. The host supplies model intelligence where used. Ambiguity about consequential behavior must be resolved in the contract; it must not silently become an unsafe machine action. Infer sensible reversible defaults and expose them for editing.

## A request must become a complete product journey

For example, “build a taxi service” implies more than a sample screen: customer and driver journeys, onboarding, accessible UI, booking/dispatch, state and persistence, maps/location, identities and permissions, failure/recovery, deployment, observable tests and operations. Real payment/provider/device integration requires the actual adapter and authorization. Missing dependencies are recorded, not replaced with invented completed behavior.

Common plumbing should come from maintained reusable capabilities. The author describes the domain and intent, rather than repeatedly rebuilding routing, storage, error handling, UI, packaging and harnesses. A scoped prototype is labelled as such; a complete product claim needs the complete acceptance journey.

## Benchmark families

1. **Compiler, runtime and machine work:** optimized C and relevant hand-written assembly on the same target. Match algorithms, numeric semantics, I/O and correctness. Include equally specialized C/assembly, startup and steady state, code size, memory, throughput/latency and failed cases. Add independent target runs. C/assembly are primary machine-level comparators, not optional footnotes.
2. **Complete application creation:** established stacks appropriate to the job. Python remains one useful comparator, alongside C/C++, Java, web/mobile stacks and their libraries. Measure specification, discovery, authoring, tests, repair, delivery and real model usage; disclose warm preparation and unmeasured costs. Do not reduce RF2 to a Python contest.
3. **Portability:** execute the same portable behavior through real target contracts and adapters; qualify each backend/ABI/runtime, drivers, lifecycle, I/O, graphics and packaging independently. Compiler host, target, emulator and physical device are separate facts.
4. **Safety and reliability:** named invariants, authority boundaries, invalid inputs, resource exhaustion, concurrency/cancellation, recovery, update/rollback and adversarial controls. Neither the RF2 name nor native execution supplies security by itself.

Historical negative benchmark results remain. No universal fastest, all-hardware, all-app or energy claim follows from a finite study.

## Cross-layer and physical research

Keep algorithm, representation, memory layout, compiler, instruction selection and circuit exploration in scope. The owner explicitly wants research below conventional high-level boundaries, including how physical signal/device choices might support different computing approaches.

Candidate hypotheses need a defined workload, exact/bounded-error semantics, design space, strong existing baseline, equivalent-output checks, simulation assumptions and eventual measurements on appropriate hardware. Track data movement, control, encoding/conversion, wiring, power and failure costs where relevant. Software results do not establish a new transistor or quantum/photonic device. Retain disproved hypotheses as evidence.

TTC's broader intent/meaning direction is an owner research ambition. Its existing local scheduling paper and recorded experiments remain separately attributed; they are not automatically proof of a semantic compiler, new device physics or universal speedup.

## Foundation and product tracks must advance together

- Language/compiler: numerical semantics, values/ownership, collections, errors, concurrency, ABI and verifiable lowering.
- Targets/devices: general x86-64/ARM adapters, embedded support, firmware/drivers, boot/runtime and RU’OS integration.
- Creation system: intent contracts, discoverable capabilities, project memory, reusable SDKs, harness engineering, diagnostics, testing and packaging.
- Product experience: cohesive UI/components, complete workflows, installer/update/rollback and usable authoring tools.
- Evidence: matched C/assembly/runtime and complete-product comparisons, source/input identity, failures and explicit limits.

Do not choose another near-identical scalar report simply because its test harness is convenient. Such apps remain regression/examples. Before a sprint, state which foundation or complete-product gap it closes and how it advances this vision. Preserve useful existing implementations rather than restarting the language.

## Next direction checkpoints

These are planned acceptance gates, not newly completed features or another percentage denominator:

- Define an intent/target contract usable by both application and systems work, with explicit resources, errors and platform assumptions.
- Establish matched native workload evidence against optimized C and hand-written assembly, including size and steady-state costs rather than only process startup.
- Advance one real additional backend/ABI or device integration with executable acceptance tests; do not count a fixed boot image as a general target.
- Demonstrate a complete product workflow through the reusable creation system and retain its portability/deployment gaps.
- Extend recipes only with validated behavior; a short request should invoke real capability, not hide missing implementation.

## Continuity

`PROJECT-CONTINUITY.md`, `PIPELINE.json` and the source RF2 skill must point here. Preserve the fixed historical delivery ledger and independent firewall/platform gates. Keep this project's continuity local; no Kanika Memory/shared retained records. Current owner hold remains: no commits, GitHub writes or live firewall/infrastructure changes without a later instruction changing that scope.
