# Choose an RF2 example

Start with [RF2 From Zero](../book/learning-edition-1/README.md), [package selection](../docs/START-HERE.md#choose-a-package) and the [first native app](../docs/FIRST-APP.md). Select an example by **execution profile and target**, not just its filename. Existing `.flow` and `.rf2` source paths are retained for compatibility.

## Learn, then build

| You want to | Entry point | What to expect |
| --- | --- | --- |
| Learn decisions, functions and loops | [Eight complete lessons](../book/learning-edition-1/examples/) | Bounded Core programs; use the lesson's check/run/native-build route |
| See bits, hex, ASCII and logic | [Number Lab CLI](number-lab/), [browser lab](number-lab-web/) | Native Mac examples; the browser renders HTML/CSS |
| Edit and execute Core lessons | [Studio walkthrough](../docs/BOOKING-STUDIO.md) | Workbench 0.38; not a general Systems IDE |
| Parse, sort and summarize numeric input | [Collection tools](collection-tools/README.md) | Trusted Mac programs sharing bounded heap collection/parser libraries |
| Find duplicate numeric values | [Sorted lookup](collection-tools/LOOKUP.md) | Source addition qualified in sprint 0.40; borrowed lower/upper-bound lookup |
| Read and search text documents | [Documents workspace](documents/README.md), [shared APIs](documents/LIBRARIES.md) | Explicit UTF-8 corpus, read-only originals; no PDF extraction or persistent index |
| Build a booking application | [Booking CLI and GUI](../docs/BOOKING-STUDIO.md) | One room, bounded journal and explicit uncertain-save behavior |
| Search lines from a CLI | [Text search](text-search/) | Shares text/collection modules with Documents |

## Explore systems and devices

| Area | Source or guide | Boundary |
| --- | --- | --- |
| File bytes and Unicode | [Hex](hex/), [Unicode lines](unicode-lines/), [buffer audit](buffer-audit/) | Trusted Mac source; inspect ownership and error contracts before use |
| File checksums | [Checksum source](file-checksum.rf2), [comparison method](../docs/BENCHMARKS-0.21.md) | Real supplied files; SHA identity is not independent correctness approval |
| Function edits and rebuilds | [Function changes](function-changes/), [incremental builds](../docs/INCREMENTAL-BUILDS.md) | Explicit build caches; no automatic authority through MCP |
| Embedded firmware | [ESP32-C3 guide](esp32c3/README.md) | Separate bounded RV32 compiler; emulator evidence, physical validation pending |
| Virtual machines | [Hypervisor foundation](hypervisor/), [VM runner](vm-runner/) | Apple Hypervisor development contracts; not proof of a Linux-booting RF2 OS |
| Browser/edge research | [Browser lab](browser-lab/), [Worker example](cloudflare-worker/) | Narrow supported experiments; not a general browser or cloud SDK |
| Bounded authenticated operations | [Evidence contract](evidence-contract/), [trust contract](../docs/TRUST-0.18.md) | Separate development server; not extra authority for the stable nine MCP tools |
| Nested application records | [Isolated experiment](../experiments/nested-records/README.md) | Candidate borrowed composition; not released general nested ownership |

## One safe build route for Mac Systems examples

From the source checkout, select the qualified compiler bundle explicitly:

```sh
export RF2_HOME="/absolute/path/to/RF2-0.36-dev-macos-arm64"
sh tools/dev.sh doctor
sh tools/dev.sh check examples/collection-tools/lookup.flow
sh tools/dev.sh build examples/collection-tools/lookup.flow output/first-lookup --opt
printf '9,1,9,3,2' | ./output/first-lookup/program 9
# {"first":3,"after":5,"matches":2}
```

Use a new output directory. Build/check never run the program; the last line executes it explicitly. The 0.36 compiler supports this lookup library. The optional nested-record experiment requires its own candidate compiler and must not be substituted silently. Core, Mac Systems and ESP32-C3 programs have different contracts; the [learning edition](../book/learning-edition-1/README.md) explains their distinct commands.

## Add a useful example

Provide the target, required tool version, input, expected output, refusal/failure cases, reusable modules and a reproducible verification route. Keep tests and benchmark controls in [tests](../tests/README.md) and [tools](../tools/README.md), with links from the guide. Fixtures demonstrate programming behavior; they do not establish workplace or physical-device results. A listed directory is a starting point, not a promise of unrestricted platform support.
