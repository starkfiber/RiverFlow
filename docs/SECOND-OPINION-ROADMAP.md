# RF2 second opinion and evidence roadmap

## Implemented 0.17 update

The native 0.17 increment implements reservation-backed byte vectors and small record-valued success results. Its contract and precise limits are in [storage/results](STORAGE-RESULTS.md), with [release qualification](RELEASE-0.17-VERIFICATION.json). The retained loop reentry use-after-release case was corrected with runtime lifetime guards. Controlled native fault injections are not actual OS OOM measurements. This update does not rerun competitor builds or turn the original 0.16 source comparison into a new parity assessment. Earlier candidate proposals below remain explicitly historical/planning material.


Review date: 12 November 2026, Malaysia time. This is an independent task within the same AI-assisted development session, not a human audit or a review by a separate AI provider. It inspected the released RF2 0.16 baseline and selected primary implementation files in CPython, OpenJDK and LLVM. It did not build those upstream projects or run a comparative performance experiment.

**Assessment:** RF2 is a working, narrowly qualified native language/toolchain with useful file applications and an explicit MCP boundary. It is not yet a general replacement for the libraries, platforms, tooling and compatibility contracts of Python, Java or C++. Growable storage and structured outcomes are the right next foundations. Adding more application templates before those foundations would increase surface area faster than capability.

## Revisions reviewed

The following references are pinned for reproducibility; development HEAD is not a released version or a maturity guarantee. Re-pin explicitly for a later review.

