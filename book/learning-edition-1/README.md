# RF2 From Zero

## First Learning Edition

**Ilangkhumanan Thirunavokkarasu · Stark Fiber Enterprise**  
Learning edition 1.0 · November 2026 · Teaching baseline: Workbench 0.38

An original beginner's guide to RiverFlow. An independent technical edition, prepared with AI assistance in writing and engineering review. This is not an edition of, or an affiliation with, the commercial For Dummies series. The repository MIT licence applies to this original material and code. The uploaded books informed the capability comparison; their text, branding and examples are not reproduced here.

**The promise:** understand the current language, make a program work, inspect a failure and build toward a useful application. This edition covers the supported learning journey and introduces the wider systems work. It does not claim every language feature or future platform is implemented.

[Readable HTML edition](RF2-From-Zero.html) · [Test record](VERIFICATION.json) · [Evolution specification](../../docs/RF2-EVOLUTION.md)

## How to learn from this book

Read chapters 1–6 first. Type the small examples instead of pasting a large application. Predict the result, run it, then change one thing. Chapters 7–12 introduce the systems language and libraries. Chapters 13–17 use real applications and failure exercises. Chapters 18–24 explain targets, evidence, UI design, project scenarios and the wider direction.

You need an Apple Silicon Mac for the qualified native package. A browser provides the graphical display. An AI assistant is optional. There is no embedded AI model in the executable. The input examples are teaching data, not records of real customers or research participants.

Each lesson identifies what to do, what to observe and what that observation does not establish. Exercise answers appear in chapter 20. Code in this book uses the existing syntax, not the proposed braces/import/var syntax from an earlier architecture sketch.

## 1. What a program promises

A program is a set of precise instructions. A booking program might promise to reject two reservations for the same room and time. A number program might promise to add a list without silently overflowing. Good software also tells you what happens when it cannot keep that promise.

RF2 has two important routes. **Core** is a small, bounded computation language. It reads the supplied numbers and produces a result. **Systems RF2** can use files, memory and operating-system operations. It is more powerful and requires more care. Familiar-looking words do not mean both routes have the same permissions or number rules.

The compiler turns supported systems source into machine code for a particular target. The runtime can execute checked Core instructions. These are different execution paths. Neither makes an unsupported library appear automatically.

**Checkpoint:** explain why adding numbers should not require permission to edit your files.

## 2. Get a working tool before learning syntax

Use the repository's [Workbench download guide](../../dist/workbench-0.38/README.md). Compare the downloaded archive with its published SHA-256 value, extract it and follow the normal macOS security process. A matching checksum identifies bytes; it does not independently establish publisher trust. This development bundle is ad-hoc signed, not a notarized installer.

Open Terminal in the extracted folder. Terminal is a text interface for starting programs. Run:

```sh
./rf2 status
```

The leading `./` means the executable in this folder. Workbench 0.38 contains the unchanged runtime reporting 0.17.0. The bundle edition and runtime contract version are different identifiers. That is not an instruction to fetch a different executable.

If your Mac cannot execute the file, stop and inspect the package, architecture and OS message. Do not disable security protections just to get through a lesson. Intel Mac, Windows and Linux desktop execution are not qualified by this package.

**Checkpoint:** identify your bundle version and runtime version separately.

## 3. Your first working program

Use Studio first if you have never saved source text. If you use TextEdit, choose Format → Make Plain Text before saving; use the exact filename `sum.flow`, not `sum.flow.txt` or an RTF document. Create that plain-text file containing:

```flow
rf2 v1 checked
sum input
```

There are two nonempty lines. The first selects a compact checked program. The second asks for the sum of the supplied input. The `.flow` extension identifies source text; it is not an executable by itself.

Run this from the folder containing the native runtime:

```sh
./rf2 check /absolute/path/to/sum.flow
./rf2 run /absolute/path/to/sum.flow '[1,2,3]'
```

Replace the absolute source path with your own file. The quotes keep the input array together as one Terminal argument. The result object contains `value` equal to 6, along with accounting information. Do not mistake an abstract step count for milliseconds or CPU instructions.

