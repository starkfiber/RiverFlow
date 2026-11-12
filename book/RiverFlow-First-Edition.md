# RiverFlow RF²
## Ideas into checked computation

Ilangkhumanan Thirunavokkarasu

Stark Fiber Enterprise

First edition, revised · November 2026 · Package 0.15

# About this edition

RiverFlow is a language in active development. This book describes a small language that runs, a compiler path that can be inspected, and a way to connect research questions to evidence. The complete original examples use RF2_U32_CORE_V0. The standalone 0.4 addition has a separate RF2_COMPACT_V1 front end and an explicitly distinct RF2_SYSTEM_A64_V1 implementation profile. Chapters 16 through 28 cover the later native compiler, applications, modules, guarded optimization, checked collections and recoverable text-processing libraries. The 0.15 compiler emits its own ARM64 machine code; early C-emitter examples remain historical reference routes. The profile matters more than the age of the book: another dialect may use familiar words while giving them different meanings.

RiverFlow aims to make programming understandable and useful. This edition does not claim universal compatibility, new semiconductor technology, independent academic approval or million-year durability. Claims need reproducible evidence.

The implementation was developed with AI assistance. Its parser, interpreter, C emitter and tests are available in the public repository. AI proposes and explains. A deterministic language contract defines which programs are accepted. The tests and measurements described here were executed locally, with their boundaries recorded. They do not establish every possible program or machine.

This is an independently published technical edition by Stark Fiber Enterprise. No ISBN, commercial publisher endorsement or university approval is asserted. Original text and code are provided under the repository’s MIT licence. The five RiverFlow concept artworks were generated with AI; they are artistic metaphors, not experimental figures. Third-party tools retain their own licences.

The current source, corrections and downloadable editions are at https://github.com/starkfiber/RiverFlow. The interactive playground is at https://starkfiber.github.io/RiverFlow/rf2/. Keep a copy of the specification and the release used for your experiment. A web page can change after a book is printed.

# 1. Begin with one small promise

A programming language is an agreement about meaning. Its spelling is the visible part, but the agreement also covers numbers, errors, effects and what happens when a program cannot finish within its limits. RiverFlow begins by making that agreement small enough to inspect.

RF² is pronounced RiverFlow Squared. The square is part of the identity. It does not add an infinity operator or turn every computation into a square root. The initial domain is unsigned, 32-bit integer computation over an input array. A program can load an element, add or multiply numbers, count set bits, test whether a value is nonzero, call scalar helpers and perform a bounded loop.

That is deliberately less than the full dream. A language that claims everything immediately leaves a reader unsure which part is implemented. A useful foundation gives a precise answer to a smaller question. Can this source be checked? What result does it produce? Which effects does it require? How is failure reported? Can another implementation produce the same observable behavior?

Consider a request to total five numbers. The user wants a result. The language must also decide whether a very large total wraps, whether a count can exceed the array, and whether a program may contact a server while it runs. Core answers those questions before any model becomes involved. Arithmetic mode is explicit, array access is bounded, and the only language effect is reading the supplied input.

The boundary gives AI a constructive role. A model can turn an idea into a proposed program and explain a rejected operation. It does not get to invent a working network instruction simply because the user asks for one. Unsupported behavior needs a new specification, an implementation and tests.

The deeper research question is therefore not whether AI can emit convincing syntax. It is whether a compact, inspectable contract can turn proposals into reliable, testable work. The compiler and runtime are part of that investigation. A phone operating system, a learned planner and an optical processor are separate implementations and experiments. They do not become integrated because their names appear in a diagram.

Try a simple standard while reading: after each feature, ask for an example, an expected result and a counterexample. The first demonstrates intent. The second gives a checking target. The third shows that the boundary has meaning.

# 2. Your first working river

For native 0.7 on Apple Silicon Mac, users run a standalone executable. The encoded minimum is macOS 14; actual qualification is on the recorded local Mac. Node, npm, Python and C++ are not runtime requirements. The executable uses macOS system interfaces; it is not an operating system of its own.

The first compact program is:

```text
rf2 v1 checked
sum input
```

Save it as sum.rf2. With the downloaded executable:

```sh
./rf2 run sum.rf2 '[1,2,3,4,5]'
./rf2 check sum.rf2
./rf2 expand sum.rf2
./rf2 mcp
```

The result is 15 with 18 abstract Core work events. These events are not processor cycles. Chapter 15 explains the native implementation, its tests and its four-operation boundary. General Core programs and helpers now also run through this native tool. Chapter 17 distinguishes runtime execution from per-program native compilation.

The historical release 0.4 build used a Python seed. The native compiler added in 0.5 can rebuild itself, and native 0.6 composes its runtime modules through the supplied build script. No Python, C/C++ compiler, assembler or linker is invoked by that native rebuild. The OS still signs the resulting image.

The detailed examples below retain the original Core profile. They now run in both the native runtime and the JavaScript reference. The browser playground remains a reference interpreter; it is distinct from the native executable.

Here is a complete program with no input-dependent calculation. It returns 520 in checked arithmetic.

```flow
FLOW "First light"
PROFILE RF2_U32_CORE_V0
ARITHMETIC CHECKED
FUNCTION main(data: u32[], count: u32) RETURNS u32
  STEP first = ADD WITH { a: 500, b: 20, result: answer }
  RETURN answer
END
```

FLOW gives the program a readable name. PROFILE chooses the contract. ARITHMETIC chooses what addition and multiplication do at the edge of the number range. The main function accepts an array and a count, even when this particular example does not use them. RETURN makes the result explicit.

Save that Core source in first.flow and run it with an empty array using native 0.6. You can check it without executing it, or lower it to systems source for inspection.

```sh
./rf2 check first.flow
./rf2 run first.flow '[]'
./rf2 lower first.flow
```

The native check command reports a validated plan. Lower returns systems-profile kernel source; a separate compiler step creates an executable. The retained JavaScript compile command writes JSON IR, and emit-c writes C. A source listing or successful build does not prove execution on a target device.

The website runs the reference interpreter in a browser worker without uploading source or arrays. Errors describe a contract to examine.

Exercise: change the constants and predict the result. Then test an unsupported operation; the checker must refuse it.

# 3. Numbers with a visible edge

A u32 value is an integer from zero through 4,294,967,295. A language needs a policy for operations whose mathematical result is larger. RiverFlow gives the program author two choices: CHECKED and WRAP.

In checked arithmetic, overflow is an error. Adding one to the maximum u32 value does not return a normal result. This is often the right starting point for quantities where silently changing a large number into a small one would hide a defect.

In wrapping arithmetic, the result is reduced modulo 2^32. The same addition returns zero. Wrapping arithmetic is useful when a computation is intentionally defined over fixed-width words. It should be a decision, not a surprise caused by the target compiler.

```flow
FLOW "Visible wrap"
PROFILE RF2_U32_CORE_V0
ARITHMETIC WRAP
FUNCTION main(data: u32[], count: u32) RETURNS u32
  STEP edge = ADD WITH { a: 4294967295, b: 1, result: value }
  RETURN value
END
```

This program returns zero. Change WRAP to CHECKED and it must fail with a checked arithmetic overflow. These two outcomes are not contradictory: the source explicitly selected different arithmetic contracts.

Multiplication needs particular care in a JavaScript bootstrap. Ordinary JavaScript Numbers cannot exactly represent every product of two u32 values. RiverFlow therefore uses BigInt internally for arithmetic and returns a u32 Number only after applying the selected rule. For example, multiplying the maximum u32 by itself in wrapping mode produces one. A floating-point approximation would be an unacceptable replacement for that behavior.

The C backend uses uint64_t intermediates. The product of two u32 values fits in an unsigned 64-bit integer. Checked mode compares the intermediate with UINT32_MAX. Wrapping mode converts the intermediate to uint32_t. These are implementation mechanisms for the same source-level agreement.

Do not equate a wide intermediate with a wider language type. Core still returns u32. It does not currently provide floating point, negative integers, strings or arbitrary-precision output. If your problem needs those types, the correct response is to identify the missing feature and design it carefully. Using an unrelated encoding without documenting it only moves ambiguity into the application.

Exercise: predict the result of 65,536 multiplied by 65,536 in each mode. The mathematical result is 2^32. Checked mode must reject it; wrapping mode must return zero. The calculation is small, but it tests the whole chain from source policy to emitted code.

# 4. Arrays, counts and bounds

An input array and an iteration count are related but different. The array tells the program which elements exist. The count can choose how many iterations to perform. Core requires the supplied count to lie within the array’s capacity, but a LOAD instruction addresses the declared array capacity, not an implicit slice restricted to count.

The standard sum program captures this distinction. It iterates from zero up to count, excluding the endpoint, and loads the corresponding element on each iteration.

```flow
FLOW "A river of numbers"
PROFILE RF2_U32_CORE_V0
ARITHMETIC CHECKED
FUNCTION main(data: u32[], count: u32) RETURNS u32
  VAR total = 0
  FOR i FROM 0 TO count LIMIT 65536
    STEP read = LOAD WITH { array: data, index: i, result: item }
    STEP add = ADD WITH { a: total, b: item, result: total }
  END FOR
  RETURN total
END
```

With [1,2,3,4,5] and a count of three, the result is six. With a count of zero, the loop performs no iterations and returns zero. The initial value is therefore part of the algorithm, not decorative setup.

The LIMIT value places a source-level maximum on the loop. It does not change an excessive count into a smaller one. A count larger than the declared loop limit fails. This avoids a dangerous convenience where the language quietly returns a partial answer while the caller believes it processed all the input.

The loop’s upper value is captured on entry. Parameters and the induction variable are immutable. Locals created inside the loop cannot escape its scope. Existing locals, such as total, can be updated. Nested loops are not part of this profile. Those choices simplify both reasoning and the work bound; they are not a statement that nested loops are inherently bad.

Memory deserves a second boundary when using generated C. A C pointer does not prove that an allocation exists. The caller must provide a valid, stable buffer and truthful length. The generated entry point checks supported capacities, alignment and output overlap, but it cannot turn an arbitrary integer address into a safe object. A language-level array contract and an operating-system memory boundary solve different problems.

Exercise: write a program that explicitly loads index one. Run it with [9] and then [9,12]. The first call must fail and the second must return 12. Then ask whether a count of one should forbid that explicit load when two elements exist. Core’s answer is no; capacity is the LOAD boundary. Record that rule before designing a slice type with different semantics.

# 5. Compose with scalar helpers

A small language becomes more useful when a reader can give repeated logic a name. Core helpers accept up to four scalar u32 arguments and return one u32 value. Calls use the helper’s parameter names. Forward calls are allowed, but recursion is rejected.

This complete program uses a helper to sum the squares of the input values.

```flow
FLOW "Squares in a stream"
PROFILE RF2_U32_CORE_V0
ARITHMETIC CHECKED
FUNCTION square(value: u32) RETURNS u32
  STEP product = MUL WITH { a: value, b: value, result: squared }
  RETURN squared
END
FUNCTION main(data: u32[], count: u32) RETURNS u32
  VAR total = 0
  FOR i FROM 0 TO count LIMIT 65536
    STEP read = LOAD WITH { array: data, index: i, result: item }
    STEP transform = CALL square WITH { value: item, result: term }
    STEP add = ADD WITH { a: total, b: term, result: total }
  END FOR
  RETURN total
END
```

For [2,3,4], the expected answer is 29. The helper call is not a request to an AI model. It is an ordinary deterministic function call in the checked program. A model may have helped write the source, but no inference service is needed to multiply two values during execution.

