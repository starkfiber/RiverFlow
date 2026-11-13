# Native collection tools from shared RF2 modules

These two command-line applications read supplied unsigned integer values. They do not collect sensor readings, connect to a device, classify an incident or claim a measured workplace outcome. Their `.flow` entry files use the trusted RF2 systems profile on the qualified native host.

- `telemetry-summary`: count, minimum, maximum, checked sum and lower median.
- `value-frequency`: sorted unique values with exact occurrence counts.

Both import **one canonical** `lib/numbers.rf2`, which parses numbers, sorts the heap collection and computes aggregates. Both also import `lib/output.rf2` for checked writes. Each application first owns a collection, fills it, explicitly moves that owner to a new binding, passes mutable borrows to library helpers and relies on ordinary result-return cleanup. The library does not copy an owner or hide a global numeric collection.

## Build and try

Use the qualified native development compiler that implements `collection`. From the repository root:

```sh
./tools/build-program.sh /absolute/path/to/rf2c examples/collection-tools/telemetry-summary.flow summary-build --opt
printf '9,1,9,3,2' | ./summary-build/program
# {"count":5,"minimum":1,"maximum":9,"sum":24,"median_lower":3}

./tools/build-program.sh /absolute/path/to/rf2c examples/collection-tools/value-frequency.flow frequency-build --opt
printf '9,1,9,3,2' | ./frequency-build/program
# {"count":5,"unique":4,"frequencies":[{"value":1,"count":1},{"value":2,"count":1},{"value":3,"count":1},{"value":9,"count":2}]}
```

Native binaries need no Python, Node or npm runtime. Independent development tests use Python integer, sorting and frequency oracles. The `.flow` filename is accepted by the native compiler; it does **not** establish ESP32, Arduino, firmware or cross-platform compilation. A hardware target needs its own backend, ABI, runtime/drivers, linker/boot contract and actual tests.

## Input contract

Input is at most **1 MiB** and contains at most **65,536 values**. Values are canonical decimal u64 integers from `0` through `18446744073709551615`. A number has no sign, leading zeros (except `0` itself), decimal point, exponent or unit suffix. ASCII space, tab, CR and LF can separate values. A single comma can also separate values, with surrounding permitted whitespace. Empty comma fields and a trailing comma refuse.

An empty or whitespace-only frequency input produces an empty table. A summary requires at least one value. The summary refuses a sum greater than u64 rather than wrapping. The lower median is element `(count-1)//2` of sorted input, using zero-based indexing. Frequency counts do not require the input values to have a representable sum.

The application reads stdin completely within its budget before parsing, sorting or writing output. It does not discover paths, open input files by itself or alter input. Standard input/output are borrowed descriptors. Output is numeric JSON. Consumers need an integer-aware parser to preserve the full u64 range; floating-point JSON consumers can round large integers. Values are not emitted as decimal strings. Output failures can leave a partial JSON document; the CLI does not claim transactional stdout or cleanup after fatal signals/traps.

## Errors and limits

Unexpected CLI arguments return status2 with usage on stderr. Ordinary input, collection, arithmetic or output errors return status1 and `Error CODE` on stderr. Application error3 is a read failure,5 a write failure,22 invalid/empty input,27 the stdin budget and75 decimal/sum overflow. Collection operations can return additional positive error codes from their documented allocation/retirement contract. These application codes are not a promise that every number is the target OS's identically named errno.

Malformed input and oversized input produce no JSON before the failure. Collection cleanup follows the ordinary result-return protocol. The language's typed borrow/move boundaries do not establish arbitrary raw-pointer safety, concurrent mutation, unbounded allocation, owner return/transfer across functions or safety under raw-syscall interference.

The library uses heapsort, an established O(n log n) sorting algorithm. There is no new sort algorithm, speed, energy, model-token or hardware claim. Supplied examples and generated test inputs are programming fixtures, not fabricated sensor results.

## Reproduce the checks

```sh
RF2_TEST_COMPILER=/absolute/path/to/qualified-rf2c python3 tests/standalone/collection_apps_verify.py
```

The controller compiles actual `.flow` programs in ordinary and optimized modes, compares full JSON with independent integer oracles, tests larger-than-stack datasets, input/descriptor/budget failures and a single isolated shared-parser mutation affecting both applications. Preserve the emitted report and exact compiler/source identities; a controller passing against an older candidate is not final qualification for a later one.
