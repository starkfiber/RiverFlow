# Ten-language source audit and RF2 acceptance roadmap

Reviewed 12 November 2026. Baseline: RF2 0.17, before the experimental five-hypothesis sprint. This is a selected source and specification review, not a claim to have reverse engineered every upstream repository or implemented every language feature. No competitor compiler was built or benchmarked in this audit. The source files were downloaded as text and selected mechanisms inspected; their contents were not executed.

## Which ten, and what the ranking measures

The [TIOBE November 2026 index](https://www.tiobe.com/tiobe-index/) gives the following list. Its ratings indicate search-derived popularity, informed by engineers, courses and vendors. They are not a census of executed programs, code volume, quality or task success.

| Rank | Language | Rating |
| --- | --- | --- |
| 1 | Python | 20.86% |
| 2 | C | 11.48% |
| 3 | Java | 8.89% |
| 4 | C++ | 8.35% |
| 5 | C# | 3.39% |
| 6 | JavaScript | 2.42% |
| 7 | R | 2.27% |
| 8 | SQL | 1.91% |
| 9 | Visual Basic | 1.88% |
| 10 | Go | 1.69% |

Assembly is rank 17 and Rust rank 11 in that index. Assembly is included below as a systems comparison, not inserted into the top ten. Separately, [GitHub Octoverse 2026](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/) places TypeScript, Python and JavaScript first through third by monthly participating accounts. This measures activity attributed through repository primary languages and is a different population and metric. Neither ranking can establish that RF2 will become number one.

## Reproducible inspection scope

Nine implementation repositories cover the ten ranked languages. Exact source revisions are pinned below. The public [source manifest](TOP-TEN-SOURCE-MANIFEST.json) contains all 28 downloaded file paths, byte counts, SHA-256 hashes and commit timestamps. `REVIEW-LOCATORS.json` supplies navigation points, not behavioral test results. These local source snapshots are review inputs, not RF2 implementation code or an upstream distribution.

| Implementation | Pinned revision | Selected source paths |
| --- | --- | --- |
| python/cpython | `9f386367333f7845095d764fad3ad9b397d04672` | [python.gram](https://github.com/python/cpython/blob/9f386367333f7845095d764fad3ad9b397d04672/Grammar/python.gram), [listobject.c](https://github.com/python/cpython/blob/9f386367333f7845095d764fad3ad9b397d04672/Objects/listobject.c), [dictobject.c](https://github.com/python/cpython/blob/9f386367333f7845095d764fad3ad9b397d04672/Objects/dictobject.c), [ceval.c](https://github.com/python/cpython/blob/9f386367333f7845095d764fad3ad9b397d04672/Python/ceval.c) |
| llvm/llvm-project | `1b1fed44d3dcca649a9877915d57c3357a98124e` | [ParseExpr.cpp](https://github.com/llvm/llvm-project/blob/1b1fed44d3dcca649a9877915d57c3357a98124e/clang/lib/Parse/ParseExpr.cpp), [SemaExpr.cpp](https://github.com/llvm/llvm-project/blob/1b1fed44d3dcca649a9877915d57c3357a98124e/clang/lib/Sema/SemaExpr.cpp), [CGExpr.cpp](https://github.com/llvm/llvm-project/blob/1b1fed44d3dcca649a9877915d57c3357a98124e/clang/lib/CodeGen/CGExpr.cpp), [vector.h](https://github.com/llvm/llvm-project/blob/1b1fed44d3dcca649a9877915d57c3357a98124e/libcxx/include/__vector/vector.h), [AArch64InstrInfo.td](https://github.com/llvm/llvm-project/blob/1b1fed44d3dcca649a9877915d57c3357a98124e/llvm/lib/Target/AArch64/AArch64InstrInfo.td) |
| openjdk/jdk | `0ffbaaa5f40fdfe6d227e10e2a734eda25772121` | [JavaCompiler.java](https://github.com/openjdk/jdk/blob/0ffbaaa5f40fdfe6d227e10e2a734eda25772121/src/jdk.compiler/share/classes/com/sun/tools/javac/main/JavaCompiler.java), [threads.cpp](https://github.com/openjdk/jdk/blob/0ffbaaa5f40fdfe6d227e10e2a734eda25772121/src/hotspot/share/runtime/threads.cpp), [ArrayList.java](https://github.com/openjdk/jdk/blob/0ffbaaa5f40fdfe6d227e10e2a734eda25772121/src/java.base/share/classes/java/util/ArrayList.java) |
| dotnet/roslyn | `b907b90240f9f22873227aa510794dd280d61f57` | [SyntaxFactory.cs](https://github.com/dotnet/roslyn/blob/b907b90240f9f22873227aa510794dd280d61f57/src/Compilers/CSharp/Portable/Syntax/SyntaxFactory.cs), [VisualBasicCompilation.vb](https://github.com/dotnet/roslyn/blob/b907b90240f9f22873227aa510794dd280d61f57/src/Compilers/VisualBasic/Portable/Compilation/VisualBasicCompilation.vb) |
| dotnet/runtime | `5f7ac81dc6222f94c9bac5267ad2c01340b58f93` | [gc.cpp](https://github.com/dotnet/runtime/blob/5f7ac81dc6222f94c9bac5267ad2c01340b58f93/src/coreclr/gc/gc.cpp), [List.cs](https://github.com/dotnet/runtime/blob/5f7ac81dc6222f94c9bac5267ad2c01340b58f93/src/libraries/System.Private.CoreLib/src/System/Collections/Generic/List.cs) |
| v8/v8 | `fb3d762b1d35683776a99bdf4ce466a404280002` | [parser.cc](https://github.com/v8/v8/blob/fb3d762b1d35683776a99bdf4ce466a404280002/src/parsing/parser.cc), [interpreter.cc](https://github.com/v8/v8/blob/fb3d762b1d35683776a99bdf4ce466a404280002/src/interpreter/interpreter.cc), [heap.cc](https://github.com/v8/v8/blob/fb3d762b1d35683776a99bdf4ce466a404280002/src/heap/heap.cc) |
| wch/r-source | `780021752eb83a71e2198019acf069ba8741103b` | [gram.y](https://github.com/wch/r-source/blob/780021752eb83a71e2198019acf069ba8741103b/src/main/gram.y), [memory.c](https://github.com/wch/r-source/blob/780021752eb83a71e2198019acf069ba8741103b/src/main/memory.c), [eval.c](https://github.com/wch/r-source/blob/780021752eb83a71e2198019acf069ba8741103b/src/main/eval.c) |
| postgres/postgres | `9a849767eb281c9502aab4a7384a654004ec6ffe` | [gram.y](https://github.com/postgres/postgres/blob/9a849767eb281c9502aab4a7384a654004ec6ffe/src/backend/parser/gram.y), [execMain.c](https://github.com/postgres/postgres/blob/9a849767eb281c9502aab4a7384a654004ec6ffe/src/backend/executor/execMain.c), [xact.c](https://github.com/postgres/postgres/blob/9a849767eb281c9502aab4a7384a654004ec6ffe/src/backend/access/transam/xact.c) |
| golang/go | `f37eedeb17ddc24aeeb66e69b9f94a99d23d5504` | [README.md](https://github.com/golang/go/blob/f37eedeb17ddc24aeeb66e69b9f94a99d23d5504/src/cmd/compile/README.md), [proc.go](https://github.com/golang/go/blob/f37eedeb17ddc24aeeb66e69b9f94a99d23d5504/src/runtime/proc.go), [mgc.go](https://github.com/golang/go/blob/f37eedeb17ddc24aeeb66e69b9f94a99d23d5504/src/runtime/mgc.go) |

C and C++ share this Clang sample; libc++ adds a C++ library implementation. C# and VB.NET share the .NET runtime but retain separate Roslyn compilers. VB.NET does not stand for every historic Visual Basic implementation. PostgreSQL represents one SQL dialect and database engine, not all SQL. `wch/r-source` is an R implementation mirror; the R Core manual remains the semantic reference. A branch-head snapshot is not necessarily a released version. None of these samples constitutes an exhaustive standards-conformance assessment.

## What the mature implementations separate

| Language and semantic reference | Data, errors and resource model | Runtime, libraries, tooling and targets | RF2 comparison and next useful gate |
| --- | --- | --- | --- |
| [Python](https://docs.python.org/3/reference/datamodel.html) | Object values, mutable lists and dictionaries; exceptions; implementation-managed memory | CPython grammar, evaluator and container internals are separate responsibilities; host libraries and extensions supply much of the ecosystem | RF2 has scalar records and bounded bytes, not general dynamic objects/maps. Build nested structured input processing with recoverable errors before claiming Python-like utility |
| [C / Clang toolchain](https://clang.llvm.org/docs/Toolchain.html) | Typed values, pointers, explicit allocation and release; errors commonly carried through return values | Parsing, semantic checking, code generation, assembler/linker, runtime and platform libraries are distinct parts of a usable toolchain | RF2 emits Darwin ARM64 code directly, but this does not provide every ABI, target or C library. Qualify one FFI boundary and another target independently |
| [Java specifications](https://docs.oracle.com/javase/specs/) | Classes, interfaces, generics, exceptions and managed references | javac, JVM, standard collections and threading services are separate layers; Java source support alone is not JVM/library compatibility | RF2 lacks comparable general object/generic/runtime services. Demonstrate structured collections and deterministic resource failure behavior first |
| [C++ / libc++](https://libcxx.llvm.org/) | Templates, object lifetime, RAII and containers; exceptions and explicit error styles | Compiler implementation is distinct from standard library, ABI and platform services | Owned RF2 files and local byte vectors are narrower than general RAII. Test ownership transfer, alias invalidation and cleanup on every supported exit before extending the guarantee |
| [C# reference](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) | Classes/structs, generics, exceptions and managed memory, with explicit resource disposal idioms | Roslyn compiler and .NET GC/library implementation are distinct; application frameworks add their own contracts | RF2 results are deliberately bounded, not general generic sum types. Add richer typed error payloads only with exhaustive-handler and layout tests |
| [JavaScript / ECMAScript](https://tc39.es/ecma262/) | Objects, arrays, closures, exceptions and promises | V8 parser, interpreter and heap implement engine behavior; filesystem, networking and event loops belong to a host contract | RF2 MCP is a bounded host interface, not a browser/Node replacement. Implement one explicit asynchronous capability with cancellation before claiming host parity |
| [R language definition](https://cran.r-project.org/doc/manuals/r-release/R-lang.html) | Vector-oriented values, lists, environments and evaluation semantics | Parser, evaluator and memory manager underpin statistical libraries; numerical and missing-value semantics matter | RF2 lacks floating-point/statistical data breadth. Verify numeric representation and missing-value handling against independent expected results before scientific workloads |
| [SQL / PostgreSQL conformance](https://www.postgresql.org/docs/current/features.html) | Relations, declarative queries, null semantics and transactional operations | Parser, executor and transaction manager are separate; dialect conformance and persistence are engine-specific | An RF2 parser or in-memory collection is not a database. Specify crash, isolation and durable-write contracts before introducing database claims |
| [Visual Basic reference](https://learn.microsoft.com/en-us/dotnet/visual-basic/language-reference/) | VB.NET has its own syntax, types and runtime-language services | Roslyn VB compilation uses the wider .NET runtime/library platform; classic VB compatibility is outside this sample | Readable RF2 syntax is useful but insufficient to replace desktop ecosystems. Test one complete user workflow and packaging/accessibility requirements |
| [Go specification](https://go.dev/ref/spec) | Structs/interfaces, slices/maps, typed returns, goroutines and channels | Compiler and runtime coordinate scheduling, GC and standard-library services | RF2 lacks tasks, channels, synchronization and cancellation. Implement a race-aware bounded concurrency contract, not just a thread-spawn syscall |

These are capability categories, not equal-weight scores. “Has a compiler” is not equivalent to “has the library, deployment, debugger and maintenance ecosystem.” AI can generate source in existing languages as well as RF2. RF2's potential advantage must be tested as a complete, checked authoring workflow with explicit authority and understandable diagnostics.

### Concrete source observations

The pinned CPython `listobject.c` distinguishes logical size from allocation and handles resizing failure. Pinned libc++ `vector.h` checks requested capacity and maximum size in `reserve`, using a separate buffer for relocation. OpenJDK `ArrayList.java` computes new capacity before copying. These are examples of mature storage engineering, not evidence that one growth factor is universally fastest. RF2's reservation-backed vector currently avoids general relocating-container alias questions by restricting ownership and scope.

The pinned .NET `gc.cpp` explicitly separates allocation and collection responsibilities and server/workstation configurations. Go's `schedule` checks scheduler state before dispatch; `gcStart` checks whether the current runtime state permits starting collection. Safe concurrency requires runtime invariants, not only syntax. The PostgreSQL parser's opening notes prohibit parse actions from accessing the database or depending on mutable session state during multi-statement parsing. That separation is directly relevant to keeping RF2 checking free of unapproved effects.

The source sample establishes where responsibilities live and motivates RF2 requirements. It does not establish upstream defect rates, relative performance or security superiority. Full path links above make each observation inspectable.

## Assembly, hexadecimal and the machine boundary

The pinned LLVM AArch64 instruction definitions are an implementation sample for a specific ISA. They do not describe all assembly languages or all hardware. RF2's machine emitter needs instruction encoding, register/stack rules, calling conventions, executable layout and platform behavior. Hexadecimal and ASCII are representations; neither adds a new instruction set or lets software change fabricated transistor topology. Device control, GPU execution and optical computing each require the relevant target, driver or apparatus and executed evidence.

## A–Z acceptance ledger

This is an explicit review checklist, not an assertion of exhaustive coverage. Status refers to released 0.17 contracts, not unqualified sprint candidates. See [capability map](CAPABILITY-MAP.md), [storage and results](STORAGE-RESULTS.md), [second opinion roadmap](SECOND-OPINION-ROADMAP.md) and [external review brief](EXTERNAL-REVIEW-BRIEF.md).

| Area | RF2 baseline / gap | Decisive acceptance evidence |
| --- | --- | --- |
| A Arithmetic | u64 systems and checked/wrapping u32 Core; numeric breadth incomplete | Boundary, overflow and independent signed/float oracle tests for each new type |
| B Bytes | Fixed byte arrays and bounded reservation-backed vectors | Empty/full/growth/failure cases without corrupting existing contents |
| C Control | Branches, loops and helpers; bounded Core differs from systems | Short-circuit effects and nested control-flow differential tests |
| D Data | Scalar nominal records; no general nested collections/maps | Layout, update, alias and serialization tests for new data types |
| E Errors | Exhaustive bounded result handling; scalar errors | Every supported error branch, rich payload layout and propagation failures |
| F Functions | Local helpers/modules; limited public interop | Calling-convention and FFI ownership round trips |
| G Generics | Not general-purpose generics | Sound substitution and code generation, including rejected invalid programs |
| H Heap/lifetimes | Local noncopyable owners; no general heap ownership | Move/borrow/escape rejection and use-after-release adversarial corpus |
| I Input/output | Trusted files/CLI; short I/O remains caller responsibility | Truncation, partial reads/writes, permissions and cleanup failure injection |
| J Jobs | No general concurrent task runtime | Deadlock, cancellation, bounded queues and scheduling under contention |
| K Kernel/ABI | Darwin ARM64 qualified route | Another target's executable and ABI tests on that actual target |
| L Libraries | Narrow implemented application capabilities | Stable contracts, malformed input and version compatibility tests |
| M Modules/packages | Local imports; no registry | Deterministic dependency resolution and reviewed package provenance |
| N Network | No qualified networking/TLS stack | Timeout, protocol framing, TLS validation and connection cleanup |
| O Optimization | Narrow guarded reductions and fallback paths | Independent oracle, invalidation tests and full time distributions |
| P Permissions/effects | MCP bounded; systems code is trusted | Undeclared effect rejection and authority-boundary escape tests |
| Q Queries | No relational engine | Explicit null, transaction, durability and recovery contracts |
| R Reproducibility | Self-reproduction receipts exist; scope bounded | Clean build inputs, toolchain identity and externally repeatable receipts |
| S Source diagnostics | Existing parser/compiler diagnostics | Exact source spans and useful errors for generated and imported code |
| T Targets/tooling | Native Mac route; broad targets unimplemented | Debug information, packaging and target-specific acceptance suites |
| U Unicode | UTF-8 scalar views; not grapheme normalization | Invalid sequences, combining characters and clear indexing contracts |
| V Verification | Finite local regression corpus | Independent tests, mutation tests and false-acceptance/failure accounting |
| W Web/UI | Bounded browser editor; no general UI framework | Accessibility, state persistence and real user workflow tests |
| X Cross-language | No broad library/ABI compatibility | Independent producer/consumer tests and documented data ownership |
| Y Yield/async | No qualified general async/cancellation | Cancellation at each suspension with resource state checked |
| Z Zero inflated claims | Feature and test scope must remain explicit | Review claims against actual receipts, failed cases and limitations |

## Priorities and falsifiable success

1. Preserve checked semantics through a typed, effect-aware internal representation. Give every optimizer a stated precondition, a fallback and independent expected outputs. Text patterns alone cannot establish semantic equivalence.
2. Expand data and lifetime capabilities deliberately: richer typed errors, nested records, ownership transfer and general collections. Carry malformed input, allocation failure and cleanup errors through real applications.
3. Stabilize library, package and interoperability contracts. Reuse a small number of trustworthy capabilities rather than claiming every platform from raw syscalls.
4. Add concurrency only with cancellation, synchronization and cleanup behavior. Then qualify platform backends with actual acceptance runs.
5. Evaluate AI-assisted productivity using matched complete tasks, a named model/tokenizer, all prompts and retries, correctness review and total execution cost. Shorter source spelling alone is not fewer tokens or less engineering effort.

A good RF2 result is a working application that another person can build, inspect, repair and safely extend. Number-one adoption, universal speed wins, hardware breakthroughs and worldwide novelty are hypotheses, not conclusions of this audit. The five experimental mechanisms in the companion sprint should be judged against prior art and adversarial tests before being advertised as differentiators.

## What remains unverified

No entire upstream repository was reviewed line by line. No ten-language benchmark, compiler build matrix, full standards suite, ISA audit or independent security certification was executed here. Library ecosystem sizes and implementation effort were not measured. The selected snapshots can guide implementation and external review; they cannot prove parity with ten mature ecosystems or that humanity missed a fundamental computational primitive.