Recursion would require a different account of stack use and termination. Core instead checks the entire function graph for cycles. A cycle is rejected even if a particular example input would never follow it. The rule is intentionally structural. It keeps accepted call depth bounded without asking a model to guess whether a recursive function will terminate.

The checker also validates unused functions. A malformed helper is not made acceptable by leaving it disconnected from main. This makes the meaning of a compiled module less dependent on which test happened to run first.

A helper improves communication when its name identifies a useful concept. It makes code worse when it merely hides a simple operation behind a grand claim. A function called prove_security does not prove security because its name sounds authoritative. Its behavior and assumptions still need inspection.

Exercise: add a second helper that doubles a scalar with checked addition. Use it in place of square and predict the total for [2,3,4]. Then make the helper call itself. The checker should reject the cycle before any evaluation or C compilation.

# 6. Useful small algorithms

Core includes POPCOUNT and NONZERO because they make compact experiments possible without adding arbitrary host effects. POPCOUNT returns the number of set bits in a u32 word. NONZERO returns one for a nonzero value and zero otherwise.

A population-count reduction turns an array of words into a count of set bits. It can be useful for testing bit-oriented representations, but it does not make this release an optical computer or a general neural-network compiler.

```flow
FLOW "Count the lights"
PROFILE RF2_U32_CORE_V0
ARITHMETIC CHECKED
FUNCTION main(data: u32[], count: u32) RETURNS u32
  VAR total = 0
  FOR i FROM 0 TO count LIMIT 65536
    STEP read = LOAD WITH { array: data, index: i, result: item }
    STEP bits = POPCOUNT WITH { value: item, result: ones }
    STEP add = ADD WITH { a: total, b: ones, result: total }
  END FOR
  RETURN total
END
```

For [0,1,3,255], the result is 11: zero bits, one bit, two bits and eight bits respectively. A separate expected calculation is valuable. Comparing two implementations that copied the same mistaken algorithm is weaker than checking each against a simple independently calculated result.

Replace POPCOUNT with NONZERO and rename its result consistently. The resulting program counts occupied entries rather than bits. For [0,1,3,255], it returns three. These two questions sound similar in conversation and have very different meanings in code. Explicit operations make the difference reviewable.

A useful next step is to identify a real input representation. Does zero mean an absent observation, a failed sensor, or a legitimate measured value? The language cannot decide that domain meaning for you. An algorithm that is correct for the wrong interpretation still produces a misleading report.

For research, separate the mathematics from its use. A bit count can be checked exhaustively on selected small inputs and challenged with the full-width all-ones word. That does not establish that a downstream classification is accurate. Likewise, counting nonzero events does not establish that every event was collected reliably.

Exercise: create a tiny dataset and write down what each number represents. Calculate both reductions by hand. Explain which one answers your actual question. If neither does, the right improvement may be a better model of the problem rather than a faster implementation of the wrong reduction.

# 7. What the compiler checks

{{PIPELINE_FIGURE}}

A compiler is not just a translator. Before execution, RiverFlow checks whether source belongs to the selected language. It validates the header, parameter types, variable references, operation arguments, assignment rules and call graph. It rejects unknown effects rather than silently converting them into something convenient.

The implementation has a source-size limit, a function-count limit and a static body-node limit. Those limits keep this prototype’s accepted modules bounded. They also make testing more practical. A numerical limit should be recorded in the specification, not hidden in a mysterious timeout.

Checking all names before execution catches a class of errors that input examples alone cannot expose. A misspelled variable in a helper may not be exercised by today’s test. A type checker can still reject it. This is one reason AI-generated source should pass the same checks as manually written source.

The intermediate representation contains the selected arithmetic mode, the declared read_input effect and the checked function bodies. It is useful for inspecting what the compiler understood. It is not a proof object accepted by an independent theorem prover, and it is not a machine-code executable.

The public run path starts from source and validates it. It does not provide a tool that accepts arbitrary mutated IR and trusts its contents. If a future interface accepts serialized IR directly, it will need its own parser, validation and compatibility contract. Trust should not move invisibly from one interface to another.

The work budget is enforced during evaluation. Each function call, body statement and loop iteration consumes an abstract event. The maximum is 1,048,576 events per evaluation. POPCOUNT’s internal implementation is not counted bit by bit; its source operation has a defined event cost in this model. Consequently, the budget is a language accounting rule rather than a hardware timing guarantee.

Suppose a platform experiences a slow input read, a scheduler pause or a cold cache. The abstract event count may stay identical while elapsed time changes. A research paper about deadlines therefore needs measured timing and a scheduling model in addition to this counter.

Exercise: make a loop body longer while keeping its result unchanged. Ask whether the work count should change. In this profile, it does: extra source statements consume events even if a later compiler could eliminate their machine instructions. Preserving the observable count is part of backend equivalence.

# 8. Native C without changing the promise

Package 0.3 introduced C11 emission from the JavaScript reference. This chapter preserves that comparison path. Native 0.6 instead lowers Core through the RiverFlow systems compiler, described in Chapter 17. Neither route establishes phone execution.

```sh
node bin/rf2.mjs emit-c examples/sum.flow sum.c
clang -std=c11 -O2 -c sum.c -o sum.o
clang -std=c11 -O2 sum.c examples/native-driver.c -o first-native
./first-native
```

The second command creates an object file. The next commands link the supplied caller and run it; the expected result is 15 with 18 work steps. A program needs a caller and a link step. Treating sum.o as an operating system image would confuse three different levels of integration.

The emitted entry point is:

```c
int rf2_eval(const uint32_t *data, size_t words,
             uint32_t count, uint32_t *out,
             uint32_t *work);
```

A successful call returns zero and writes the result. The optional work pointer receives the abstract event count. The caller supplies valid allocations, truthful capacities and stable input. Output and work must not overlap one another or the input. The wrapper checks supported address alignment, arithmetic ranges and overlap before evaluating.

Error codes distinguish invalid ABI or capacity, checked overflow, LOAD bounds, the declared loop limit and the execution work limit. A failed evaluation does not write a normal result through out. A work count can still be reported for an evaluation failure. An invalid ABI call is rejected before that evaluation begins.

The general backend emits functions with generated C identifiers. It does not insert the user’s function spelling as arbitrary C syntax. Arithmetic uses unsigned intermediates, and helper calls carry the work and error state explicitly. The backend preserves the interpreter’s successful outputs and work events in the retained differential cases.

A native ABI is still a contract with a trusted caller. C cannot verify that an arbitrary non-null pointer names a real allocation. The wrapper does not provide process isolation or revoke operating-system privileges. To execute untrusted programs safely, a host must also consider the compiler, runtime process, resource limits and the platform’s security boundary.

The MCP emission tool returns C text only. It does not invoke Clang or execute a binary. This keeps a useful review step between a model requesting code and the host deciding to compile or run it.

Exercise: emit C for the checked sum and the wrapping example. Find the overflow check in the general path. Then connect a tiny C caller and compare its output with the interpreter. A matching result is evidence about that case, not a proof of every backend transformation.

# 9. One optimization that can be explained

Optimization is easiest to trust when its preconditions fit on a page. The first native optimization recognizes the exact simple input sum: a zero-initialized accumulator, a loop over the count parameter, one LOAD from the input at the induction variable, one ADD into the accumulator and a return of that accumulator. It does not recognize a function merely because it is named sum.

For this exact structure, the interpreter’s successful work count is W = 3 + 3n. There is one function event, one initialization statement and one loop statement. Every iteration adds an iteration event, a LOAD statement and an ADD statement. With at most 65,536 iterations, W is at most 196,611, below the execution budget.

That bound allows the native implementation to account for events directly rather than checking the general budget at every step. The loop limit is still checked before the first iteration. In checked mode, the implementation must stop at the first overflowing addition and report the corresponding event count. A final-only overflow check would not preserve that failure observation.

In wrapping mode, the mathematical sum of at most 65,536 u32 values fits in u64. Reducing the final sum modulo 2^32 gives the same result as reducing after every addition. That reasoning depends on the recognized operation and the declared maximum input. It does not automatically justify similar transformations for subtraction, observable intermediate values or arbitrary side effects.

The general emitter remains available through emitC(source, { optimize: false }). It gives the tests a conservative comparison. A useful optimization should survive deliberately similar programs that do not meet its preconditions: a nonzero initial value, a helper in the loop, a changed array index or a returned intermediate must not be silently treated as the exact sum.

The benchmark compares generated code with a handwritten sum implementation using the same ABI admission. Both are compiled with the same settings in separate translation units, without link-time optimization. The results describe the selected workload and host. They do not demonstrate a universal compiler advantage.

Exercise: change the initial total to one. Predict how the result changes and check that the exact-sum optimization no longer applies. Then explain which assumption in the derivation failed. Learning to reject an optimization for a nearby program is as important as learning to apply it to the easy case.

# 10. AI and MCP as an inspectable workshop

The Model Context Protocol connects a model host to tools and resources. In RiverFlow, the host supplies model intelligence. The local server provides bounded operations with explicit input schemas. Installing the plugin does not install an independent academic council or give a model new hardware authority.

The current native tools report capabilities, check source, execute Core or compact programs, return lowered kernels and export validated attendance records. A separate JavaScript reference provides batch evaluation, C emission and the public SFE repository catalog. Those reference features are not silently native tools.

A productive session starts by asking what is supported. The model then proposes source, calls the checker, runs known inputs and inspects errors. If the task needs a missing effect, the session should produce a versioned design proposal rather than a fictional successful tool response.

The catalog is intentionally narrower than an arbitrary web browser. A document request chooses a named repository from the snapshot. The server constructs the pinned public README URL. It does not accept an arbitrary URL, transmit account credentials or execute instructions found in the document. A README may contain an installation command, but reading that command is not permission to run it.

Batch evaluation is useful when several inputs share one program. Preparation happens once, while every input receives fresh execution state and its own budget. There is no persistent compiled cache or hidden training loop. An error rejects the tool call; a caller should not infer that every input completed merely because some early ones were valid.

Measurement tools deserve the same discipline. A ratio calculated correctly from invented numbers remains invented evidence. The comparison tool states that values came from the caller and that it has not authenticated measurement conditions. Units are explicit. A latency comparison does not establish energy savings.

For a practical agent workflow, retain the request, accepted source, profile, inputs, outputs, errors, tool version and code revision. This record lets another reader examine what happened. It is more useful than a transcript that simply says the agent approved itself.

Exercise: ask an assistant for a network operation in the current profile. A good answer identifies the unsupported effect and proposes a service extension. It should not manufacture a successful RF² network instruction. Use that refusal as a test of the whole workshop, not just the parser.

# 11. Read performance without fooling yourself

A performance number needs a denominator, a boundary and a comparator. RiverFlow’s early interpreter experiment measured repeated parsing, prepared execution and a direct JavaScript sum. Preparation improved the small repeated workload, but the direct loop remained much faster. Retaining that result changed the next engineering question: native lowering became a concrete experiment rather than a slogan.

The native benchmark measures a warm checked sum over resident arrays. Compilation, process startup, loading and allocation are excluded. It rotates candidate and baseline order, checks returned results and work counts, and retains every trial. The manual baseline shares the ABI admission but uses a straightforward sum loop. It is a stronger comparison than an intentionally slow interpreter.

The benchmark does not measure a phone, network request, cold application start or battery consumption. Its small-call timings amortize a clock over many calls. A few nanoseconds in a warm microbenchmark are not a promise of interactive latency. The full path may include parsing, copying, scheduling, input/output or service delays that dwarf the inner calculation.