**Exercise:** change the input to `[2,4,6]`. Predict the value before running it.

## 4. Four useful compact operations

Keep the first line and replace only the second:

| Operation | Input | Expected value |
| --- | --- | --- |
| `sum input` | `[1,2,3]` | 6 |
| `squares input` | `[1,2,3]` | 14 |
| `bits input` | `[0,1,3,255]` | 11 |
| `nonzero input` | `[0,8,0,2]` | 2 |

Squaring multiplies each number by itself before adding the results. Bits counts the set bits: 255 has eight, 3 has two and 1 has one. Nonzero counts entries unequal to zero. None of these operations opens a file or contacts a website.

The input array uses JSON notation: square brackets, commas and whole numbers. A string such as `"three"` is not a valid u32 number input. The checked number range is 0 through 4,294,967,295.

**Exercise:** explain why `bits input` over `[7,8]` returns 4, not 15.

## 5. Overflow is a design choice

A fixed-width integer has a limited range. In checked mode, a sum that exceeds the supported range is refused. In wrapping mode the arithmetic wraps around that width. Choose the meaning before choosing the implementation.

Try the checked sum with `[4294967295,1]`. Expect refusal, not a successful value. In a separate file, change the first line to `rf2 v1 wrap` and repeat. Expect value 0. Wrapping can be useful for defined bit arithmetic. It is usually the wrong way to hide a financial or reservation-count error.

The systems profile uses unsigned machine-word behavior and unsigned comparisons. The expression `0-1` does not create an ordinary signed negative value there. You cannot assume Python's negative-number rules apply. Floating-point and general signed-type support remain implementation work.

**Checkpoint:** distinguish a refused computation from a computation whose specified answer is zero.

## 6. Use Studio without Terminal editing

Create a new private project folder and start Studio as described in the [Workbench walkthrough](../../docs/BOOKING-STUDIO.md). The three arguments are absolute paths to your project, native bundle and source/tool bundle. The downloadable Workbench includes the required native build helper.

Studio provides four separate actions. **Check** validates supported source. **Run checked code** executes through the bounded runtime. **Build native** creates an executable without starting it. **Run native** builds and runs the checked program. These labels represent real differences, not four names for the same operation.

Start with Sum and `[1,2,3]`. Run it, then change `sum input` to `squares input`. The answer changes from 6 to 14. Each action records a new source revision in the selected private folder. Do not treat the editor as a safe place to execute arbitrary downloaded programs: this edition accepts bounded Core, not arbitrary systems source.

**Checkpoint:** find the saved source and diagnostic files after one action. Leave them intact while investigating a failure.

## 7. From a recipe to general systems source

The compact operations are a convenient starting point, not the whole language. General systems source has functions, variables, loops and explicit effects. For example:

```flow
profile RF2_SYSTEM_A64_V1
fn twice(n)
 return n*2
end
fn main(argc,argv)
 let answer=twice(7)
 if answer==14
  return 0
 end
 return 1
end
```

`main` is the entry point. `argc` and `argv` represent command-line arguments. A zero exit status conventionally indicates success to the caller; returning 14 would report status 14, not print the number 14. This program checks its own result and exits successfully.

The current syntax closes blocks with `end`. It uses `let` to establish a local and `set` to update one. Do not substitute a proposed `var`, braces or a Java class declaration. A proposal is not an accepted program.

Build this lesson from a source checkout with explicitly selected tools:

```sh
sh tools/build-program.sh /absolute/bundle/rf2c book/learning-edition-1/examples/functions.flow new-build --opt
./new-build/program
```

The build directory must be new. Compilation and signing are separate from execution. Systems programs are trusted local code, not an extension of bounded MCP authority.

## 8. Variables, branches and loops

A variable gives a value a name. Initialize it before use. A branch chooses a path. A loop repeats while its condition remains true. This loop computes 0+1+2+3+4:

```flow
let n=0
let total=0
while n<5
 set total=total+n
 set n=n+1
end
```

A complete runnable version is included as [loop.flow](examples/loop.flow). These statements belong inside a systems function. They are a fragment, not a complete compact program. If you omit the update to `n`, you have created a loop that does not finish. The systems compiler does not prove termination of arbitrary loops.

