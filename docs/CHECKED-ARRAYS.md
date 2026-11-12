# Checked fixed arrays in the native compiler

This capability is included in the 0.12 native compiler. Historical receipts retain their original compiler identities; current release qualification is recorded separately in RELEASE-0.12-VERIFICATION.json.

```rf2
profile RF2_SYSTEM_A64_V1
array Readings(u64, 64)
fn put(values: Readings, index, value)
 set values[index] = value
 return values.length
end
fn main(argc, argv)
 let values = Readings()
 do put(values, 3, 42)
 return values[3] - 42
end
```

## Contract

An array declaration defines a nominal type with a fixed capacity. This chapter describes the u64 element type; release 0.12 also supports packed u8 arrays, described in TEXT-BYTES.md. The capacity is a canonical decimal integer from 1 through 255; zero, leading-zero/hexadecimal spellings, overflowing literal spellings and larger capacities refuse. Array and record declarations share the existing 32-type limit and namespace. Different declared types remain different even when their capacities match.

An owned array is constructed with empty parentheses at function level. Every element is initialized to zero. It occupies one pointer slot plus one stack slot per element, within the existing 256-slot function frame limit. Function parameters and other locals consume slots too: a 255-element array fits in a no-parameter function but not alongside main's two parameters. Recursive calls get distinct frames. No implicit heap allocation, growth or shared global collection is involved.

Typed parameters borrow the array by reference. Updates are visible to the caller; two parameters may intentionally alias the same object. Ordinary typed code cannot return the array, copy/rebind it, use it in arithmetic, pass it to scalar/raw-intrinsic arguments or use it before initialization. These restrictions prevent ordinary typed array pointers escaping their frame; they are not an ownership proof for arbitrary raw systems code.

`values.length` is the fixed capacity, not a mutable count of populated elements. Applications track a separate logical count. Element reads and writes check the full unsigned index against capacity before addressing the element. A negative expression wraps under the systems scalar rules and is consequently out of range. Invalid access prints `RF2 bounds` to stderr and exits with status 2. There is no catch/recovery value yet.

For assignment, the array and index are evaluated and checked before the right-hand side. An invalid write therefore does not run a side-effecting value expression. Ordinary expression evaluation order remains unchanged. The emitter shares one cold error path for the whole image; normal successful checks fall through. Checks are emitted in both default and optimized modes. No general bounds-check elimination is claimed.

This remains the trusted systems profile. Raw loads, stores and OS effects elsewhere in a program are not made safe by an array declaration. There is no thread-safety, arbitrary pointer isolation, nested array/record element, resizable vector, UTF-8 string or unrestricted lifetime inference. Those need additional language rules and tests.

## Executed verification

[The array receipt](ARRAYS-VERIFICATION.json) records 200 native value cases, 36 runtime bounds failures, 58 compile refusals, four lifetime/frame cases, 160 independent application comparisons, 22 invalid application inputs and two checks that failing writes do not run their right-hand side. Each category includes default and optimized code. Values include u64 maximum; capacities, recursive arrays, zero initialization, nominal mismatches, frame exhaustion and borrowed aliases are checked.

The [latency analyzer](../examples/latency/) is the first complete application using the feature. It parses up to 128 supplied samples, sorts them through a typed array module and emits minimum, maximum, sum, lower median and nearest-rank p95. These are supplied numbers; the program does not measure a clock or infer engineering/participant outcomes.

[Measurements](COLLECTIONS-MEASUREMENTS.json) retain seven rotated process trials for random/descending inputs of sizes 1, 32 and 128, with cold/warmup, minima/maxima and checked outputs. Comparisons include default/optimized RF2, a frozen 0.11 raw-global-buffer translation, Clang insertion sort and Clang qsort. The raw-buffer variant has different lifetime/bounds semantics, and qsort changes the algorithm. Observed times are around the process-startup floor, with varying order. They establish executable behavior and timing scope, not isolated bounds-check cost or language-wide superiority.

[The regression receipt](ARRAYS-REGRESSION.json) also records the older compiler suites, two native self-generation stages, matching output from the published 0.11 bootstrap, byte-identical rebuilt runtime and fresh default/compact MCP SDK checks. [A retained-trace example](ARRAYS-REAL-TRACE.json) applies the program to seven earlier process timings rounded to integer microseconds; it is reanalysis, not a fresh timing experiment.

## Build and run

With a frozen downloaded 0.11 native compiler at `./rf2c`:

```sh
mkdir -p output
./rf2c native/compiler/compiler.rf2 output/rf2c-arrays
codesign -s - output/rf2c-arrays
./tools/build-program.sh output/rf2c-arrays examples/latency/main.rf2 output/latency-build --opt
./output/latency-build/program 12 7 19 8 11 43 17
```

Expected output:

```json
{"count":7,"min":7,"max":43,"sum":117,"median_lower":12,"p95_nearest_rank":43}
```

Developer reproduction: set RF2_TEST_COMPILER to the new binary and run tests/standalone/arrays_verify.py. tools/measure-collections.py also takes RF2_BASELINE_COMPILER for the frozen comparator and RF2_BENCH_RUN for a fresh evidence directory. Existing release receipts must be preserved. Compiling remains an explicit developer action; systems source is not accepted or run through MCP.

## Next language work

Checked collections are a foundation for useful programs. The next priorities are text/byte semantics, recoverable error values, explicit owned-resource cleanup and then tasks with a shared-memory model. Platform adapters and boot targets need their own built artifacts and runtime acceptance tests. None is implied by this array implementation.