A useful formula is speedup = baseline_time / candidate_time. A value below one means the candidate was slower. Another useful quantity is relative change = candidate_time / baseline_time - 1. Neither formula makes the inputs comparable. That judgment comes from the experimental design.

An average alone can conceal failure. A faster successful subset is not necessarily a better system if it misses deadlines, drops jobs or changes output quality. Keep the failure count, worst observed cases, setup costs and unsupported inputs visible. A language that omits required behavior has not optimized the same problem.

Repeat measurements in fresh processes and on more than one environment before making a broad claim. Fix the workload and acceptance rule before seeing the final result. If an experiment changes after a failure, preserve the failed protocol and explain the correction. Do not count repeated execution of the same deterministic model as independent hardware replication.

The retained benchmark tables are included near the end of this edition. They are a snapshot of the release evidence. They may motivate the next optimization; they do not decide whether every future design is good.

Exercise: compare a candidate that takes eight milliseconds with a baseline that takes ten. Then add five milliseconds of candidate-only setup. Report both the warm ratio and the complete first-use ratio. Explain which one answers your user’s question.

# 12. Build a service boundary before an operating system

The research behind RiverFlow includes native operating systems, bounded kernels, developmental learning, scheduling and human use of AI. Their questions can inform one another, but combining names is not integration. A service boundary gives those connections something testable to meet at.

Start with one operation. Specify its input ownership, result shape, errors, deadlines, cancellation behavior and authority. Then implement a reference backend over an established platform API. A native backend can attempt the same contract. Compare observable traces, including failures, rather than only successful return values.

This approach does not abandon native systems research. It separates the value of a language and coordination model from the cost of bringing up a particular peripheral. A hosted result may establish that the service contract is usable. It does not establish independence from the host OS. A native firmware acknowledgment may establish one transaction. It does not establish WiFi association or data transfer.

The Kernel 8 direction motivates deterministic work and resource accounting. Kernel 9 motivates adaptive proposals behind fixed guards. Developmental AI motivates a separation between learning and acceptance. Tamil Time Continuum motivates measuring scheduling decisions together with overhead and missed jobs. VOIKE motivates semantic comparison across execution backends. The human-AI workplace study motivates inspectable decisions and full operating costs. These are design links in this release, not implemented modules or confirmed hypotheses.

A future service extension must also decide what the current profile leaves out. Who grants a capability? What makes a service generation fresh? What happens if a reply arrives after cancellation? Can a failed owner release a resource that another subsystem still uses? Those are protocol and systems questions. Rewriting the source in a different language does not make them disappear.

The sensible unit of progress is one complete contract, with source identity and retained evidence. It is smaller than a universal OS and more useful than a diagram with no executable path.

Exercise: define a read-only clock service without implementing it. State the clock domain, units, monotonicity expectation, error behavior and whether the value proves anything about a remote device. Then identify which parts require a new language effect and which belong in the host service contract.

# 13. Testing as a form of explanation

A good test suite teaches the contract while challenging it. RiverFlow compares ordinary outputs with independently calculated answers and deliberately exercises overflow, bounds, recursion, scope and work limits. Native tests compile emitted C with address and undefined-behavior sanitizers and compare successful values and abstract work counts with the interpreter.

Sanitizers are valuable because a normal output can coexist with a memory defect. They are not a proof of all allocations or all hardware behavior. Their coverage is the executed test path. A test that never reaches a dangerous branch cannot establish that branch is safe.

Differential testing has a different limitation. If the interpreter and emitter copied the same mistaken rule, they may agree while both are wrong. Include independent examples, mathematical identities and boundary values. Zero iterations, all-ones words, exact overflow thresholds and a count just beyond capacity are often more informative than another random ordinary input.

For the recognized sum optimization, test nearby non-matching structures. The optimizer must decline a nonzero initial accumulator and preserve the general path. For prepared execution, run a successful input after a failed one to check that local state did not leak across calls. For MCP, test the actual stdio connection and tool schema, not a mock list of advertised names.

The book’s complete flow examples are checked by an executable tool in the repository. This avoids a gap where the implementation passes tests but the printed teaching example has drifted. Shell snippets and C snippets remain clearly distinguished from complete RiverFlow programs.

Keep evidence at the correct level. Parser checks, interpreter results, native host results, emulation and physical device observations answer different questions. A hash identifies retained bytes. It does not prove the claim written beside those bytes. An AI-assisted review is useful criticism, but it does not become human peer approval because several roles agreed.

Exercise: invent an intentionally wrong expected answer for the population-count example. A useful verification process must reject it. If a harness only prints PASS without checking results or its own failure path, the output is decoration rather than evidence.

# 14. Make the language durable

A long-lived language needs more than a memorable name. It needs a readable specification, stable examples, explicit versioning, reproducible builds where possible, migration paths and people willing to maintain them. Durability begins with modest claims that another person can check.

Profiles allow old meaning to remain identifiable while new capabilities develop. Package version 0.3 adds an implementation path without changing the Core profile’s arithmetic and effects. A future service dialect should have its own versioned contract if it changes observable behavior or permissions. Quietly broadening an old profile would make saved evidence ambiguous.

Preserve source and evidence separately from the installed tool cache. A cache is convenient for launching a plugin; it is not an archive strategy. Keep release source, the book source, machine-readable examples, test receipts and checksums. If a build is not byte-for-byte reproducible, record the difference rather than assigning it an invented explanation.

Publication also has limits. A downloadable technical book makes ideas available. It does not establish scientific novelty or academic acceptance. If a claim enters a thesis, link it to the actual experiment and its source revision. If the experiment used a model peer, say so. If a physical test failed, retain the failure and explain what changed before a later success.

The same rule applies to authorship and open source. Respect upstream licences and third-party contributions. A shared brand does not erase another person’s work. Original RiverFlow code and text are openly licensed, while dependencies and referenced standards retain their own terms.

The next useful milestones are practical: widen the example corpus, test more compilers and targets, improve diagnostics, design one service extension, and compare it against the simplest credible alternative. Each milestone should leave behind a program someone can run and a result someone can challenge.

The point is not to make readers admire a system they cannot inspect. It is to give them a foundation they can understand, use, question and improve. A small river becomes valuable when it reaches somewhere real.

# 15. A standalone river, with an honest bootstrap

The first native standalone is not a packaged JavaScript process. Its front end, arithmetic routines, JSON parser, UTF-8 handling, bounds checks, decimal output and MCP dispatch are written in RiverFlow source. The source uses an explicitly separate systems profile, RF2_SYSTEM_A64_V1, because it needs pointers, loops, 64-bit arithmetic and operating-system interfaces. Those facilities do not silently become part of u32 Core or permissions available to tool callers.

A small trusted seed compiler reads the systems source and emits ARM64 instructions and a Mach-O executable directly. macOS applies an ad-hoc signature. Neither a C/C++ compiler nor an assembler or linker is invoked by this build. The executable has no imported language-runtime symbols; it loads through the normal macOS dyld and libSystem interface and uses OS system calls for input, output and explicit command-line file reads.

In release 0.4 the seed itself was written in Python. That release established native execution rather than self-hosting. Chapter 16 records the subsequent bounded self-reproduction result in release 0.5. Saying everything is RiverFlow would currently hide a real dependency at build time. The native compiler must reproduce and qualify its own output before that claim can change; the executed scope of that check matters. Hardware instruction semantics, the operating system and code signing also remain external contracts.

## Small syntax, visible meaning

Compact V1 supports four reductions: sum, sum of squares, total set bits and number of nonzero elements. Each chooses checked or wrapping u32 arithmetic explicitly. The full vocabulary is shown here:

```text
rf2 v1 checked
sum input

rf2 v1 wrap
squares input

rf2 v1 checked
bits input

rf2 v1 checked
nonzero input
```

These are four separate programs, not one combined source file. The header and operation are required; whitespace separates their five tokens. The input array and optional prefix count are supplied separately. In the original 0.4 compact front end, unknown words, extra instructions, hidden effects and general Core source reject. Native 0.6 and later admit Core through a separate checked front end. The implementation does not claim to understand unrestricted natural-language requests.

The expand command prints the exact full Core source for the selected operation. That makes short notation inspectable: a compact sum expands to initialization, a bounded loop, input loads, additions and a return. The native implementation executes its admitted reduction using ARM64 instructions. It does not invoke a model or interpret each request through Python or Node.

## Evidence before adjectives

The executable passed 1,016 differential cases against the retained JavaScript reference and independent integer arithmetic. Successful values, work counts and overflow outcomes agreed. The tested corpus includes zero-length input, prefixes, maximum u32 values, full-width seeded words, smaller values and the maximum 65,536-word array.

Separate negative and parser checks challenge invalid data, count/capacity errors, unsupported profiles, malformed JSON, duplicate keys including escaped spellings, UTF-8 and surrogate handling, request-size and nesting limits, and recovery after a refused request. Seeded byte mutations test the actual native process. A separate official MCP SDK client exercises discovery, success, overflow refusal and the next successful call. The executable also runs with its command search path disabled, so launching another language runtime cannot explain the result.

The evidence is in docs/STANDALONE-VERIFICATION.json and the executable-level tests. It is not an independent audit, formal verification or proof that a hand-built parser has no defects. No new speed or energy measurement is asserted. The earlier C-backend timing table belongs to that earlier experiment, not this standalone executable.

## What is still open

The 0.4 standalone targeted Apple Silicon macOS and exposed three native tools. Release 0.6 adds general Core support, lowering and a versioned application operation, described in the following chapters. C emission, batch execution and public-repository research tools remain separate reference capabilities. General Core helpers and admitted statement sequences now have a native path. There is no automatic phone installation, wireless qualification or arbitrary application-generation capability.

After the systems-compiler milestone in Chapter 16, the remaining foundation is to migrate more Core behavior, qualify another target and review the machine encoder independently. Compact service plans then need real versioned implementations, explicit permissions and acceptance tests. A short command should save repeated description without concealing unimplemented work.

Hundreds of tokens rather than millions remains a hypothesis. Measure matched tasks from start to finish, including documentation, schemas, capability creation, tool responses and repairs. Count failures. Report first-use construction separately from reuse. A short source listing alone establishes neither task-level token savings nor better software.

# 16. RiverFlow builds its compiler

A compiler can be written in the language it compiles. The useful milestone is an executed build, with the resulting bytes and behavior checked. Release 0.5 adds a native compiler, rf2c, written in RiverFlow systems source. It reads the documented systems subset and directly emits an ARM64 Mach-O image. It does not call Python, Node, a C/C++ compiler, an assembler or a linker.

The operating system still signs the emitted image before execution. The build also depends on existing ARM64 hardware, macOS interfaces and a trusted starting compiler. Self-hosting does not mean a system has no external foundations. It means this compiler can compile its own supported source.

## Three generations, one image

The experiment begins with a native compiler produced by the historical seed. That compiler reads its own RiverFlow source and emits the next compiler. The generated compiler repeats the build, and a further native generation repeats it again. All three unsigned executable images match byte for byte, including the source-derived identifier.

The same native-generated compiler emits the existing computation runtime. That image also matches the historical encoder exactly. After signing, the generated runtime passes the 1,016 comparison cases against the JavaScript reference and independent integer arithmetic, as well as MCP discovery, overflow refusal and recovery checks.

These are actual generated-image and execution checks. The native compilation stages run with the command search path disabled, so an unnoticed Python or Node subprocess cannot account for their compilation. The controller invokes macOS signing explicitly between builds.

The result is narrower than universal language completion. It applies to the documented systems compiler source, its accepted lexical subset, the tested runtime source and the recorded Mac. It does not migrate arbitrary Core helpers, every historical ASMX dialect or application services. It does not establish a new speed result.

