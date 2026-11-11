# RiverFlow RF²
## Ideas into checked computation

Ilangkhumanan Thirunavokkarasu

Stark Fiber Enterprise

First edition, revised · November 2026 · Package 0.4

# About this edition

RiverFlow is a language in active development. This book describes a small language that runs, a compiler path that can be inspected, and a way to connect research questions to evidence. The complete original examples use RF2_U32_CORE_V0. The standalone 0.4 addition has a separate RF2_COMPACT_V1 front end and an explicitly distinct RF2_SYSTEM_A64_V1 implementation profile. The profile matters more than the age of the book: another dialect may use familiar words while giving them different meanings.

The author’s ambition is to make programming understandable, useful and durable. Those aims guide the work; they are not measurements. This edition does not claim universal compatibility, new semiconductor technology, independent academic approval or a language that will survive a million years. A reader should be able to reproduce a claim without agreeing with the ambition behind it.

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

For the standalone 0.4 path on Apple Silicon macOS 14 or newer, users run a single executable. Node, npm, Python and C++ are not runtime requirements. The executable uses macOS system interfaces; it is not an operating system of its own.

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

The result is 15 with 18 abstract Core work events. These events are not processor cycles. Chapter 15 explains the native implementation, its tests and its four-operation boundary. General Core helpers and arbitrary admitted statements still use the reference tools described below.

Developers building the standalone from source currently use a small Python seed and the macOS signing utility. The seed writes AArch64 instructions and the executable container directly, without a C/C++ compiler, assembler or linker. This is a trusted bootstrap, not self-hosting.

The remaining detailed examples in Chapters 2 through 14 teach the original Core profile. For those reference-development exercises only, install Node 22 and the repository's pinned npm dependencies. The browser playground also retains that reference interpreter. These developer tools are distinct from the standalone runtime.

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

For this general Core reference exercise, save that text in first.flow and run it with an empty array using Node 22. The compact standalone does not accept arbitrary Core source. You can check it without executing it, or emit a JSON intermediate representation for inspection.

```sh
node bin/rf2.mjs check first.flow
node bin/rf2.mjs run first.flow '[]'
node bin/rf2.mjs compile first.flow first.json
```

The compile command writes checked JSON IR. It does not produce a native executable. The emit-c command, introduced later, writes C source. A clear distinction between these outputs prevents a common mistake: treating a successful build step as proof that an application ran on its target device.

The website runs the same interpreter in a browser worker. It does not send source or arrays to an inference service. Edit the array, then edit the program. When an error appears, read it as information about the contract rather than a judgment about the person writing the code.

Exercise: replace 500 with 7 and 20 with 11. Predict the result before running. Then change ADD to an unsupported operation. A useful system should refuse the second change rather than quietly choose some other meaning.

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

Package 0.3 adds C11 source emission. This is a real implementation path: checked RiverFlow source becomes C, which a separate compiler can turn into host machine code. It is not a claim that RiverFlow is self-hosted or that the generated code has run on a phone.

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

The language tools report the current profile, check source, evaluate an input, evaluate a batch using one preparation, and emit C text. The public SFE bridge lists a fixed repository catalog, inspects an entry, retrieves its pinned root README, exposes proposed research links and calculates ratios from supplied measurements.

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

The seed itself is written in Python. This is why the result is a native bootstrap milestone, not a self-hosted language. Saying everything is RiverFlow would currently hide a real dependency at build time. A future native compiler for the systems profile must reproduce and qualify its own output before that claim can change. Hardware instruction semantics, the operating system and code signing also remain external contracts.

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

These are four separate programs, not one combined source file. The header and operation are required; whitespace separates their five tokens. The input array and optional prefix count are supplied separately. Unknown words, extra instructions, hidden effects and general Core source reject. The implementation does not claim to understand unrestricted natural-language requests.

The expand command prints the exact full Core source for the selected operation. That makes short notation inspectable: a compact sum expands to initialization, a bounded loop, input loads, additions and a return. The native implementation executes its admitted reduction using ARM64 instructions. It does not invoke a model or interpret each request through Python or Node.

## Evidence before adjectives