| Project | Exact revision | What was inspected |
| --- | --- | --- |
| [RF2 0.16](https://github.com/starkfiber/RiverFlow/tree/83bd22eb3e82f3e616354bd6f8cc5edbafd265b0) | `83bd22eb3e82f3e616354bd6f8cc5edbafd265b0` | Native compiler, capability and ownership contracts, logical guard/app tests, release receipts |
| [CPython](https://github.com/python/cpython/tree/10862056f51eed3a332be3eefd51d4d6e871dade) | `10862056f51eed3a332be3eefd51d4d6e871dade` | Parser/compiler/interpreter entry points; list/dict implementations; file I/O and list tests |
| [OpenJDK](https://github.com/openjdk/jdk/tree/b9519c26738e8718e2f9a3db73821c864012322e) | `b9519c26738e8718e2f9a3db73821c864012322e` | javac compiler, Java thread/heap implementation, ArrayList and AutoCloseable |
| [LLVM project](https://github.com/llvm/llvm-project/tree/40cdba30a2892c3212b4133258bd1cb725a071fb) | `40cdba30a2892c3212b4133258bd1cb725a071fb` | Clang parsing/semantic/code-generation files; loop vectorizer; libc++ vector and unique_ptr |

Repository metadata and 18 selected source files were fetched from their public primary repositories. The local fetch/hash manifest is retained under `artifacts/second-opinion/PRIMARY-SOURCE-MANIFEST.json`; that ignored engineering artifact is not required to understand this public roadmap. No entire-repository equivalence or review of every upstream subsystem is claimed.

The 0.17 growable-storage and structured-result work was requested during this review. It remains a candidate until its own final compiler hash, contracts and executed receipts are qualified. Do not read this baseline assessment as certification of later working-tree changes.

## Compare the right things

Python is a language; CPython is one implementation, including its interpreter, object model and standard library. Java is a language and platform; OpenJDK combines a compiler, VM/runtime and libraries. C++ is a standardized language, not one canonical implementation repository. In this comparison, Clang supplies the C++ front end, LLVM supplies optimization/backends, and libc++ supplies a standard-library implementation. A complete C++ toolchain also needs platform-dependent runtime/linking components. [Clang toolchain documentation](https://clang.llvm.org/docs/Toolchain.html), [libc++ project](https://libcxx.llvm.org/).

RF2 should be compared separately at language semantics, compiler, runtime, libraries, tooling and target integration. Counting repository lines or implementation languages does not measure capability. CPython being implemented partly in C does not mean its users program every Python task in C. RF2's use of Python/JavaScript development controllers does not establish a Python/Node dependency for a tested native user executable.

| Layer | Useful upstream implementation evidence | RF2 0.16 position | Gap to close |
| --- | --- | --- | --- |
| Front end | CPython separates parsing, compilation and execution; Clang retains an inspectable AST and semantic analysis | Bounded source scanner with checks interleaved with direct emission and token-pattern optimizers | A typed/effect-aware intermediate representation, source locations and diagnostics before emission |
| Data/object model | CPython list/dict/object machinery; OpenJDK collection classes; libc++ generic containers | Fixed nominal u64/u8 arrays, scalar-field records, function-local byte/text views | Growable containers, nested values, maps, strings and explicit lifetime rules |
| Memory/lifetimes | CPython private-heap domains; OpenJDK heap/GC machinery; libc++ allocation and ownership helpers | Function-frame objects and noncopyable owned files; trusted raw memory remains available | Owned growable memory, transfer/borrowing, allocation failure and cleanup policies |
| Errors and cleanup | OpenJDK AutoCloseable; Clang exception/cleanup lowering | Scalar nominal results, exact handlers, ordinary-return file cleanup and first-cleanup-error protocol | Structured success/error payloads, error context and aggregation, explicit fatal/cancellation rules |
| Numeric model | Mature runtimes/libraries support substantially broader numeric types and operations | Unsigned scalar systems arithmetic plus a separate checked/wrapping u32 Core | Specify signed types, floats, conversions and overflow before claiming numerical breadth |
| Optimization | LLVM has independent optimization and target-lowering infrastructure | Several guarded, workload-specific scalar/reduction paths and retained fallbacks | Verified IR passes, alias/effect reasoning, broader workloads and multi-host measurement |
| Standard libraries | Collections, I/O, text, networking and many other components are separate subsystems | A small set of useful file/document capabilities and examples | Stable library APIs, testable network/TLS boundaries, serialization and package provenance |
| Targets/tooling | Upstream target implementations and toolchain components are not just source syntax | Qualified Apple Silicon macOS emitter; explicit OS signing; local browser-based Studio | Target-specific ABIs/object formats/linking, debugger/source maps, language tooling and packaging |
| AI integration | An external client may generate or explain code in any language | Nine native bounded MCP tools; host supplies intelligence | Matched complete-task evaluation and retained usage receipts before AI productivity claims |

The table is an architectural comparison, not a standards-conformance matrix or a benchmark result. RF2 need not reproduce every historical feature of another language to be useful. It must specify and qualify the applications it promises.

## Concrete lessons from primary source

CPython's list resize implementation separates logical size and allocated storage, and its private-heap API specifies allocator-domain pairing and failure behavior. RF2 should define the same categories for its own storage contract without copying CPython's object model or growth formula. [Pinned list implementation](https://github.com/python/cpython/blob/10862056f51eed3a332be3eefd51d4d6e871dade/Objects/listobject.c), [memory API](https://docs.python.org/3/c-api/memory.html).

OpenJDK ArrayList has explicit capacity-growth logic. Its AutoCloseable contract addresses close failures and resource state. These are useful review questions for RF2, not a reason to add Java exceptions or garbage collection automatically. [Pinned ArrayList](https://github.com/openjdk/jdk/blob/b9519c26738e8718e2f9a3db73821c864012322e/src/java.base/share/classes/java/util/ArrayList.java), [pinned AutoCloseable](https://github.com/openjdk/jdk/blob/b9519c26738e8718e2f9a3db73821c864012322e/src/java.base/share/classes/java/lang/AutoCloseable.java).

Clang's AST/semantic/code-generation separation and libc++'s distinct vector and ownership components illustrate why a language's core, optimizer and libraries should not be conflated. RF2's previous optimizer admission fixes make a typed representation a practical reliability priority. This is a review inference, not proof of an unfixed compiler defect. [Clang AST](https://clang.llvm.org/docs/IntroductionToTheClangAST.html), [pinned semantic analysis](https://github.com/llvm/llvm-project/blob/40cdba30a2892c3212b4133258bd1cb725a071fb/clang/lib/Sema/SemaExpr.cpp), [pinned vector](https://github.com/llvm/llvm-project/blob/40cdba30a2892c3212b4133258bd1cb725a071fb/libcxx/include/__vector/vector.h), [pinned unique_ptr](https://github.com/llvm/llvm-project/blob/40cdba30a2892c3212b4133258bd1cb725a071fb/libcxx/include/__memory/unique_ptr.h).

## Prioritized gates

Priority expresses dependency and risk, not a promised date or percentage. Each row closes only when the final revision has the named evidence.

| Gate | Deliverable | Acceptance evidence |
| --- | --- | --- |
| P0: growable storage | Specified initial/maximum capacity, growth arithmetic, indexing and mutation; owned allocation/release | Forced allocation failure preserves old contents and metadata; boundary/overflow tests; repeated growth/release; deterministic allocator seam; real app exceeding the old fixed-array limit |
| P0: structured outcomes | Defined payload layout, caller/callee ABI, scope and cleanup interaction | Nested calls preserve payloads; caller owns returned storage; no pointer into a dead frame; distinct field order/values in both variants; wrong-type and escaped-arm refusals |
| P0: release reliability | Reproducible source/binary identity and regression gate | Exact tagged source, fresh build, fixed-point evidence, final default/optimized runs, clean package and official MCP checks; failures retained |
| P1: typed representation | Parsing/type/effect validation precedes lowering; diagnostics with source locations | Equivalent expected behavior across baseline/new pipeline; invalid code rejected before emission; optimizer passes cannot bypass readiness, ownership or bounds checks |
| P1: larger data libraries | Growable bytes/u64 collections, strings, maps and serialization with stable contracts | Empty/large/duplicate/invalid inputs; growth failure and aliasing; Unicode policy; real search/index or document-processing app |
| P1: numeric breadth | Signed integer and floating-point specifications plus conversions | Edge/overflow/rounding/NaN/infinity tests against independent exact or high-precision expectations; no silent comparison with incompatible semantics |
| P2: developer tooling | Formatter, parser-based editor tooling, source maps and debugger integration | Malformed-source corpus, source/diagnostic roundtrips, a debug session mapping emitted operations back to RF2 source |
| P2: network services | Reviewed connection/TLS/error/timeout APIs and capability policy | Disposable service tests with short I/O, disconnects, retries and bounded resources; certificate/hostname failure cases; no new MCP network authority by accident |
| P2: concurrency | Task lifetime, shared-memory, atomics, cancellation and cleanup model | Deterministic interleaving/cancellation probes, races tested under a supported detector or equivalent instrumentation, teardown receipts |
| P3: target expansion | One additional backend/platform package at a time | Concrete built/executed target artifact, ABI/object format/linking checks, resource/permission behavior and clean install/run evidence |
| P3: ecosystem adoption | Versioning, compatibility, packages, provenance and contributor workflows | Third-party complete apps, locked dependencies, migration tests, license/security review and repeatable release qualification |

### P0 details that should block a release

A failed resize must not silently lose old data. If growth maps new storage then fails to release the old mapping, the implementation needs a stated recoverable state and retained ownership of every live mapping. It cannot simply forget one pointer. Capacity calculations require overflow checks before allocation or copy. A logical-length reduction must not expose stale bytes through later growth unless the contract explicitly allows that behavior.

A structured result must not return a pointer into the callee's expired frame. If hidden return storage is used, nested calls and cleanup must preserve its address. Handler payload lifetimes, mutability and variant-field type checking need admission tests as well as output tests. A matching numeric payload in one happy path cannot qualify a record ABI.

Allocation failure must be forced through an inspectable deterministic test seam or a genuinely measured OS failure. Merely requesting a huge block is unreliable on systems with virtual-memory overcommit. Fault injection is a test mechanism; do not describe the injected event as a naturally observed production incident.

## A comparison programme that can earn stronger claims

Use the same logical job and output oracle, not superficially similar source. Candidate workloads: a growing byte accumulator, stable record aggregation, JSON/CSV parse-and-report, Unicode search with a declared unit, and a small connection protocol after networking exists. Keep individual microbenchmarks separate from end-to-end applications.

For each run record machine/OS, exact revisions and compiler flags, runtime/build configuration, workload and input hash, correctness, failures, warmup and rotated trials. Separate startup, compilation, I/O and steady-state compute. Include memory high-water marks and total costs. Use uncertainty intervals and retain slower cases. A faster specialized reduction is evidence for that workload, not for RF2 versus a whole language.

AI productivity requires complete-task trials: matched instructions, model/version, prompt/context, tool policy, retries, actual provider usage receipts, final correctness and human review effort. File length or tokenizer counts alone do not establish generation speed or billed savings. Existing no-speed/no-token-claim receipts should remain intact until a matching experiment exists.

## External review handoff

Use [the review brief](EXTERNAL-REVIEW-BRIEF.md) with another AI or human reviewer. Request runnable counterexamples and source-linked findings before patches. Reproduce each issue on the named revision, preserve its oracle, apply the smallest correction, then replay it and the affected regressions. Keep unresolved and inconclusive findings visible. Source inspection by an AI is useful evidence, not independent institutional approval.

## Planning-only overlay: proposed 0.17 contract

This overlay evaluates the proposed contract, not an executed or released implementation. It must remain planning-only until final source/binary identities and test receipts are attached. The baseline comparison above is unchanged.

The proposed byte vector reserves a fixed virtual address range, initially inaccessible, up to a declared maximum of 1 MiB. Logical capacity grows after a successful permission change on a prefix; append can choose geometric capacity steps. Ordinary cleanup unmaps the reservation. This is a useful **bounded growable byte vector backed by a fixed virtual reservation**. It is not relocating allocation, arbitrary heap objects, an unlimited vector, a generic allocator or proof that the maximum resident memory has been physically committed. A stable address also does not itself prove safe borrowing.

The proposed structured result carries an ok record of at most four scalar fields in the private RF2 register protocol: x0 tag and x1 through x4 payload. The err arm remains scalar. A typed handler copies the record into the caller's frame and prevents passing that payload as a mutable helper argument. This is a practical value-return stage, not generic algebraic data types, nested structured payloads, a general foreign-function ABI or complete exception handling.

Apple's archived platform manuals describe mappings and page protection, including page alignment and errors, and distinguish unmapping from closing a file. They do not establish this RF2 implementation's behavior under every memory-pressure event. Actual host ABI and page-size assumptions need their own receipt. [mmap](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/mmap.2.html), [mprotect](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/mprotect.2.html), [munmap](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/munmap.2.html).

### Acceptance gates retained for this strategy

| Boundary | Required evidence before qualification |
| --- | --- |
| Reservation versus capacity | Exact reserved range and configured maximum; zero initial logical length/capacity; distinction between permission changes, touched pages and resident-memory measurements |
| Page granularity | Actual host page size; base/length handling; maximum and non-page-multiple limits; no logical access beyond length even if a kernel protection operation covers a larger page |
| Growth commit | Permission-change success precedes logical-capacity update; failure leaves logical length/capacity and existing readable bytes unchanged; no unnecessary permission call for an already sufficient capacity |
| Growth arithmetic | Geometric-step and rounding overflow checks, requests above maximum, zero operations and exact boundaries; allocation result checked before any data access |
| Mutation and aliasing | Append/index operations obey length and initialization rules; nominal identity and use-after-release checks; a live view cannot permit a forbidden mutation just because the virtual address is stable |
| Lifetime and release | Repeated reserve/grow/use/release in a live process; unmapping covers the reservation, not only current capacity; primary-versus-cleanup error policy; no exposed raw pointer in the checked interface |
| Record construction | Each field expression evaluated once in defined order; earlier fields survive a later function call; large and distinct values in all four positions |
| Record return and handling | Final payload copied into caller-owned storage; tag and all payload registers survive nested calls and ordinary cleanup; handler annotations and field order match the nominal type |
| Rejection and scope | Wrong payload type/count, wrong handler annotation, arm escape and attempted mutable helper passage refuse; scalar err behavior is preserved |
| Real application | A supplied input exceeds the old fixed-array limit, causes multiple observed growth transitions and returns a multi-field summary verified independently; failure and cleanup outcomes are also exercised |

The private result protocol needs special attention during cleanup: preserving only the former scalar tag/payload pair is insufficient for a four-field ok record. Similarly, populating x1 through x4 too early can lose a previous field when a later field expression makes a call. Neither issue is alleged as a reproduced defect here; they are explicit review targets.

### Deterministic fault injection is not observed OOM

The proposed native test injector replaces an expected Darwin syscall sequence with instructions that return a chosen errno and set the error carry flag. This can deterministically exercise the caller's mmap or mprotect failure branch. It does **not** produce an actual kernel allocation failure, exhaust RAM, establish memory-pressure resilience, or prove all real kernel side effects match the injected branch.

Retain original and patched executable hashes, patch offsets and expected original instruction words. Refuse a patch if its sequence/count does not match. Run a successful unpatched control, then the failure oracle without changing expected data, length or capacity. Report injected errno and branch coverage separately from any naturally observed system error. If real unmap failure is later injected, retain the stated ownership/retry policy rather than quietly treating every cleanup attempt as a successful release.

The reservation strategy avoids copying and releasing an old allocation during growth, so the earlier relocating-resize failure gate is not applicable to this specific implementation. It remains a gate for any future relocating allocator. That is a justified change in design, not evidence that a relocation test passed.