Declare a value outside a branch if you need to update and read it after that branch. Do not rely on an uninitialized value or a branch-local name escaping its block. Good diagnostics are part of the learning experience, but not all current diagnostics explain every mistake well.

**Exercise:** predict the total if the condition becomes `n<6`.

## 9. Make libraries, not repeated copies

A library holds reusable behavior. A source entry imports a local module with `use`. In the current module system, paths resolve from the entry's directory, including imports made by its libraries. They are not automatically relative to each importing file.

That detail explains why Booking, Studio and Documents share one physical `examples/documents` root. They use the same text, IO and transport modules. Copying a library into every new application would create several versions that can disagree.

The module system rejects unsupported paths and cycles, but it is not a package registry or a hostile-filesystem containment system. Functions currently share a namespace. More convenient library distribution and namespacing remain work.

**Checkpoint:** follow `use "lib/booking.flow"` from the Booking entry to the date/time and storage modules. Identify behavior shared with the graphical app.

## 10. Records, arrays and growing collections

A record groups named scalar fields. A fixed array stores a declared number of typed elements. A growing collection can acquire more storage within its declared limit. These solve different problems.

Existing records cannot freely contain other records, strings or collections as rich nested values. Growing heap collections currently hold unsigned 64-bit numbers with bounded ownership rules. They are not Python dictionaries or Java generic object collections.

Use the [numeric summary application](../../examples/collection-tools/README.md) to see parsing, sorting and summarizing shared across two programs. Feed it `9,1,9,3,2`; the expected count is 5, minimum 1, maximum 9, sum 24 and lower median 3. Sorting five values does not prove an unlimited dataset can fit in memory.

**Exercise:** for room/customer/reservation data, list which fields should be typed values rather than manually packed memory offsets. This is a design exercise; nested value support is not yet implemented.

## 11. Recoverable errors are part of the result

A typed result function returns `ok(...)` or `err(...)`. A `handle` statement must cover both. This prevents silently discarding the result variant. It does not force the programmer to choose a sensible recovery action.

```flow
result Number(u64,u64)
fn accept(n):Number
 if n==0
  return err(22)
 end
 return ok(n)
end
```

This is a library fragment. A caller must handle success and failure in the documented order. See the complete [results.flow](examples/results.flow) lesson for an executable caller.

Do not write an empty error branch just to make the compiler accept your code. Decide whether to explain, retry, refuse, or inspect state. Retrying an uncertain save can create a second operation. More elaborate generic error objects and automatic propagation are not available merely because another language has them.

**Checkpoint:** explain the difference between “no booking saved” and “save outcome uncertain.”

## 12. Text, bytes and resource ownership

Bytes are small integer storage units. UTF-8 encodes text using sequences of bytes. A byte count and a character count can differ. RF2 has validated scalar-oriented text operations, but a Unicode scalar is not always an entire user-perceived character.

The shared text library offers useful searches and escaping. Exact byte search does not provide regex matching, Unicode normalization or language understanding. Never display unescaped user text as HTML just because it passed UTF-8 validation.

Owned resources help pair acquisition with cleanup. Current guarantees are scoped: normal-return cleanup and supported local moves do not make raw pointers safe, protect against every signal or establish concurrent borrowing rules. Review cleanup errors rather than treating them as impossible.

**Exercise:** use a Tamil name in Booking. Observe storage and display. Do not infer complete Tamil collation or grapheme-editing support from one successful name.

## 13. Booking: one useful application

Booking is deliberately small: one room, a calendar date, start and end minutes, a name and a saved identifier. Start with a new journal:

```sh
./booking init /absolute/path/to/room.rf2book
./booking-web /absolute/path/to/room.rf2book
```

The printed URL opens the local graphical form. Create a 09:00–10:00 reservation. Try 09:30–10:30 on the same date. The overlap must be refused. Then try 10:00–11:00: adjacency is allowed. Cancel the first reservation and reload.

The interval rule is `startA < endB` and `startB < endA`. Both must hold for overlap. Equal boundaries therefore do not conflict. Start must precede end on the same day. There is no timezone conversion or recurring schedule engine.