The executable passed 1,016 differential cases against the retained JavaScript reference and independent integer arithmetic. Successful values, work counts and overflow outcomes agreed. The tested corpus includes zero-length input, prefixes, maximum u32 values, full-width seeded words, smaller values and the maximum 65,536-word array.

Separate negative and parser checks challenge invalid data, count/capacity errors, unsupported profiles, malformed JSON, duplicate keys including escaped spellings, UTF-8 and surrogate handling, request-size and nesting limits, and recovery after a refused request. Seeded byte mutations test the actual native process. A separate official MCP SDK client exercises discovery, success, overflow refusal and the next successful call. The executable also runs with its command search path disabled, so launching another language runtime cannot explain the result.

The evidence is in docs/STANDALONE-VERIFICATION.json and the executable-level tests. It is not an independent audit, formal verification or proof that a hand-built parser has no defects. No new speed or energy measurement is asserted. The earlier C-backend timing table belongs to that earlier experiment, not this standalone executable.

## What is still open

The standalone currently targets Apple Silicon macOS only. It exposes three native tools, not all ten reference tools. General Core helpers, arbitrary admitted statement sequences, the C emitter, batch execution and public-repository research tools remain in the reference implementation. There is no automatic phone installation, wireless qualification or arbitrary application-generation capability.

The next foundation is to migrate more Core behavior, qualify another target, review the machine encoder independently, and implement the seed in the native systems profile. Compact service plans then need real versioned implementations, explicit permissions and acceptance tests. A short command should save repeated description without concealing unimplemented work.

Hundreds of tokens rather than millions remains a hypothesis. Measure matched tasks from start to finish, including documentation, schemas, capability creation, tool responses and repairs. Count failures. Report first-use construction separately from reuse. A short source listing alone establishes neither task-level token savings nor better software.

# Appendix A. Commands and interfaces

Native standalone, no Node or npm required:

```sh
./rf2 status
./rf2 check examples/compact/sum.rf2
./rf2 run examples/compact/sum.rf2 '[1,2,3]'
./rf2 expand examples/compact/sum.rf2
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

The native Codex plugin now launches an existing RF2 binary, configured by RF2_BIN or output/bin/rf2. It does not install npm dependencies or fall back to Node. The older JavaScript MCP server remains a separate development reference. Other MCP clients can launch plugin/launch-mcp.sh over stdio. Use one registration route per client to avoid duplicated servers. The client controls whether the rf2 skill appears as a slash command; the package does not force a UI convention.

The native tools are rf2_status, rf2_check and rf2_run for Compact V1. The older reference language tools additionally include rf2_run_batch and rf2_emit_c. Only the JavaScript reference supplies the SFE research tools: sfe_repositories, sfe_repository, sfe_repository_document, sfe_research_map and sfe_compare_measurements. Their schemas define inputs; none grants a device capability or executes emitted C.

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

The following tables are generated from retained release receipts when this book is built. They are descriptive observations from one host. Raw trials remain in the repository. A later edition must regenerate its snapshot rather than quietly reusing a favorable old result.

{{EVIDENCE_TABLES}}

# Appendix D. Further reading and source boundaries

The RiverFlow Core specification, source, tests and benchmark records are the primary references for this edition. External sources below explain the tools and platform responsibilities; they do not independently validate RiverFlow.


1. RiverFlow RF² source and specification. https://github.com/starkfiber/RiverFlow

2. RiverFlow Core specification. https://github.com/starkfiber/RiverFlow/blob/main/docs/SPEC.md

3. Model Context Protocol specification. https://modelcontextprotocol.io/specification/2026-07-28

4. MCP TypeScript SDK server documentation. https://ts.sdk.modelcontextprotocol.io/server

5. Clang AddressSanitizer documentation. https://clang.llvm.org/docs/AddressSanitizer.html

6. Clang UndefinedBehaviorSanitizer documentation. https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html

7. Android platform architecture. https://developer.android.com/guide/platform/

8. Embedded Swift documentation. https://docs.swift.org/latest/documentation/embeddedswift/

9. Git repository and attribution documentation. https://docs.github.com/en/repositories

This book does not reproduce private thesis manuscripts, participant data, device calibration, credentials or recovered third-party papers. Research connections are stated as proposed directions unless this edition identifies an actual executed result.