## Rebuild it yourself

The native download includes the compiler and both implementation sources. Choose a new output path each time:

```sh
./rf2c native/compiler/compiler.rf2 next-rf2c
/usr/bin/codesign -s - --force next-rf2c
./tools/build-runtime.sh ./next-rf2c next-runtime
./next-runtime/rf2 run examples/compact/sum.rf2 '[1,2,3]'
```

The expected value is six. The compiler refuses an existing output file or a symlink instead of overwriting it. A source or resource-limit refusal occurs before output creation. An operating-system write failure may leave an incomplete newly created file; that is a failed build, not an executable result.

The Python seed is preserved for initial bootstrap and development comparison. Preserving it is useful provenance. A native rebuild no longer needs it, but deleting the historical route would not prove that route had never influenced the compiler.

## Challenge the compiler

The verification executes 24 small programs with independently specified results. They cover arithmetic, unsigned comparisons, precedence, loops, conditional branches, memory access, quoted operators, forward calls and all eight argument registers. Their unsigned images also match the historical encoder.

Fourteen full source-fingerprint cases exercise empty input, padding boundaries, arbitrary bytes and the maximum source size. The native SHA-256 calculation follows the published algorithm in NIST FIPS 180-4 and is compared with the host reference. This is an implementation test, not NIST certification or a signature scheme.

Fifteen refusal checks include malformed source, unsupported calls, duplicate locals, comparison chains, buffer bounds, source depth/size limits and existing output protection. The source, generated artifacts and fingerprints are recorded in docs/NATIVE-COMPILER-VERIFICATION.json. A later edition should rerun the tests rather than inherit the numbers as a permanent score.

Several early failures improved the implementation. A library-path length error affected the image metadata. A comparison instruction used the wrong register field. Blank lines caused one function scan to miss a control statement. A quoted minus sign was incorrectly treated as an operator. The comparisons caught these before release; passing after correction does not erase the failures.

## What a fixed point cannot prove

Two agreeing compilers can share a mistake. A self-reproducing compiler can preserve unwanted behavior. These tests are not diverse double compilation, an independent audit or a proof of security. Trusted systems source still uses raw pointers and explicit OS calls. It must never be confused with the restricted input-only computation interface exposed over MCP.

The next chapters record the general Core and application checkpoint in 0.6. Broader target qualification and independent review remain open. The token-saving question remains separate: count complete matched tasks, including setup, tool context, failures and repairs. A self-built compiler is a meaningful foundation, not evidence that the entire application-building vision is finished.

# 17. General Core on a native foundation

A language becomes more useful when it can reuse a function without regenerating its implementation. Core already had named scalar helpers, forward calls and bounded loops in the reference implementation. Release 0.6 brings those behaviors into the native runtime, with a separate route for building per-program machine code.

The two routes deserve different names. The run command checks source and executes internal instructions in a native runtime written in RiverFlow. It does not secretly launch Node or Python. It also does not compile a new executable for each request. The build route lowers the checked program into RiverFlow systems functions and passes those functions to the native compiler. The resulting kernel contains instructions generated for that particular program.

{{NATIVE_PIPELINE}}

## Reuse the complete examples

The helper example in Chapter 5 is stored in book/examples/example-4.flow. It sums the squares of its input through a scalar helper. Both routes should produce 29 from the same data:

```sh
./rf2 check book/examples/example-4.flow
./rf2 run book/examples/example-4.flow '[2,3,4]'
./tools/build-core.sh ./rf2 ./rf2c \
  book/examples/example-4.flow squares-build
./squares-build/program '[2,3,4]'
```

The build script creates a new directory. It combines the lowered kernel fragment with a trusted input harness, invokes rf2c and explicitly applies macOS signing. The returned text from lower is not itself an executable, and a build log is not a measurement of the program's behavior. The tests execute the resulting artifact.

## Keep the contract intact

The native checker validates every function, including an unused helper. It checks argument names, arity, types and assignments, rejects call cycles, and keeps parameters and induction variables immutable. Main receives one read-only array and a count. Scalar helpers can accept up to four values. A loop captures its upper value on entry; names introduced inside it cannot escape.

A LOAD still uses input capacity, not the chosen prefix count. Checked arithmetic still rejects an excessive result. Wrapping arithmetic still reduces modulo 2^32. The source, function, instruction, input and work limits remain explicit. Neither a model nor the application adapter may quietly relax those rules to get a successful response.

Native input must be well-formed UTF-8. For valid Unicode, the source budget uses UTF-16 code units to match the reference string contract. Malformed file bytes and unpaired surrogate escapes reject at the native boundary. The conformance corpus also challenges Unicode trimming, exact statement formatting and unsupported line separators.

One test caught a subtle named-argument collision. A helper parameter named result can be declared, but a call cannot use the same unique field both as that input and as the required output field. The reference rejects the impossible call shape. The native checker now rejects it too, while permitting an unused helper with that parameter. Refusal cases are part of the contract, not obstacles to be hidden.

## What was actually executed

The general Core corpus contains 109 program entries, 317 admission checks and 1,095 executions against the reference. It includes helper chains, four named arguments, Unicode, restored loop scope, unused invalid functions, recursion, overflow, bounds and the work budget. A further 180 seeded source mutations are included in the admission count.

The direct-kernel corpus covers 18 native build cases and 163 actual executable runs. It includes all five complete original book examples, a program with 501 scalar registers, and an explicit work-limit refusal probe. The generated path agrees on successful values and work counts and on the expected dynamic error categories. The old compact corpus is rerun separately to preserve its earlier behavior.

Memory-backed frames keep generated functions within the systems compiler's local-variable limit. They are an implementation choice, not a performance result. A trustworthy account retains that cost and tests the register-heavy case instead of presenting only the smallest program.

These comparisons do not prove all possible programs correct. A shared assumption can survive differential testing, and the direct native code has not received an independent security audit. Sanitizer checks on the old C backend remain useful evidence about that backend; they are not sanitizer coverage of this machine-code path.

# 18. One application operation, end to end

The first application capability is attendance.local@1. It accepts attendance records, validates them, refuses duplicate student/date pairs, and produces CSV with present, absent and late counts. It is a batch exporter with a defined contract, not a claim that an entire school system or unrestricted application builder has been completed.

The supplied test-records.json contains three explicit TEST identifiers with one record in each state. They are programming inputs, not student observations or evidence of a school outcome. The local command is:

```sh
./rf2 attendance \
  capabilities/attendance.local.v1/test-records.json \
  register.csv
```

The expected counts are one present, one absent and one late. The receipt records the number of rows, CSV byte length and a SHA-256 fingerprint. An independent CSV reader checks that the exported records recover the original input fields and order.

## Make permission a concrete action

The CLI writes only the explicitly supplied new output path. It refuses an existing file or symlink, validates the dataset before opening the output, and creates an owner-only file. A write or close failure is reported as failure and may leave an incomplete newly created file. The implementation does not claim crash-safe journaling.

The MCP tool accepts records and returns CSV text. It accepts no path or permission argument and does not write a file. This distinction lets an assistant prepare a useful export while the host or person decides where to save it. Core itself still has only its read-input effect.

There is no hidden teacher authorization, editing interface or remote student database. Those would need separate contracts and tests. The operation is useful because it does one complete job with observable outputs and refusals, rather than presenting a template as an application result.

## Validate before counting

Each record must contain exactly a student ID, a canonical Gregorian date and a state. IDs are constrained to short ASCII identifiers that begin with a letter or digit. Delimiters, controls and formula prefixes reject. Dates are checked for real days and leap years, not only the shape of ten characters. State is exactly present, absent or late.

One student may appear on different dates. The same student/date pair cannot occur twice. This rule is checked before export, so the system does not silently discard or double-count a conflicting row. The current maximum is 1,000 records per request; an excessive dataset fails rather than being truncated.

The constrained fields make a simple CSV format sufficient. The declared round trip is tested with an independent CSV reader. It is not a guarantee that every spreadsheet editor will preserve identifiers when someone edits and re-saves a file.

## Use Core for the business calculation

The application does not merely surround a language demonstration with a new title. Its counts come from the versioned tally.flow program. The validator converts the three states to weights of 1, 1024 and 1048576. A checked Core sum, implemented through a scalar helper and bounded loop, combines them into three ten-bit count fields.

The admitted total cannot exceed 1,000, so no field reaches 1,024 and carries into the next field. The full packed value fits within u32. The exported counts are decoded from that generated result. This is ordinary bounded integer arithmetic, not a new mathematical theorem or a claim to solve a scientific conjecture.

The Core source is lowered by the native tool and compiled into the application. Its generated kernel can be reproduced and compared with the committed artifact. A capability manifest binds the source and kernel fingerprints. Hash identity helps detect changed bytes; it does not establish an authentic author, remote attestation or independent approval.

## Test the whole operation

The executed application corpus contains 34 successful exports or calendar acceptance cases, 45 refusals and three file-protection checks. Round-trip datasets include the maximum record count. The tests compare counts with an independent calculation, check actual CSV bytes and fingerprints, validate leap-year behavior, refuse duplicate/schema/unsafe-ID inputs, and verify that a later Core request still works after an application error.

The official MCP SDK separately exercises export and duplicate refusal. The CLI tests inspect the written file, its permissions and the unchanged contents of an existing file and symlink target. These are software observations from controlled programming inputs. They do not establish adoption, educational benefit, workplace savings, energy reduction or token savings.

The next application should reuse this discipline: a versioned interface, explicit authority, an implemented calculation, observable output and a refusal corpus. The token-economy question must then be measured across matched complete tasks, including setup, schema context, tool responses and repairs. A short invocation becomes valuable when the work behind it is real and inspectable.

# 19. A readable application plan, measured honestly

A useful short language needs something concrete behind its words. Release 0.7 adds a versioned application plan for invoice totals. It selects a real local operation with explicit data and arithmetic. It does not ask a model to invent accounting rules while calculating a price.

```rf2
rf2 app v1
invoice total
currency MYR
tax 600 bps
```

These ten words are the entire plan. ASCII whitespace separates them; their order is fixed. Currency is a three-letter uppercase label. The tax input is a canonical integer from zero through 10000 basis points. In this example, 600 basis points means a calculation rate of six percent. It is a chosen input, not advice that a particular transaction is taxable at that rate. The plan is limited to 256 bytes. Unknown versions, extra words and implied permissions reject.

With the downloaded native executable, run:

```sh
./rf2 app capabilities/invoice.total.v1/quote.rf2 \
  capabilities/invoice.total.v1/test-lines.json
```

The supplied programming fixture has two lines: two units at 1250 cents and one unit at 399 cents. The subtotal is 2899 cents. Invoice-level half-up rounding produces 174 cents of tax and a total of 3073 cents. These are executed arithmetic examples, not customer transactions or business outcome data.

## Give the money a precise meaning

Each line contains exactly quantity and unit_cents. Quantities are positive integers; prices can be zero. Both are bounded u32 values. The generated Core kernel multiplies quantity by price through a scalar helper, then adds the line amounts in a bounded loop. A line amount or subtotal that exceeds u32 cents rejects. The adapter calculates tax with an unsigned 64-bit intermediate and requires the final total to fit u32 as well.

The rounding rule is floor((subtotal times tax_bps plus 5000) divided by 10000). It applies once at invoice level. Applying it to each line could produce a different answer. That difference belongs in a business contract, not in an undocumented implementation detail. Negative credit notes, fractional quantities, discounts and exchange rates are outside this version.