Restart the app with the same journal. Previously saved active bookings should reappear. Keep the file path explicit. The teaching app does not provide user accounts, payments, multiple rooms or production hosting.

## 14. What if two people book at once?

A correct booking needs more than an overlap function. Two writers could both inspect an empty schedule and then both save. Booking uses a cooperative file lock around reading, validating, checking and writing the journal.

The tests start separate native processes. For a shared overlapping request, one succeeds and the other receives conflict or busy. That is evidence about this cooperative file protocol. It is not proof of a language thread model or protection against a malicious process ignoring locks and replacing files.

GUI forms include a revision. A stale form must refresh instead of assuming the schedule is unchanged. A user-friendly recovery displays the latest state and invites a deliberate new attempt. Blind automatic retries are not always helpful.

**Exercise:** open two browser tabs, load the same revision, save from one and submit the other. Inspect the current bookings rather than expecting a second confirmation.

## 15. What if a save fails?

The journal appends events and syncs them. A failed append attempts to restore the old length and sync that rollback. Error 9002 means the outcome is uncertain, not a successful save and not a guaranteed absence of change. Error 9001 identifies a malformed or torn journal that must not be silently erased.

The existing qualification distinguishes a real OS file-size limit that forced a partial write from disposable source-injected sync/truncate errors. Both are useful, but they answer different questions. Neither establishes power-cut durability on every disk.

The journal supports 512 events, including cancellations. A checksum detects some corruption; it is not a signature or proof of who wrote the record. Compaction and stronger recovery remain future work.

**Checkpoint:** write an error message that asks the user to inspect current state without falsely promising the original state survived.

## 16. A read-only document workspace

The Documents bundle can load explicitly selected UTF-8 files into a bounded snapshot, search them and show previews. Its CLI and graphical app share text and collection modules. This is a second application family, not an invoice-only demonstration.

The current corpus is bounded to 64 files and 1 MiB. It does not automatically extract uploaded PDFs, continuously index a disk or edit originals. A screenshot of a search does not establish those unimplemented capabilities.

Try the supplied English and Tamil programming fixtures before private documents. Change a query, check the source path and verify the preview. A search result is a match, not proof that the document's claim is true.

**Exercise:** name one feature that belongs in the text library and one that belongs only in the document interface.

## 17. Ask an AI through MCP

MCP is the tool interface between a host and defined operations. RF2's native runtime exposes nine tools. Core tools can check, run or lower supported source; fixed application tools have their own exact contracts. The host supplies language-model intelligence.

Do not ask a model to bypass a rejected effect by renaming it. General systems source, arbitrary filesystem paths and unrestricted networking are not admitted through the Core checker. The IDE does not silently widen these permissions.

A useful request is: “Write a checked compact sum, test `[1,2,3]`, then explain what happens on overflow.” A weak request is: “Prove it is universally fastest.” The first names an observable task; the second needs a defined experiment before it can have an answer.

**Checkpoint:** distinguish source generation, source checking, runtime execution, native building and permission to run an executable.

## 18. Machine code, boards and the wider stack

RF2's Mac compiler emits ARM64 machine code. A separate backend emits a bounded ESP32-C3 RV32 subset. Existing boot, UART, timer/watchdog and interrupt work has emulator evidence. Physical board and sensor qualification are still pending.

A backend must implement the target's instruction encodings, calling conventions, memory layout and platform interface. Hexadecimal is a way to write numbers, not a new processor. Software cannot make arbitrary hardware capabilities exist by changing source syntax.

Do not flash a board from a book example without confirming board identity, target image, wiring and recovery. A Mac systems program is not automatically ESP32 firmware. Likewise an x86 assembly example cannot be compiled by an ARM64-only application backend without a target implementation.

**Exercise:** describe the separate evidence needed for compilation, emulator execution and physical sensor readings.

## 19. Learn like a tester

For each feature, keep four items: input, expected outcome, actual outcome and limitation. Add an adverse case. A pass should mean the assertion matched, not merely that a tool returned text.

