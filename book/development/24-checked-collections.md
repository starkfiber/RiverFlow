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