The CLI reads the explicitly supplied files and returns JSON on standard output. It creates no invoice file and contacts no service. The native MCP tool invoice_total accepts the plan and lines and returns the same totals without filesystem access. It is a calculator capability, not an invoice PDF generator, accounting ledger, tax authority or payment service.

## Compare before celebrating

The conformance suite executes 630 successful comparisons, 108 subtotal comparisons with native 0.6, 39 refusals, 200 seeded plan mutations and five CLI cases. Independent integer calculations check the results. The cases include tax ties, zero and maximum amounts, total overflow, malformed inputs, duplicate JSON keys and successful requests after failures. The generated kernel is reproduced from its retained Core source. Existing Core, Compact V1, attendance, direct-kernel and compiler checks are rerun separately.

The timing experiment uses three fresh process pairs and seven rotated trials per size in each pair. The table reports medians of 21 batch averages. Timed work includes controller serialization, local pipes, validation, calculation and result checking. It excludes startup, compilation and model inference. These are local round-trip measurements, not processor cycles or individual latency percentiles.

| Lines | Native invoice, µs | JavaScript explicit config, µs | Core 0.6, µs | Core 0.7, µs |
| --- | ---: | ---: | ---: | ---: |
| 1 | 18.53 | 26.73 | 68.14 | 68.07 |
| 32 | 57.22 | 32.03 | 84.26 | 83.96 |
| 1000 | 1195.59 | 301.58 | 593.24 | 587.50 |

The native invoice operation wins on the smallest input and loses on the larger ones. The JavaScript comparator uses the same lines and exact integer arithmetic, with explicit currency and tax fields. Its ordinary JSON parser does not provide the native duplicate-key refusal; the timed inputs are valid canonical JSON. This is a useful practical comparison, not a proof that every security property is identical. Core timings remain close to the previous release. No general acceleration follows from this table.

## Count the complete interface

A short source listing is not the same as a small AI task. The plan itself uses 19 tokens in each of the two encodings tested. The experiment also counts the actual selected tool schema, 20 serialized requests and their 20 responses. The alternative reference tool takes currency and tax_bps directly and returns the same result fields.

| Encoding | Plan alone | Native schema + 20 round trips | Explicit schema + 20 round trips |
| --- | ---: | ---: | ---: |
| o200k_base | 19 | 3193 | 3010 |
| cl100k_base | 19 | 3128 | 2945 |

Repeating the plan costs more encoded interface tokens in this fixture. The native tool schema is slightly smaller, but that does not recover the repeated request overhead. The full six-tool native catalog is counted separately in the raw report rather than silently omitted from a whole-session claim.

No model inference was run for this experiment. The counts come from tiktoken 0.14.0 over retained text. They are not billed usage, hidden reasoning tokens or measurements of an AI building and repairing an application. Prompt caching, capability construction and failed attempts remain open parts of that experiment. A future saving claim needs complete matched tasks and actual usage receipts.

The next engineering decision should follow these results. Profile the larger native path before optimizing it. Consider plan reuse only with explicit lifetime and authority rules. Keep the readable plan where it helps people understand intent, and accept that ordinary structured arguments may be cheaper for repeated tool calls. A language improves by answering these questions with evidence rather than protecting its first slogan.

Sources: capabilities/invoice.total.v1/, docs/INVOICE-VERIFICATION.json, docs/CAPABILITY-MEASUREMENTS-0.7.json and docs/INTERFACE-TOKEN-FIXTURES.json. Every timing trial and encoded fixture is retained for another reader to inspect.

# 20. Reuse without hiding the rules

Release 0.8 follows the measurements rather than assuming short syntax must win. It adds checked-plan reuse, improves ordinary input handling and turns the invoice operation into a file-based workspace. Each part has a different contract. A saved document can survive a process. An in-memory plan handle cannot. Neither grants a payment or file permission through MCP.

## Separate setup from repeated work

The prepare tool checks an explicit invoice plan and returns its currency, tax rate and a process-local handle. A caller should inspect those rules before using it. Apply accepts that handle and fresh lines. Release removes it. There are 32 slots; filling them rejects further preparation rather than silently evicting a live plan.

Handles are locators, not authentication or signatures. A process-specific mask comes from OS entropy. A bounded monotonic counter combined with that mask never reissues a released number within the process. This does not prove global uniqueness across processes. Clients must discard handles on reconnect. Separate users should have separate server processes; multi-user isolation is not implemented. Internal entropy access accepts no caller-controlled path.

A failed request cannot silently change the currency or tax rate in a prepared plan. New lines still pass all checks. The interface accepts no rule override, file path or network argument. The tests fill the cache, apply distinct rules, challenge invalid requests, release plans and verify that a fresh process begins without them.

## Measure what changed

Development phase probes pointed toward JSON parsing and line validation as larger costs than reading the short plan. The implementation now avoids repeated field lookups and handles ordinary decimal u32 inputs directly, while retaining the exact parser for other admitted JSON number forms. Unescaped strings can borrow already validated input bytes for the active request. Escaped strings keep the decoder. Borrowed bytes are not retained as saved plan data.

The old suites were rerun after these changes, including malformed UTF-8, controls, duplicate decoded keys, numeric forms and recovery. Passing them is evidence about those cases, not an independent security audit. Three fresh process sets compare the final binary against frozen 0.7 and the exact-integer JavaScript comparator. The following medians cover 21 batch averages per size and variant, including controller and pipe costs, but excluding startup and preparation.

| Lines | Native 0.7, µs | Native 0.8, µs | Prepared 0.8, µs | JS, µs |
| --- | ---: | ---: | ---: | ---: |
| 1 | 18.99 | 18.84 | 17.27 | 25.12 |
| 32 | 57.95 | 50.43 | 49.03 | 32.48 |
| 1000 | 1187.25 | 962.26 | 959.95 | 294.88 |

The large native request improves over 0.7 here, while JavaScript remains faster. Reuse helps the smallest request more than the largest because new lines still need validation and arithmetic. The data does not support a general native speed, energy or platform claim. Raw phase and request observations remain in the repository, including their limits.

The token experiment includes every discovered tool schema and the complete prepare, apply and release lifecycle. It compares the same calculation with repeated unprepared 0.7 requests. Three issued handles per workload account for variation in their encoded spelling.

| Calls | Reuse, o200k | Unprepared, o200k |
| --- | ---: | ---: |
| 1 | 1119 to 1122 | 689 |
| 20 | 3703 to 3725 | 3577 |
| 100 | 14685 | 15737 |

Short sessions lose. The measured 100-call session wins on encoded interface size. These are exact tiktoken counts, not billed inference usage or a completed AI coding-task experiment. Actual matched model runs would still need usage receipts, construction costs, failed proposals and repairs. A handle saving repeated description is useful only when the operation behind it is real and its lifetime stays explicit.

## Save and revise a real document

The local workspace stores exactly a versioned format, the plan and lines. It recomputes totals on inspection and export. It rejects unknown stored total fields instead of trusting a stale number. Its commands are:

```sh
./rf2 invoice save capabilities/invoice.total.v1/quote.rf2 \
  capabilities/invoice.total.v1/test-lines.json first.invoice.json
./rf2 invoice inspect first.invoice.json
./rf2 invoice set first.invoice.json 0 2 250 edited.invoice.json
./rf2 invoice remove edited.invoice.json 1 revised.invoice.json
./rf2 invoice pdf revised.invoice.json worksheet.pdf
```

Indices start at zero. Set can replace a line or append at the current count. Every edit names a new file. Existing files and symlinks are refused; the previous document remains unchanged. A failed operating-system write can leave a partial new file, so crash-safe transactions are not claimed.

The PDF writer is RiverFlow systems source. It writes objects, content streams, page references and cross-reference offsets directly. No external PDF renderer is launched by the user workflow. Forty lines fit on an A4-sized page; larger inputs continue across pages, with totals on the last page. Test libraries independently parse the generated zero, forty, forty-one and thousand-line cases, check page counts and bounds, and reject the need for repair. The example is also rendered for visual inspection.

This is a file-based workspace, not a graphical editor or a legally complete invoice service. It provides editable lines, saved revisions and printable calculation worksheets. Customer registration, tax-law decisions, payments and accounting records need their own requirements. Programming fixtures remain distinct from customer activity.

## Expand a bound with evidence

The runtime had reached the systems compiler's 128-function limit. Release 0.8 widens it to 256, expands both metadata and local-name storage, executes the upper accepted cases and rejects 257 before creating output. The last test function uses all 256 local slots. Native compiler generations reproduce their unsigned image, and the complete runtime still matches the historical encoder.

The larger systems bound does not change Core's sixteen-function contract. It gives implementation modules room to grow while keeping saved computation semantics identifiable. Independent review, more targets, a graphical interface and actual AI-task usage measurement remain separate milestones. A useful release makes these boundaries easier to inspect rather than marking every ambition complete.

Sources: docs/REUSE-MEASUREMENTS-0.8.json, docs/PREPARED-0.8-VERIFICATION.json, docs/WORKSPACE-0.8-VERIFICATION.json and docs/COMPILER-BOUNDS-0.8.json.

# 21. From machine calls to graphical applications

A language becomes useful through complete paths. A quantity typed into a form should reach a checked calculation, survive a save and reopen, and appear correctly in a PDF. The same compiler should also express the process, memory and I/O operations needed underneath. Release 0.9 connects those paths in RiverFlow Studio.

The launcher, socket controller, request parser, HTML renderer, draft model and PDF writer are RF2 source. The compiler emits ARM64 machine code. The browser displays standard HTML and CSS and submits ordinary forms. There is no client script or embedded language model. This is a browser-displayed local workspace, not an AppKit widget window. The operating system and browser remain explicit platform dependencies.

## A small plan, a complete path

The invoice plan remains readable: choose the invoice-total capability, currency and tax basis points. Its calculation uses integer cents. The editor accepts decimal prices only to make human input easier. The RF2 parser converts at most two decimal places exactly; it never uses binary floating point to decide money. Quantity is a positive integer. Adding or removing a row, changing tax and exporting a worksheet all recompute the same checked totals.

Saved documents use the existing versioned format. Opening a document validates uploaded bytes rather than accepting an arbitrary server path. Exported PDFs are byte-identical to the 0.8 writer for the same document. Those checks establish compatibility of these operations, not a complete accounting or tax-compliance system. Customer records, invoice numbering, payment collection and legal invoice rules are further capabilities to specify.

## The platform boundary is an ABI

The trusted systems profile now provides syscall6 with a call number and six arguments. The compiler places the number in x16, arguments in x0 through x5 and emits the Darwin service instruction. BSD carry-set errors become negative errno values. A portable-looking function name cannot erase a platform-specific return convention. Multiple-return-register calls need explicit wrappers.

Fork exposed that distinction. An early launcher interpreted only x0 and started a second controller instead of opening the browser. Darwin also reports the child path in x1. The corrected fork_process primitive uses that flag and gives the child zero, while the parent receives the PID. An executed test makes the child exit with status 7, then checks the parent's wait result. The editor reaps its browser-opener child when closing.

The platform tests also execute PID and UID queries, negative errno and a six-argument memory mapping followed by a write, read and unmap. The native compiler's unsigned output matches the historical encoder for these fixtures. The compiler again reproduces its own image. These are precise executable checks, not a proof of memory safety, every OS call, universal compatibility or a new transistor design.

## Request state matters as much as arithmetic

The controller binds only to IPv4 loopback at a fresh port. A private nonce comes from operating-system entropy. Every edit and download checks exact Host, Origin, nonce and draft revision. A stale form refuses rather than silently overwriting another revision. POST followed by a redirect keeps refresh from repeating a valid edit. Failed validation restores both committed data and visible fields.