WhatIF separates functional behavior, capacity, resilience and security. This edition applies those perspectives to the lessons and existing application receipts. A short loopback GET smoke test checks status/header behavior only. It cannot prove successful bookings, a million users or security.

Reverse Lab ties claims to artifact versions and inspections. ThesisPro's review rules separate evidence, method, practical usefulness and prose. Those are AI-assisted review perspectives here, not external professors or publisher endorsement. The versioned evidence ledger records the scope and limits of this edition.

If something fails, preserve the input and diagnostic. Change one cause, rerun the affected example and record the correction. Do not delete the failure or weaken the expected result to make a green checklist.

## 20. Answers and your next project

Chapter 3: `[2,4,6]` sums to 12. Chapter 4: seven has three set bits and eight has one; the count is four. Chapter 8: extending the loop to include five produces 15. Chapter 10 is a proposal exercise: a reservation should eventually carry typed identity, time interval and customer data, but current nested value support is missing. Chapter 12 tests UTF-8 storage/display only. Chapter 16: reusable matching belongs in a text library; choosing a preview panel belongs in the interface. Chapter 18: compilation needs output/encoding checks, emulation needs an executed model trace, and a sensor claim needs measurements on identified physical hardware.

Choose a small next project: room availability CLI, a text statistics viewer, or a number summary tool. Define input, output, permission and failure behavior first. Reuse an existing library where it fits. If it does not fit, name the missing contract before writing another private copy.

Your progress is not the number of pages read. Can you predict an output, run the program, explain a refusal, find the source and identify what is still unknown? Those are useful first-edition outcomes.

## 21. Build an interface people can understand

A language and a visual design system solve different problems. Java classes do not automatically produce a clear screen. RF2 machine code does not automatically choose readable typography or a sensible form layout. The current RF2 application route generates HTML/CSS; the browser draws it. Native widgets, graphics and mobile adapters require separate implementations.

Start with the task. In Booking the main action is reserving a room, so the page should show the date/time form and current availability together. The status must explain whether a save succeeded, conflicted or is uncertain. An attractive success colour is harmful if it hides an uncertain outcome.

The reusable `workbench-ui.flow` module already provides cards, input labels, focus rings, notices and a responsive grid. It is an early component layer, not a complete design framework. Reuse that layer instead of generating a different colour scheme and form structure for every page. A future RF2 UI library should expose meaningful components with stable behavior: a field with validation, an action with pending/success/failure states, a table with an empty state, and a view that explains where the user is.

**Your UI checklist:** can the page be operated with a keyboard? Do errors identify the next action? Is the layout readable on a narrow display? Is information conveyed in text as well as colour? Are destructive actions distinct? Are long names and empty results handled? Inspect each condition in the actual rendered interface. A source-level stylesheet does not prove the result is accessible.

**Exercise:** sketch Booking for a phone-width display. Keep the reservation form before the saved list. Write three different status messages for success, conflict and uncertain save. Avoid a decorative animation that makes the result slower to understand.

## 22. What is special about RF2?

RF2 does not become useful because another language has classes and RF2 has a different keyword. Classes organize values and behavior. Syntax expresses meaning. C source can be compiled to machine code, but C and assembly are distinct languages. RF2 likewise needs an implementation behind every advertised capability.

Its present direction combines three things: human-readable source, native tools written in RF2, and a bounded interface an AI can inspect and call. Its result and ownership mechanisms make some failure and resource obligations explicit. The compiler and tests are inspectable. Those are concrete properties, not proof that RF2 is uniquely capable or universally better.

The larger opportunity is to package useful behavior so humans and AI compose tested capabilities rather than rebuilding validation, storage and recovery repeatedly. Booking is an early example: one rule library supports a CLI and a browser interface. That can reduce duplicated logic. Whether it reduces total development effort compared with a mature stack remains an experiment.

A useful evaluation asks: did the application work, how many defects remained, could someone else install it, how much work was required to change it, and what permissions did it need? Short source alone can hide a great deal of setup. A convincing first program is a beginning, not a reason to migrate a business.

**Exercise:** describe an RF2 advantage as an observation you could test. Replace “fastest language” with a specified workload, baseline and measurement.

