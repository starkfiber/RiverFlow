# RF2 everywhere: direction and acceptance gates

Maintainer direction, 15 November 2026. The ambition is one readable language and coherent SDK for learning, applications, devices and system software. Success means people choose it for complete jobs. Benchmarking Python, Java, C/C++, assembly and established application stacks remains part of the plan. Leadership is an objective measured by use case, not a badge awarded by this repository.

## What should stay simple

A child starts with inputs, decisions, repetition and visible results. A developer adds reusable types, libraries, tests and deployment. A systems author adds explicit machine, memory and device contracts. An AI host discovers supported tools and composes the same checked capabilities. Advanced control should be available without forcing every beginner to learn instruction encodings first.

One language does not mean every program can run unchanged on every device. Portable application logic needs a supported target and libraries; hardware-specific code needs an explicit adapter. A browser cannot grant firmware access merely because the source has a `.flow` suffix. Compatibility means preserved behavior within a declared contract, including failures.

## Present target matrix

| Destination | Evidence today | Next acceptance gate |
| --- | --- | --- |
| Apple Silicon Mac | Direct ARM64/Mach-O compiler, native CLI apps, local browser UI and nine-tool MCP runtime | Rich owned application values, typed persistence and general project tooling |
| ESP32-C3 | Separate bounded RV32 backend; vendor-emulator boot, UART, sensor-bus controls, timers and interrupts | Physical board/sensor qualification; broaden the embedded contract deliberately |
| Web browser | Bounded Core WebAssembly experiment; existing apps also serve ordinary HTML/CSS from native RF2 | General browser SDK, events, storage and accessible components; browser conformance suite |
| Linux, Windows and x86 desktop | No qualified general RF2 application target | ABI/backend, OS services, executable formats, packaging and independent target tests |
| Android, iOS and smart TV | No RF2 platform SDK qualified | Platform adapter, lifecycle, graphics, input, permissions, packaging/signing and device tests |
| RU’OS | An intended RF2 system-software destination; this repository does not qualify a running RF2 phone | Pin an actual RU’OS engineering revision and boot/runtime ABI; execute one supported component and retain results |
| Games, graphics and design tools | No general game engine, GPU stack or Photoshop-equivalent application | Rendering/input/assets/audio contracts and a complete tested application |
| AI/chatbot SDK | Bounded MCP operations work with host-supplied intelligence | Model/transport adapters, cancellation, usage accounting and a complete application; no embedded intelligence claim |

See the [capability map](CAPABILITY-MAP.md) and [example catalogue](../examples/README.md) for supported profiles. Compiler host, compilation target, execution environment and UI renderer are separate facts. “Native” must name which one it describes.

## Engineering sequence

- [ ] **G1: application values.** Define nested value layout, borrowed versus owned fields, move/return, aliasing, allocation failure and partial cleanup. Keep the [borrowed-record experiment](../experiments/nested-records/README.md) isolated until qualified. Replace one real app's manual packing without losing its data.
- [ ] **G2: numerical contract.** Signed and floating types, conversions and explicit overflow rules with independent edge-case oracles. Add decimal only with defined rounding and persistence semantics.
- [ ] **G3: durable application data.** Typed serialization, versioned schemas, migration, reopen, concurrent updates and recovery after uncertain saves. Preserve old Booking journals or provide an explicit migration.
- [ ] **G4: reusable SDK.** Namespaces, public APIs, versioned packages and repeatable dependency resolution. CLI, GUI and admitted AI tools share business logic.
- [ ] **G5: complete development journey.** Systems-aware Studio, diagnostics, testing and debugging. Accessible reusable UI components; evaluate installation and first successful app with real beginners.
- [ ] **G6: second application platform.** Choose and qualify one additional target, then run the same portable-library contract there. Build target-specific UI/service adapters explicitly.
- [ ] **G7: concurrency and systems.** Define tasks, cancellation, ownership across tasks and synchronization. Qualify a specific RU’OS component separately from desktop applications.
- [ ] **G8: comparative advantage.** Matched complete tasks and runtime workloads with retained competitors, failures, actual usage and installation costs. Publish where RF2 wins and loses.

These are acceptance gates, not eight completed features or a fixed release calendar. Performance work can proceed alongside foundation work when an invariant and independent control are available. A new backend must not silently reinterpret an existing type or permission rule.

## How we will compete

| Question | Required comparison |
| --- | --- |
| Is execution faster? | Same task, algorithm, numerical behavior, I/O and correctness oracle. Separate startup from steady state; rotate trials and keep raw results. Include equally specialized competitors. |
| Does AI build with less effort? | Same frozen feature/acceptance list and equivalent available libraries. Count actual provider usage, discovery, tool descriptions, tests, failures and repairs; separate cold setup from reuse. |
| Is delivery simpler? | Fresh-machine prerequisites, package size, install/build steps, permissions, successful launch and update/rollback behavior. |
| Is it safer? | Named threat model and failure invariants, adversarial inputs, stale state, interrupted operations and refusal tests. Distinguish raw trusted systems code from bounded tools. |
| Can children learn it? | Consented first-time learner tasks, completion and confusion observations. AI walkthroughs are preparation, not learner research. |
| Is it portable? | Same supported program and expected outcomes executed on each named target. Emulator and physical results remain distinct. |

Twofold runtime speed and 90-percent AI-usage savings are testable ambitions, not release guarantees. There is no universal “number one” scalar: correctness, latency, throughput, energy, usability and ecosystem reach require different measurements. Electricity claims need power measurements; a smaller instruction count alone is insufficient.

## Porting an existing application

An RF2 SDK should eventually let an author reuse portable logic and supply platform UI/service adapters. Porting WhatsApp or Gmail would additionally require their actual source or supported APIs, authentication, networking, notifications, storage, media, encryption, lifecycle and distribution integration. AI assistance can help implement a port; it cannot make unavailable APIs or platform services exist. No automatic Java, Python, C++ or mobile-binary compatibility layer is claimed today.

## How the supplied audit changes the plan

Adopt its focus on values, ownership and serialization; retain the existing compiler and `.flow` syntax. Its review is feedback, not independent reproduction of every test. Its broad performance score does not erase scoped measured optimizations, and its caution about feature chasing does not remove competitor benchmarks or the universal-platform ambition. A proposed shared Systems IR needs an incremental experiment with behavior preserved before replacing working emission paths.

The next foundation sprint is **typed application values** with explicit valid, invalid and partial-failure cases, followed by a Booking integration. The next platform decision should name one target and one actual user workflow. [Evolution specification](RF2-EVOLUTION.md) owns language changes; [platform research](RF2-PLATFORM-RESEARCH.md) owns the longer research hypotheses. This page connects them to the maintainer's product direction.