Idle browser preconnections caused another real failure. A blocking controller waited for an empty connection while an active form sat behind it. The fix polls the listener and eight bounded client slots. It waits only on connections ready to read and closes idle sockets silently. An active partial request has a five-second timeout. Tests retain this failure case so later changes cannot simply reintroduce it.

Saved documents and PDF downloads also require POST with current revision. Unsupported methods, duplicate request fields, oversized bodies and malformed multipart endings refuse. A content policy disallows scripts, remote assets and embedding. These controls support a private desktop controller. They do not qualify it as a public multi-user service or independently audited security system. Raw platform calls and editor launch remain outside the nine bounded MCP tools.

## Measure what changed

The final comparison uses frozen 0.8 and final 0.9 on one host. Three fresh process sets each run seven rotated trials after warmup. The editor transaction includes form encoding, POST, redirect, GET and HTML generation, but excludes browser layout and painting. It does different work from an MCP invoice call.

| Lines | MCP 0.8 µs | MCP 0.9 µs | Editor HTTP µs |
| --- | --- | --- | --- |
| 1 | 55.99 | 57.42 | 938.04 |
| 32 | 143.39 | 142.89 | 1577.17 |
| 1000 | 2718.92 | 2733.86 | 19174.67 |

The unchanged invoice operation performs similarly. The graphical path adds work. Neither result justifies a general speed claim. Prepared 0.9 medians were 52.60, 135.73 and 2742.59 microseconds for the three sizes. Host-level timing variation and different request work remain visible in the raw receipts.

The nine MCP schemas are byte-identical. Across three matched 100-call prepared sessions, encodings range from 14,583 to 14,685 o200k tokens or 14,260 to 14,362 cl100k tokens. Two pairs match; one 0.9 transcript costs 102 tokens more. Short sessions also vary by random handle spelling, including one older transcript 22 tokens shorter. There is no measured token reduction here. These are exact tokenizer counts for retained exchanges, not provider billing or the full cost of an AI building an application.

## Build the language beyond this application

The editor is an integration checkpoint. Reusable modules, structured values, owned strings, explicit error and resource lifetimes, foreign interfaces and additional code-generation targets remain language work. Each should arrive with clear semantics, working programs, refusal tests and comparisons with simpler methods. A second architecture requires its own instruction encoding and ABI qualification. Writing all of this in RF2 is a direction supported by incremental evidence, not an assertion that every existing library has already been replaced.

Sources: native/editor.rf2, native/studio/launcher.rf2, docs/PLATFORM-ABI.md, docs/EDITOR-0.9-VERIFICATION.json, docs/PLATFORM-0.9-VERIFICATION.json, docs/STUDIO-MEASUREMENTS-0.9.json and docs/STUDIO-TOKEN-FIXTURES-0.9.json. The tests preserve both successful behavior and refusal paths. The findings are useful because another developer can inspect, rerun and challenge them.

# 22. Names, records and measured reuse

Source and executable receipts for this chapter are linked from docs/LANGUAGE-MEASUREMENTS.md and docs/MODULES-TYPES.md.

A general language needs more than another application adapter. Code needs names that can be reused, data needs a shape, and a mistake at one boundary should be rejected before it becomes an arbitrary address. Release 0.10 adds local source modules and nominal records to the native systems compiler. The first complete application built with them analyses a CSV workload trace.

## A small entry with visible structure

The workload entry imports I/O, CSV and accounting modules. It constructs a Job and a Summary, reads each trace row into the job, then asks the accounting module to update the summary. Named fields replace unexplained offsets. A typed function parameter requires the declared record; another record with the same fields does not silently substitute.

```rf2
record Job(id: u64, duration: u64, deadline: u64)
record Summary(count: u64, late: u64, elapsed: u64, peak: u64)
```

The supplied three-row fixture produces three jobs, one late completion, nine elapsed ticks and a peak job duration of four ticks. The analyser also handles empty traces and up to 1,000 rows. Sixty cases compare its JSON output with independently calculated expectations. Thirteen refusal cases cover malformed rows, zero or oversized values, extra fields and exceeded input bounds. These are executed programming tests, not workplace or device measurements.

The policy is input order, with all jobs available at tick zero. A completion is late only when cumulative duration exceeds that row's deadline. This establishes deterministic accounting. It does not establish an optimal scheduler, a faster operating system or new experimental findings for another research paper.

## Reuse is a dependency contract

A library starts with module and a name. Imports use explicit local paths from the entry directory. They precede declarations, traverse in dependency order and deduplicate the same restricted path. Files share one function namespace; a collision refuses. There is no package registry, remote fetch or automatic imported execution. Thirty-two source files and sixteen active traversal levels bound the graph. Cycles, missing files and invalid relative paths refuse before output creation.

The compiler is trusted local software. Refusing absolute imports, parent traversal and final-component symlinks does not isolate the filesystem: an ancestor directory can still be an OS symlink. The image digest covers expanded source, so separate source-file hashes remain necessary for path-level provenance. Those distinctions make the evidence reviewable rather than hiding effects behind the word module.

## Record storage and lifetime

Each owned record occupies slots in the current function's stack frame. A borrowed record parameter carries its nominal type. Field updates are visible to the caller. A recursive lifetime test confirms that each invocation retains its own local fields while a deeper invocation runs.

Record returns, copying, rebinding, raw-intrinsic arguments and scalar substitution refuse. Constructors must be at function level, rather than inside conditional blocks. The first field type is a u64 machine word, and legacy systems words can also represent addresses. This is a narrow nominal boundary, not a proof of full memory safety. Nested records, strings, arrays, enums, generic types and ownership inference remain further work.

## An optimisation with a small enough claim

The optional --opt emitter recognises a numeric right operand when precedence permits a direct register path. It avoids temporary stack stores and loads while preserving operand order. Function calls and other operands use the normal path. Default compilation retains the earlier instruction path, and the compiler still reproduces its default native image through successive generations.

The following table records nine rotated fresh launches of each kernel. Each performs two million specified iterations and prints a checked checksum. Times include process start. The C and Python references compute the same checksums; they do not implement RF2's full compiler or effect contracts.

| Kernel, 2 million iterations | 0.9 ms | 0.10 default ms | 0.10 opt ms | Clang O2 ms | Python ms |
| --- | --- | --- | --- | --- | --- |
| accumulate | 14.334 | 15.185 | 11.970 | 5.349 | 181.976 |
| mix | 29.849 | 29.326 | 15.790 | 7.506 | 313.676 |
| branches | 16.071 | 15.715 | 10.243 | 5.349 | 208.129 |

The optional optimiser is faster than frozen 0.9 for these three kernels. Clang remains faster. Default 0.10 varies around the old path, including a slower accumulation result. Background host load and power state were not controlled. Three kernels on one host do not establish general superiority over C++, Java, Python, another architecture or a full application.

## Compact interaction without weaker guards

The nine MCP discovery schemas remain unchanged. Default results retain their readable summaries. An explicit compact mode omits only the redundant successful check/run summary and returns the full structured result. Errors, bounds, lowered source and other tools retain their contracts. A text-only client should use the default mode.

The complete measured session includes initialisation, discovery, one hundred successful POPCOUNT exchanges and an overflow error. It encodes to 23,877 o200k tokens in 0.9 and default 0.10, or 22,277 in compact mode: 6.70% less encoded text. This is not a provider bill, faster model inference or proof that AI generates better programs. The workload entry is 122 encoded tokens, but its full four-file source is 1,369; library and documentation context still counts.

## Learn from other languages without inheriting their claims

A pinned source review examined BAML record fixtures and MCP cleanup tests, Edict's typed pipeline and compact schema helper, DSPy's module-oriented model programming, and Zig's language reference. These offer useful design patterns. Their README claims and test files were not executed as target benchmarks. RF2's readable source, nominal checks, native emitter and bounded MCP interface are an implemented combination; no world-first novelty or universal parity is asserted.

The next useful language work is reusable strings and collections, explicit error/resource lifetimes, better diagnostics and another target. Each capability needs observable tests, failure paths and complete interaction accounting. An AI host can write RF2 and call its checked tools. That is different from claiming the executable itself contains every ability of an AI model.

# 23. Make the machine do less work

A slower result is a description of the current implementation. It does not decide whether humans or AI can build the better language. The useful question is narrower: what instructions and algorithms can be removed while preserving the promised behavior? Release 0.11 answers part of that question with an executed native optimiser.

## Diagnose before promising

The earlier emitter repeatedly moved local values through the stack and materialised Boolean loop conditions. Clang could choose registers, direct arithmetic and better loop code. Source-level compactness did not remove those machine costs. The new optional path keeps admitted locals in registers, shortens arithmetic and rotates ordinary loops. It retains a guard before the first iteration and reevaluates the condition after each completed iteration.

The calling convention matters. A leaf can use caller-saved registers because it makes no calls. Other functions preserve the selected callee-saved registers in their own stack frame. Records still own memory-backed fields, and extra locals still use stack slots. Executed tests cover eight-argument calls, recursive values, large frames, fork/wait, negative OS errors and six-argument memory mapping. Those checks qualify these paths on the tested Mac, not every platform.

## Remove moves only when the value is safe

A destructive register update is safe only when it does not erase a value the expression will read again. For that reason, the coalescer requires one leftmost read of the assignment target. Calls, fields, strings and repeated-target expressions retain their usual path. The emitted instruction classes are checked as well. An adversarial test found a missing immediate-comparison class; the compiler refused to emit that program until the handler was corrected.

A final u32 mask permits word-sized arithmetic for a restricted polynomial and bitwise expression. The lower 32 bits do not depend on the discarded high bits for those operations. Division, right shifts and comparisons do not have that property, so they are excluded. Edge tests retain large constants, overflow, zero extension and alias-sensitive cases. This is an exact local rule, not a claim of general memory safety or an unrestricted proof system.

## A whole loop can sometimes become arithmetic

Consider a serial unsigned loop that adds index AND mask to a total and increments index by one. When mask=P-1 and P is a power of two, the masked values repeat in complete periods. That structure allows an exact prefix sum.

```text
r = n mod P
F(n) = floor(n/P) * P*(P-1)/2 + r*(r-1)/2
```

For start<bound, the accumulator changes by F(bound)-F(start), modulo 2^64, and the final index is bound. If the initial condition is false, nothing changes. The implementation limits the period exponent to 32 so the residual product fits in a machine word. The full-cycle product may wrap exactly as the original accumulator does.

The compiler checks the pure two-statement body, comparison, mask and distinct variables before selecting the rule. A runtime-local bound is allowed; the rule does not look for a benchmark name or one fixed iteration count. Different masks, inclusive comparisons or extra effects retain their ordinary loop. This is fixed-size work for one eligible linear recurrence, not exponential acceleration of arbitrary programs.

## Challenge the implementation and the benchmark

The guarded reducer passed 240 cases checked by direct iteration, 80 large integer cases checked with arbitrary-precision arithmetic, and 60 fallback cases. The instruction selector passed 2,205 edge cases against an independent integer expectation and 0.10. Another 180 cases challenge aliasing, calls, spilled locals, recursion and control flow. Side-effecting conditions are checked separately. Narrowing has 340 adversarial cases. Existing computation, application, compiler-generation and protocol suites remain separate checks.

The next table uses the same runtime start, bound and seed for each variant. C is compiled with O3 and the native CPU setting. Seven rotated fresh-process trials follow a retained cold/warmup launch. Times include process startup, and every output is checked.

