# RF² RiverFlow

### Readable source. Native programs. Bounded AI tools.

Created by **Ilangkhumanan Thirunavokkarasu** · Published by **SFE** · **MIT licence**

[Download](https://github.com/starkfiber/RiverFlow/releases/latest) · [Start here](docs/START-HERE.md) · [Codebase map](docs/CODEBASE.md) · [Read the book](https://starkfiber.github.io/RiverFlow/book/) · [MCP](plugin/skills/rf2/SKILL.md)

![RiverFlow](site/assets/riverflow-hero.png)

RiverFlow is a programming language with a compiler written in RiverFlow. It emits ARM64 machine code directly for Apple Silicon macOS. Native programs run without a Node, npm, Python or C++ runtime. An AI host can use the bounded MCP interface to check and run supported computations.

The goal is one readable language for application and systems work, with explicit effects and recoverable failures. The current implementation is a foundation for that goal. Its [capability map](docs/CAPABILITY-MAP.md) states what works and what remains missing.

## Start in five minutes

Download and unpack the latest Apple Silicon Mac release, then run these commands from its directory:

```sh
./rf2 status
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
./rf2 mcp
```

The sum returns `6`. The last command starts the native MCP service over standard input and output. Follow [the host setup guide](docs/START-HERE.md#connect-an-ai-host) to connect it to an AI application.

To compile your own trusted systems program:

```rf2
profile RF2_SYSTEM_A64_V1
fn main(argc,argv)
 let answer=20+22
 return answer!=42
end
```

Save it as `program.rf2`. From a source checkout with a qualified native compiler:

```sh
./tools/build-program.sh /absolute/path/to/rf2c program.rf2 program-build --opt
./program-build/program
```

The program exits successfully. The build creates a new directory and signs the executable for local macOS execution. It never silently installs a toolchain.

## Choose your path

| You want to… | Start here |
| --- | --- |
| Learn the syntax | [Language and byte guide](docs/START-HERE.md#learn-the-language), [book](https://starkfiber.github.io/RiverFlow/book/) |
| Write a native file or text tool | [Examples](examples/), [ownership](docs/RESOURCE-OWNERSHIP.md), [text and bytes](docs/TEXT-BYTES.md) |
| Connect an AI assistant | [Native MCP setup](docs/START-HERE.md#connect-an-ai-host), [tool contracts](plugin/skills/rf2/SKILL.md) |
| Inspect smaller native images and function changes | [Compact images and working sample](docs/COMPACT-IMAGES-0.27.md) |
| Reuse unchanged native builds | [Incremental target builds](docs/INCREMENTAL-BUILDS.md) |
| Work on the compiler | [Compiler map](native/compiler/README.md), [contribution guide](CONTRIBUTING.md) |
| Test a performance claim | [Measurement guide](tools/README.md), [latest compiler experiment](docs/COMPILER-DISPATCH.md) |
| Understand platform and library gaps | [Capability map](docs/CAPABILITY-MAP.md), [full-stack direction](docs/RF2-FULL-STACK-DIRECTION.md) |

## What is available

**Stable package: 0.17.** Bounded Core computation, local modules, records, checked arrays, UTF-8 scalar views, typed outcomes, owned files, bounded growing bytes and nine defined MCP tools.

**Development source: 0.31 foundation candidate.** A separate [native development bundle](dist/0.31-candidate/README.md) is available for the tested Apple Silicon Mac target. Check a native program before creating an executable, locate mistakes with bounded source diagnostics, and build a [useful byte-search tool from a reusable RF2 library](examples/text-search/README.md). See the [implemented changes, measurements and remaining limits](docs/FOUNDATION-0.31.md). Native builds also support compact images and explicit target/function reuse. Development source is separate from the stable download. The [engineering history](docs/RESEARCH-HISTORY.md) retains earlier experiments; the [developer roadmap](docs/DEVELOPER-ROADMAP.md) states what must work next.

MCP does not grant arbitrary filesystem, network or systems-code execution. AI intelligence comes from the connected host. There is no embedded model or automatic proof of correctness.

## Inside the repository

| Directory | Purpose |
| --- | --- |
| [`native/`](native/) | RF2 compiler, runtime and native application code |
| [`examples/`](examples/) | Complete programs and capability demonstrations |
| [`tests/`](tests/README.md) | Native acceptance tests, independent oracles and regressions |
| [`plugin/`](plugin/) | Native MCP launchers and host skill |
| [`tools/`](tools/README.md) | Explicit build, measurement and publishing tools |
| [`docs/`](docs/CODEBASE.md) | Contracts, current guides and retained evidence |
| [`bootstrap/`](bootstrap/), [`src/`](src/) | Historical seed and JavaScript reference implementation |
| [`site/`](site/), [`book/`](book/) | Website and book sources |

Existing paths stay compatible. Developer test and publishing tools use other languages; those are distinct from native user runtime dependencies. [Full map and build flow](docs/CODEBASE.md) · [Source inventory](docs/SOURCE-INVENTORY.json).

## Make an improvement we can verify

Bring a complete program, an expected result and a reproducible failure. Keep a baseline, test refusal paths and report mixed results. Some RF2 optimizations remove repeated work; others still trail specialised C or general-purpose libraries. There is no universal speed or model-token claim.

Read [CONTRIBUTING.md](CONTRIBUTING.md), then choose a bounded task from the [roadmap](docs/RF2-FULL-STACK-DIRECTION.md). New targets, concurrency, richer allocation and library compatibility need real implementations and target-specific tests.

[MIT licence](LICENSE) · [Release history and experiments](docs/RESEARCH-HISTORY.md) · [External review brief](docs/EXTERNAL-REVIEW-BRIEF.md)

## Try a native learning app

[Number Lab](examples/number-lab-web/) makes binary switches, hex, ASCII and logic gates interactive. Its server and calculations compile from RF2; the browser renders ordinary HTML/CSS. See the separate [CLI game](examples/number-lab/) and [measured development results](docs/FUNCTION-REUSE-0.29.md).

![Number Lab running from native RF2](docs/assets/number-lab-0.29.jpg)