## 23. Three projects with honest acceptance tests

**A study-room planner.** Input: room, date, start, finish and student alias. Output: a confirmed identifier or clear refusal. First build only one room using the existing Booking app. A proposed extension adds several rooms. Its acceptance gate is that simultaneous overlapping saves in one room cannot both succeed, while bookings in different rooms can coexist. The proposed extension requires implementation; the current one-room journal is not secretly multi-room.

**A document helper.** Input: selected UTF-8 files and a query. Output: source-labelled matches and previews. Begin with Documents. Acceptance checks include a missing file, invalid text, no matches, a long line and a Tamil query. A later editing feature must add preview/confirmation/recovery rules instead of treating read-only search permission as write permission. PDF extraction remains a separate dependency and feature.

**A sensor logger.** Input: defined sensor readings with timing and error status. Output: bounded records and clear stale/failure indicators. The current ESP32-C3 work provides an emulator starting point, not proof of a connected sensor. First verify encoding and emulator traces; then identify physical board, sensor, wiring and observed data. A simulated temperature must never be described as a physical measurement.

For all three, separate model, interface and storage. Write the same core acceptance rule once, then exercise it through every supported interface. An AI can help produce candidate code and test cases. It cannot approve its own missing field evidence into existence.

## 24. Follow the evolution without relearning a fictional language

The evolution specification preserves existing working source. A new record feature needs rules for construction, layout, borrowing, updates and escape. A new collection needs element semantics, growth failure behavior and cleanup. A new platform needs machine-code and ABI qualification. A new tool needs an authority contract.

One [development experiment](../../experiments/nested-records/README.md) now composes typed **borrowed** records: a reservation can refer to a time record. Its finite tests exercise reading through that relationship, alias-visible leaf mutation and rejection of invalid bindings. Its 12 finite default/optimized controls passed. It is not in the released compiler and does not provide inline value copying, owned nested collections or a complete lifetime system. Do not copy proposed syntax into Workbench0.38 and expect it to compile.

That example shows why progress needs labels. Implemented source in an experiment is different from a packaged feature. Passing a finite test is different from a universal guarantee. A teaching exercise is different from an implemented application. Learning documents should help you tell those states apart.

The next broad language milestone remains typed application values and safe ownership transfer, followed by collections, serialization and storage services. The next educational milestone is a real learner completing a fresh installation and change task, recording where they get stuck. This book has an AI-executed walkthrough; it does not claim that Jitra has completed it.

**Final checkpoint:** build one small thing, explain one failure, and identify one unsupported extension without inventing a workaround that changes the claim.

## Glossary

**ABI:** rules used at machine-code boundaries. **Backend:** compiler part that emits for a target. **Bound:** a stated limit. **Core:** RF2's restricted computation profile. **Effect:** an operation's interaction beyond its local calculation. **Journal:** stored sequence of events. **MCP:** interface exposing defined tools to a host. **Ownership:** responsibility for a resource's lifetime. **Profile:** the selected language contract. **Receipt:** recorded execution evidence. **Result:** explicit success or failure outcome. **Runtime:** program that executes supported instructions or services. **Scalar:** one basic value. **UTF-8:** byte encoding for Unicode text.

## Source and evidence guide

This is original technical instruction based on the RF2 repository at commit `954762a199e1fc94e651f39fab87c2642bea71f8`. See [Core](../../docs/NATIVE-CORE.md), [types/modules](../../docs/MODULES-TYPES.md), [ownership](../../docs/RESOURCE-OWNERSHIP.md), [heap collections](../../docs/HEAP-COLLECTIONS-0.33.md), [shared libraries](../../examples/documents/LIBRARIES.md), [Workbench](../../docs/BOOKING-STUDIO.md) and [ESP32-C3 interrupts](../../docs/ESP32C3-INTERRUPTS-0.36.md). Older reference pages describe their original version; the current source and later receipts govern additions.

The learning verification record identifies newly executed examples separately from earlier application qualification. Unsupported syntax exercises are expected refusals, not an implemented-feature count. No speed, token-saving, plagiarism-detector or independent review guarantee is made.