| Runtime-input workload, 20 million steps | RF2 0.10 ms | RF2 0.11 ms | Clang O3 ms |
| --- | --- | --- | --- |
| periodic | 24.878 | 1.842 | 3.841 |
| mix | 57.312 | 22.496 | 22.232 |
| branches | 22.486 | 20.216 | 6.501 |

The eligible reduction has a clear improvement over the old RF2 loop and the loop-based C baseline in this run. The mixed-arithmetic point medians are close. The branch-heavy case remains substantially slower than Clang. An equally specialised C formula measured 2.367 ms for the largest periodic case; smaller cases reverse that ordering. At this scale, process startup obscures the cost of the formula itself. It would be wrong to turn those short timings into a universal language victory.

## Connect research through evidence

A research idea becomes useful when its proposed mechanism reaches working code and survives a stronger comparison. Here, the transferable method is explicit candidate guards, retained fallbacks, independent output checks and honest reporting of remaining gaps. Register allocation and algebraic strength reduction are known classes of optimisation. The contribution is their tested implementation and boundaries in RF2, not a claim of new mathematics or automatic academic approval.

The next branch-heavy work needs inspection of generated instructions and vectorisation opportunities. Broader languages still need collections, resource and error semantics, diagnostics and more targets. AI can help write, test and challenge that work. Its assistance is not a substitute for a measured result.

Sources and executable receipts: docs/NATIVE-OPTIMIZATION.md and docs/OPTIMIZER-MEASUREMENTS-0.11.json. The ABI reference is Arm AAPCS64, section 6.1.1; LLVM's vectorisation documentation describes its diagnostic remarks. These references are engineering specifications, not evidence that RF2 already inherits another compiler's capabilities.

# 24. Collections with a stated boundary

The checked-array capability is included in release 0.12. The earlier 0.11 compiler does not implement it.

A language becomes more useful when a program can keep several values together, pass them to a helper and change them without exposing their memory address. RF2's first checked collection is deliberately small: a fixed number of unsigned machine words.

```rf2
array Readings(u64, 64)
```

This declares a type. A function creates its own value with `let readings = Readings()`. Every cell starts at zero. `readings[3]` reads one cell, `set readings[3] = 42` changes it, and `readings.length` returns the fixed capacity. A populated count is separate from capacity. A sixty-four-cell array might contain seven actual observations; the other cells do not become observations because memory exists for them.

A helper can accept `readings: Readings`. The type annotation matters: a different array type with the same capacity is still different. The helper borrows the caller's collection and can update its elements. It cannot return the array as a scalar or send it to a raw pointer operation through the typed call boundary.

Owned arrays live in the current function's stack frame. Recursive calls have separate storage. The current compiler refuses ordinary array copies, rebinding and escaping returns. These rules are narrower than a full ownership system. The trusted systems profile still offers raw operations, and this feature does not make an arbitrary program memory-safe. It also does not define concurrent mutation.

## Check before performing the access

An index must be below capacity. The compiler emits an unsigned comparison before calculating the element address, in both default and optimized builds. If the index is out of range, the program writes `RF2 bounds` and exits with status two.

For a write, the check happens before evaluating the value on the right. That order prevents an invalid assignment from first running an unrelated side effect. A test deliberately puts a printing function on that right side and verifies that it never executes when the index is invalid.

The compiler shares one error path across the image. Successful checks fall through without visiting that path. Sharing the diagnostic avoids inserting a copy beside every access; it does not eliminate the checks or prove that their cost is free. Recoverable error values are a future language step. The current failure ends the process.

## Prove the feature in a complete program

The latency-summary example takes up to 128 supplied unsigned samples, parses them, sorts the populated prefix and prints JSON. It is written in RF2, including the typed collection module and integer output. It does not measure a clock. A caller must supply real measurements if the resulting summary is intended to describe real latency.

The example defines its statistics precisely. The lower median selects the lower middle value for an even count. The p95 rule selects the value at the ceiling of 95 percent of the count, with the corresponding zero-based position. Neither rule is left to the reader to infer from the word “percentile.”

The test compares 160 complete executions with an independent sorted-integer calculation, including equal values, maximum accepted samples, a single sample and full capacity. Invalid input tests cover empty, negative, fractional, malformed, oversized and too many values. Other tests exercise borrowing, recursive frames, zero initialization, wrong nominal types and out-of-range reads and writes.

## Measure the right comparison

The measurement keeps the old raw-buffer implementation, a C insertion sort and C qsort visible. The raw buffer has different lifetime and bounds semantics. Qsort changes the algorithm. Those are useful competing implementations, but their times cannot isolate the price of one bounds check.

Seven rotated trials per variant and input retain their cold/warmup observations and verify every output. At these small input sizes, total process times sit near the launch floor and their ordering varies. The evidence demonstrates a working checked collection and complete application. It does not establish a universal speed advantage.

The next useful steps are text and byte semantics, recoverable error values and explicit resource cleanup. Tasks will also need rules for ownership, sharing and cancellation. Each should reach the same standard: a defined contract, a real program, independent expected results, meaningful failure cases and reproducible measurements. That is how one readable language can grow toward larger systems without replacing missing mechanisms with promises.

Executable sources and evidence: docs/CHECKED-ARRAYS.md, tests/standalone/arrays_verify.py, docs/ARRAYS-VERIFICATION.json, tools/measure-collections.py and docs/COLLECTIONS-MEASUREMENTS.json.

# 25. Bytes, text and a recoverable failure

Release 0.12 lets a program report a failed byte operation and continue processing later valid input.

## Give bytes a real type

```rf2
array Packet(u8, 128)
```

This is a packed byte array. Each indexed read produces a value from zero through 255. Every ordinary indexed write checks both the index and value. The array is zero-initialized and owned by the current function's frame. Typed helpers borrow it without receiving an untyped memory address.

The compiler now recognizes read_bytes and write_bytes for this type. The caller supplies a descriptor and count. A request larger than capacity fails before the OS operation. A successful result is the actual count, which may be short. A negative result represents failure. The compiler does not silently choose a file, connect to a service or turn an AI request into authority over a user's machine.

Byte I/O belongs to the trusted systems profile on Apple Silicon macOS. Bounded Core and MCP permissions do not expand.

## Make the result explicit

The byte module defines an Outcome record containing code, value and offset. A helper writes all three fields on every operation. The caller checks code before using value. That rule avoids treating yesterday's successful value as today's failed result.

The library covers byte get/set, I/O and decimal parsing. Range, value and I/O failures have distinct statuses. A later valid operation can still succeed.

This is recoverable library behavior. It is not a general exception system or a tagged return type. The compiler does not yet require callers to inspect the record. Those stronger language features need their own syntax, type rules, failure cases and implementation.

The decimal parser accepts ASCII digits within an explicitly supplied range. Before multiplying by ten, it checks whether the next digit can fit in u64. An overflowing number returns an error offset rather than wrapping into a plausible successful value. Empty, signed, fractional and malformed input have stated outcomes.

## Keep text across a read boundary

A file read is not a character boundary. A four-byte UTF-8 sequence may begin at the end of one chunk and finish in the next. The decoder keeps its pending state between calls. It rejects invalid starts, continuation errors, overlong encodings, surrogates and values above the scalar range. At actual EOF it also checks for an incomplete sequence.

The audit reports errors and continues. A non-continuation byte is reconsidered as a possible new start, so a malformed prefix does not swallow a following valid letter. Its diagnostic grouping is documented separately from Unicode replacement rules. The program writes no repaired version of the input.

Counts need definitions. Combining marks count as separate scalars. LF counts as a newline; ASCII whitespace and NUL separate words. Normalization and grapheme segmentation are not implemented.

The encoding reference is Unicode 17, section 3.9 and table 3-7. Native tests compare validity and first-error position with an independent strict decoder. Tamil and emoji are included, as are malformed sequences and characters crossing the byte-buffer boundary.

## Finish the resource path

The complete audit application accepts stdin or one explicit file path. A named file is opened read-only, processed, then closed on normal return, read failure or the one-megabyte limit. Stdin is borrowed and left open. A same-process test verifies that the owned descriptor is no longer usable after each tested return path.

This is explicit control flow, not a general resource-ownership system. A caller-selected special file may still block. A short output write still needs caller handling. These limits belong in the contract rather than being hidden behind the word secure.

## Six foundations, six next gates

This sprint delivers packed bytes, bounded byte I/O, recoverable status helpers, streaming UTF-8 validation, checked integer parsing and the audit application with cleanup. Each has executable tests. There is no new speed or token-saving result to report for this increment.

Next are typed results, byte/text views, owned resources, growable collections, tasks/cancellation and a second-platform proof. Each needs implementation and acceptance tests.

Sources, primary specifications and reproduction: docs/TEXT-BYTES.md. Executed cases: docs/TEXT-BYTES-VERIFICATION.json.

# 26. A result that must be handled

RF2 began with a practical aim: one readable language connecting human or AI intent to inspectable native execution. A program's failure path belongs in that agreement. Release 0.13 makes two parts more explicit: how a function reports a result, and how a helper reads a window of bytes without changing its owner.

## Declare the alternatives

```rf2
result Number(u64, u64)
fn checked(n): Number
 if n == 0
  return err(1)
 end
 return ok(n)
end
```

This is a nominal type with two variants. The initial payloads are unsigned machine words. The function must explicitly return ok or err and end with a root-level return. It cannot silently fall through and manufacture a successful zero. This is a conservative syntactic rule, not complete control-flow analysis.

At the call site, handle requires both arms in fixed order. Each arm has an immutable payload name, scoped to that arm. An ordinary scalar assignment or discarded do statement cannot hide the result. Indexing or reading a property cannot turn its tag into a value.

Exhaustiveness means both variants appear. It does not prove that an error branch does useful recovery or distinguish every numeric error carried by err. Structured payloads, generic result values and automatic propagation remain further work. The current facility is a checked native function protocol, not an exception system.

## Close an old admission gap

Independent programs found that the earlier compiler admitted scalar reads before initialization, including names declared only in a false branch. Default and optimized executions could then produce different outputs. Those values were not a meaningful benchmark result.

The correction checks readiness and scope through the ordinary and optimized paths. One in-place path initially escaped the new check: a self-referential declaration could update an uninitialized register. That case was retained, corrected and tested again. A block-local declaration is now unavailable after its block; initialize an outer local before assigning to it conditionally.

This matters for result handling too. A success payload must not become readable from the error arm, or survive by name after the handler. A compiler feature is incomplete if its fast path ignores the same rule its ordinary path enforces.

## Read through an immutable window

A view declares which byte-array type it can borrow. Its constructor selects a start and count without copying the underlying bytes. Admission uses subtraction after checking the start, avoiding unsigned addition overflow. Reads check the view length rather than the owner's full capacity. An empty window at the end is valid.

Descriptors remain in the current function's frame. They cannot be returned, passed, copied or rebound. Several overlapping windows can coexist, but after the first view is created the function may perform no calls or array element updates. That includes mutation through another parameter that might alias the owner. The freeze ends when the function returns.

This deliberately conservative rule avoids pretending that a general borrow checker already exists. The caller can perform I/O, call the read-only parser, then resume mutation after that parser returns. More composable read-only calls and shorter borrow lifetimes need additional analysis.

Byte safety is not a Unicode promise. A chosen window may split an encoded character or include unused initialized capacity. Encoding, logical content length and character boundaries need their own validation. These views are suitable for byte-based text parsers; they are not normalized strings.

## Use both in a real document task

The number-audit application reads rows of unsigned decimal numbers. Its parser creates an immutable byte view and returns a typed success or error. Its caller must handle both. A malformed row is recorded, and later valid rows still contribute to a checked sum. Oversized rows, numeric overflow and accumulated-sum overflow have stated outcomes.

