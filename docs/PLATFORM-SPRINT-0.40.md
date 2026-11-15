# Application foundations and scenario coverage: sprint0.40

Source-development sprint, not a replacement for stable0.17 or Workbench0.38 downloads. Author Ilangkhumanan Thirunavokkarasu, publisher SFE. Baseline38fdd87be5dfb3e564afb468500afc70e29be966. [Qualification summary](PLATFORM-SPRINT-0.40.json).

## What changed

A reusable sorted lookup module now operates over the existing borrowed Numbers heap collection and fills a typed NumberRange. The new [lookup CLI](../examples/collection-tools/LOOKUP.md) shares parsing, sorting and output libraries with the numeric applications. It sorts input and finds exact duplicate ranges, including empty input and absent values. This adds practical lookup without inventing generic containers or changing collection ownership semantics.

The isolated borrowed-record candidate now supports nested scalar leaf updates, preserving the target address across a call-valued right-hand side. Generated tests cover1–6 nested layers, aliased and distinct children, observed leaf values and exactly-once RHS evaluation. Whole-child rebinding, missing fields, scalar traversal, wrong constructor types, borrowed-record result escape and owned-collection fields refuse.

The preparation controller now pins the canonical compiler source digest, checks the assignment patch location and exclusively creates the generated source. Older artifacts are retained. This candidate is deliberately separate from native/compiler/compiler.rf2 and shipped binaries. It is borrowed composition, not inline nested values or nested owner transfer.

## Executed evidence

| Check | Actual scope/result |
| --- | --- |
| New native controller |3,048 passing assertions, including2,000 collection lookup workloads,512 compile checks and512 executions of256 nested source variants, malformed inputs and explicit type refusals |
| Independent expected results | Python bisect over independently sorted integers; known alias/leaf/call-counter expectations in generated native programs |
| Existing collection apps |308 passing controls with candidate compiler, including growth, parsing, limits, closed descriptors and shared modules |
| Heap ownership |78 passing prior adversarial/failure controls with candidate compiler |
| Compiler self-generation | Two unsigned candidate generations match; not diverse bootstrap validation |
| MCP | Existing nine tools; systems input refused and following checked sum returned6 |
| WhatIF suite |60 read-only GET requests across baseline/parallel/post-parallel stages, all smoke stages passed; fresh integrity verification succeeded |

New numeric/search workloads run in normal and optimized modes on one Apple Silicon Mac. The variants are finite generated programs, mostly variations of the same composition pattern. They are not thousands of independent algorithms, programmers or user studies. Test and fixture generation use development Python; native lookup execution does not.

WhatIF's standard runner does not execute RF2 compiler semantics. The native controller executes those cases using WhatIF's baseline/change/invariant discipline. WhatIF's actual tool suite separately probes the already-running Booking page. Its stage named recovery is a repeat after parallel requests, not injected-failure recovery. No external traffic, hardware, physical device or shared compute was used.

## Concrete role/target exploration

[72 scenario briefs](RF2-USAGE-SCENARIOS.json) cover12 roles and6 adverse/nominal conditions. Each names the goal, hardware, protocol, invariant and missing prerequisite. They are planning records, all marked planned-not-executed. No general test result automatically closes a role journey. The generator is tools/research-scenarios.py.

The current discovery gaps include Linux services/TLS/SQL, Windows native widgets, Android packaging, physical ESP32 sensors, concurrent task semantics, owned nested values and a reusable high-quality UI toolkit. Generating a persona or accepting a filename does not implement those backends.

## Reproduce

Use a fresh output directory; retain old evidence. From the checkout:

```sh
python3 experiments/nested-records/prepare.py NEW-EXPERIMENT
sh tools/build-program.sh /absolute/qualified/rf2c NEW-EXPERIMENT/compiler.flow NEW-COMPILER --opt
RF2_TEST_HOME=/absolute/qualified RF2_NESTED_COMPILER=/absolute/NEW-COMPILER/program python3 tests/standalone/platform_sprint_verify.py
RF2_TEST_COMPILER=/absolute/NEW-COMPILER/program python3 tests/standalone/collection_apps_verify.py
RF2_TEST_COMPILER=/absolute/NEW-COMPILER/program python3 tests/standalone/heap_ownership_redteam_verify.py
python3 tools/research-scenarios.py
```

See existing WhatIF suite receipts locally under .whatif/platform-sprint-040. A new live suite must use a fresh case, reviewed routes and an explicitly authorized target; do not replay the completed directory. No external deployment or inference spend is part of reproduction.

## Remaining gates

- Full compiler/Core/platform regression, independent maintained encoder comparison, cache/reuse-context checks and additional lifetime review before promoting borrowed composition.
- Decide whether the public design needs inline values, explicit borrowed fields or both. Do not accidentally freeze a reference design as value semantics.
- Specify owned nested text/collections, cross-function transfer and partial cleanup before admitting them.
- Build typed multi-room application state and transactional storage with fresh concurrency/failure tests.
- Add shared UI components and run actual keyboard/narrow-screen/long-content/error-state journeys.
- Qualify each backend/protocol separately. No platform-parity, security, speed, energy or model-token-saving claim is made.