File opening and input processing also use result-returning functions. The app closes an owned descriptor after processing and leaves borrowed stdin open. Input limits and I/O failures identify partial statistics. None of this makes cleanup automatic across arbitrary programs.

The example input 12, bad, 30 on separate lines yields two accepted rows, one rejection and sum 42. These are programming fixtures, not a workplace or participant study. Randomized tests compare the complete output with independent integer calculations, including later recovery after errors.

## Preserve the uncomfortable evidence

Two actual agent tasks authored programs and reviewed the source. The parent reran their cases against the final binary. Separate suites check missing arms, result coercion, binding scope, aliases, view overflow and frame exhaustion. The original initialization admissions and the later optimizer mistake remain in the engineering record.

WhatIF's source heuristic did not support RF2 files and inspected none. That is an unsupported coverage result. Native program checks supplied separate executed evidence; no HTTP campaign or universal security pass is claimed. AI reviewers are not human peer reviewers.

The next work is structured result payloads, validated text views, composable immutable calls, owned resources, growable storage and task semantics. Each must reach the same standard: a clear contract, working programs, independent expected results and preserved failures. No new speed or token-saving conclusion follows from this release.

Specification and reproduction: docs/RESULTS-VIEWS.md. Application: examples/number-audit. Verification receipts and reviewed fixtures are linked from that contract.

# 27. Text people can read, resources programs release

Readable programming needs real text and predictable file lifetimes. Tamil, combining marks, emoji and malformed input all matter. Early returns should also release a registered named input file.

Release 0.14 adds validated Unicode scalar views and deferred close actions. The compiler checks their contracts and emits native instructions.

## Bytes and characters need different names

```rf2
array Bytes(u8,255)
textview Text(Bytes)
fn count(data:Bytes,n)
 let text=Text(data,0,n)
 return text.length
end
```

The constructor chooses a byte range and validates that range as strict UTF-8. It rejects truncated sequences, overlong encodings, surrogate values and values beyond U+10FFFF. NUL remains valid text. The surrounding owner may contain unrelated malformed bytes; only the chosen span is the text value.

A text view has two useful lengths. Its byte_length property is the encoded byte count. Its length property is the Unicode scalar count. Indexing returns a scalar value. A displayed family emoji can contain several scalars; a combining mark is also a scalar. This interface does not count graphemes or normalize words. Calling every visible shape a character would hide a distinction the program needs.

The descriptor does not copy source bytes. It stays in the function frame and cannot escape or mutate its owner. Existing view freezes still prohibit ordinary calls and array element updates after construction. This conservative restriction is less convenient than a complete borrowing system, but it has a contract that can be tested. Scalar indexing scans from the start and carries no speed claim.

Invalid UTF-8 construction is a fatal process trap, just as an invalid view range is a bounds trap. A document tool needing recovery first validates bytes and then constructs the view. Recoverability is an application decision with an explicit checked path, not a promise hidden behind a constructor.

## Capture once, release when returning

```rf2
fn inspect_file(path)
 let fd=open(path,0,0)
 if fd>>63
  return 1
 end
 defer close(fd)
 return 0
end
```

The defer statement captures the descriptor when reached. An ordinary function return automatically attempts the close. Captures run in reverse registration order, and early returns before a registration leave it unarmed. A shared native epilogue preserves both registers of a typed result while performing cleanup. Scalar fallthrough also runs registered actions.

The first form supports close only, at function level, with at most sixteen registrations. It does not run arbitrary callbacks or establish linear ownership. A failed close does not replace the function's authored result. Fatal traps, direct process exit and signals bypass these epilogues. A raw descriptor manually closed and reused can still refer to another resource when the deferred action runs. These limits belong beside the feature, not in an invisible footnote.

## A multilingual document tool

The unicode-lines application processes stdin or one named file. It reports accepted and rejected lines, Unicode scalar counts, Tamil-block counts and a fingerprint over accepted scalars. Malformed rows are rejected without preventing later valid rows from being processed. A separate strict prevalidator checks bytes before a text view is constructed. The view then supplies scalar indexing for the actual summary.

Opening and reading have typed outcomes with exhaustive handlers. A named descriptor has a deferred close; borrowed stdin does not. Tests inspect descriptor validity in a still-running process, including early error returns, rather than relying on the operating system to close files after termination. The input and line limits, partial statistics and output failure limitations are explicit in the application contract.

## Keep failures as part of the story

Independent tests found that the first candidate rejected a valid byte-order mark. A wrong native shift instruction and an incorrect error-string constant were corrected. A later boundary review found a maximum-index collision with the decoder's internal validation mode. An explicit scalar bounds check fixed it. Those failed candidates remain in the local evidence record.

Agent-authored programs compare native behavior with independent strict UTF-8 decoding and file-descriptor expectations. These are finite checks, not human peer review or a compiler proof. Existing compiler and MCP regressions also remain required.

Next are typed ownership, observable cleanup errors, structured results, composable immutable calls and growable storage. No new speed or token-saving conclusion follows.


# 28. One owner, visible cleanup failures

A short program is useful only when its failure behavior is understandable. The previous release could defer a close, but the file descriptor remained a copyable integer and a failed cleanup could disappear. Release 0.15 adds a checked owned-file path with visible error outcomes.

## Open into an owner

```rf2
result IO(u64,u64)
resource File(IO)
array Bytes(u8,16)
fn inspect(path):IO
 own file=File(path,0,0)
 let data=Bytes()
 let count=0
 handle read_owned(file,data,16)
 ok n
  set count=n
 err cause
  return err(cause)
 end
 return ok(count)
end
```

The constructor opens the file internally. An owner exists only after successful acquisition. Open failure immediately returns an error through the function's cleanup epilogue; earlier owners still receive their cleanup attempts. The owning function must declare the same result type as the resource.

An owner cannot be copied into an ordinary local, returned, placed in a record or passed to another function. It exposes no descriptor property. The checked I/O operations borrow it for one call and return a typed result. Byte counts above the array capacity return an error without issuing the operation. Short and zero I/O remain outcomes the caller must handle.

This initial resource form implements files opened through the platform interface. It is not arbitrary destructors, heap ownership, transferable handles or an async lifetime system. Helpers can still format and parse borrowed arrays without receiving ownership.

## Consume once, preserve the important error

Explicit release returns a handled result and consumes the owner on success or failure. Automatic cleanup is disarmed before the close attempt. A later source use refuses. Branch consumption is conservative; repeated execution of a release in a loop has a runtime guard, so it cannot close a descriptor that has since been reused.

If the function returns normally without explicit release, its epilogue attempts close in reverse registration order. A failed automatic close changes an otherwise successful result into err(65536+errno). A primary error is preserved, and only the first cleanup failure is reported. Legacy deferred closes retain their old best-effort behavior.

A failed close is not blindly retried: the numeric descriptor may have been reused. Trusted raw operations remain available and can deliberately violate the checked ownership contract. Fatal process traps, explicit exit and signals also bypass ordinary epilogues. These limits prevent a finite checked feature from being mistaken for total process isolation.

## Read a real file as bytes

The native hex application accepts a named read-only input and prints fixed rows: offset, hexadecimal bytes and an ASCII gutter. It uses owned acquisition and typed reads, and it handles short output writes explicitly. Tests compare every output byte with an independent formatter, including all 256 byte values and incomplete final rows. Input is unchanged.

In-process checks examine descriptor reuse after successful processing, a read error and an output error. Separate ownership probes perform actual writes followed by reopened readback, force cleanup errors, preserve primary errors and repeat hundreds of lifetimes. These are executed software fixtures, not a claim about all operating-system failures.

The byte reference lists every ASCII code with decimal and hexadecimal forms. RF2 already supports hex literals, bitwise work, native machine-code emission and useful file applications. That does not mean every Java, Python, C++ or assembly workflow is complete. Growable data, floating point, concurrency, more targets and a broader library remain foundations to build and qualify.

## Test the right layer

Agents wrote independent ownership and application probes. WhatIF separately checked a disposable Studio instance with bounded HTTP requests and verified the evidence. Its source heuristic did not parse RF2, and HTTP success does not prove compiler ownership. Each observation belongs to the layer actually tested.

The public capability map, contracts and release receipts make that distinction visible. No new speed, token, energy or hardware advantage follows from this chapter. Next are transferable ownership, richer error data and growable storage, with reproducible applications and failures as their acceptance gates.

# Appendix A. Commands and interfaces

Native standalone, no Node or npm required:

```sh
./rf2 status
./rf2 check examples/compact/sum.rf2
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
./rf2 expand examples/compact/sum.rf2
./rf2 lower examples/sum.flow
./rf2 mcp
```

The following commands are for the retained reference-development tools only. They require Node 22 and npm dependencies:


```sh
node bin/rf2.mjs check examples/sum.flow
node bin/rf2.mjs run examples/sum.flow '[1,2,3]'
node bin/rf2.mjs compile examples/sum.flow program.json
node bin/rf2.mjs emit-c examples/sum.flow program.c
npm test
node tools/benchmark-native.mjs
```

The native plugin launches an existing binary from RF2_BIN or output/bin/rf2. It performs no automatic build or Node fallback. Register the plugin or direct MCP server once; the client controls slash-command appearance.

Native tools cover status, checking, execution, kernel lowering and attendance export. The separate JavaScript reference retains batching, C emission and the SFE catalog. Consult the repository schemas for their exact arguments and effects.

# Appendix B. Native status codes

| Status | Meaning | Result behavior |
| --- | --- | --- |
| 0 | Successful evaluation | out receives the u32 result |
| -1 | Invalid ABI, capacity, alignment or overlap | Evaluation does not begin |
| -2 | Checked arithmetic overflow | out remains unchanged |
| -3 | LOAD beyond supplied capacity | out remains unchanged |
| -4 | Count exceeds the source loop limit | out remains unchanged |
| -5 | Execution work limit reached | out remains unchanged |

For a valid ABI and an evaluation failure, work may receive the consumed event count. The caller owns valid output storage and stable input. These checks do not establish arbitrary pointer validity or a security sandbox.

# Appendix C. Release evidence snapshot

The table below retains the historical 0.3 C-backend experiment. It does not measure the native 0.6 IR runtime or newly lowered kernels. These descriptive observations come from one host; raw trials remain in the repository. A later performance claim needs its own matched experiment.

{{EVIDENCE_TABLES}}

# Appendix D. Further reading and source boundaries

The RiverFlow Core specification, source, tests and benchmark records are the primary references for this edition. External sources below explain the tools and platform responsibilities; they do not independently validate RiverFlow.


1. RiverFlow RF² source and specification. https://github.com/starkfiber/RiverFlow

2. RiverFlow Core specification. https://github.com/starkfiber/RiverFlow/blob/main/docs/SPEC.md

3. Model Context Protocol specification. https://modelcontextprotocol.io/specification/2024-11-05

4. MCP TypeScript SDK server documentation. https://ts.sdk.modelcontextprotocol.io/server

5. Clang AddressSanitizer documentation. https://clang.llvm.org/docs/AddressSanitizer.html

6. Clang UndefinedBehaviorSanitizer documentation. https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html

7. Android platform architecture. https://developer.android.com/guide/platform/

8. Embedded Swift documentation. https://docs.swift.org/latest/documentation/embeddedswift/

9. Git repository and attribution documentation. https://docs.github.com/en/repositories

This book does not reproduce private thesis manuscripts, participant data, device calibration, credentials or recovered third-party papers. Research connections are stated as proposed directions unless this edition identifies an actual executed result.

Native compiler hash algorithm reference: NIST FIPS 180-4, https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf.
