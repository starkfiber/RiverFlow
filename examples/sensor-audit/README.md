# Sensor log audit

A standalone RF2 program for checking recorded temperature CSV logs before using them in a report. It validates the entire input, calculates per-sensor summaries and flags readings outside selected thresholds. It never opens a serial device, changes a file, controls equipment or claims a physical measurement.

The runtime is native Mac ARM64. The supplied compilation evidence uses the isolated 0.49 candidate; the source also builds with 0.48B. A compatible native compiler is required. No Python, Node, npm or C++ runtime is required by the resulting application. Python is used only for the independent test oracle; an existing Node executable was used only to expose and verify a JSON consumer precision problem.

## Build and run

From the repository root, choose a compatible native compiler and a new build directory:

```sh
sh tools/build-program.sh /path/to/rf2c examples/sensor-audit/main.flow new-sensor-build --opt
./new-sensor-build/program examples/sensor-audit/fixtures/signed-sensors.csv
./new-sensor-build/program examples/sensor-audit/fixtures/signed-sensors.csv -1000 50000
```

The source imports the adjacent `lib/` modules. Keep that folder with `main.flow`. The two base text/I/O modules are reused byte for byte from `examples/documents/lib/`; the application-specific `sensor.flow` supplies parsing, accumulation and JSON rendering.

The CSV header must be exactly:

```text
sensor_id,timestamp_ms,temperature_mC
```

Rows have exactly three unquoted fields. Sensor IDs are canonical decimal integers from 1 through 32. Timestamps are canonical decimal integers from 0 through 18446744073709551615 and must increase strictly for each sensor. Different sensors may share a timestamp or arrive interleaved. The program does not require one global timestamp order.

Temperature is an integer number of milli-degrees Celsius, from -100000 to 200000 inclusive. Examples: `-1250` means -1.250°C; `25000` means 25°C. Leading zeros, `+`, `-0`, decimals, whitespace, exponent notation, quotes and extra fields refuse. LF and CRLF files are accepted; a final LF is optional. Empty records and a bare terminal CR refuse. Input is bounded to 1 MiB, each data record to 128 bytes and the complete file to 4096 records. A header with no records is allowed.

Optional thresholds have the same temperature syntax/range and must satisfy `LOW_MC <= HIGH_MC`. Defaults are 0 and 50000. `below_low` counts values strictly below the low threshold; `above_high` counts values strictly above the high threshold. Equal endpoints do not alert. These are selected data thresholds, not a clinical, electrical or industrial safety standard.

## Output and errors

Success returns exit 0 and one `rf2.sensor-audit.v2` JSON object. It contains total rows, thresholds and sensors sorted by numeric ID. Each sensor includes count, first/last timestamp, minimum, maximum, signed sum, alert counts and an exact rational mean (`numerator_mC` / `denominator`). No floating-point rounding or signed-machine reinterpretation is used. Internally temperatures use an explicit nonnegative offset; bounded sums fit exactly in u64.

`first_ms` and `last_ms` are **canonical decimal strings**, preserving the full timestamp range in ordinary JavaScript JSON consumers. Other reported integers stay within the JavaScript exact-integer range under the stated input bounds. The initial epoch 1 prototype used JSON numbers for timestamps. A real `JSON.parse` roundtrip changed both near-u64-max values into `18446744073709552000`. The final wire schema was intentionally versioned to v2; the original v1 results remain historical. The mathematical oracle was preserved byte for byte, while final wire values are separately checked and normalized into arbitrary-precision integers for comparison.

Malformed input, unsafe/missing files, invalid thresholds and capacity failure return exit 2 with a stderr diagnostic (including the input line where applicable) and **no stdout report**. Original input bytes remain untouched. Output is assembled only after full input validation. A broken output pipe can still receive a prefix before an I/O failure; stdout is not a transactional file. Parent directories may contain symlinks; the final input component cannot be a symlink. This is a trusted local Systems program, not a path-containment sandbox or live-file snapshot service.

## Tests

`reference.py` is a standalone Python stdlib batch comparator. `reference_stream.py` is a stronger single-pass aggregation comparator that avoids storing each sensor's full sample list. Both use the same strict v2 wire contract and pass the same 149 black-box cases; the latter still reads one bounded file and is not an unbounded streaming service. These comparators are development tools, not RF2 runtime dependencies. Process-inclusive timings, startup and persistent computation must be reported separately.

```sh
python3 examples/sensor-audit/verify.py /path/to/native/program --label local-replay
python3 examples/sensor-audit/api_verify.py /path/to/native/compiler
python3 examples/sensor-audit/verify.py examples/sensor-audit/reference.py --python-reference --label python-reference
```

The black-box oracle uses Python's exact integers and independent record/statistics code. It checks generated valid logs, signed boundaries, all 32 IDs, 4096/4097 rows, full-u64 timestamps, 2^53 boundaries, malformed records, rejected thresholds and unchanged input hashes. Epoch 1 passed 148 original cases. Final epoch 2 passed 149 cases in both compiler modes. Direct library checks cover 16 refusal/state-preservation cases across both modes. One initial API test generator accidentally replaced `OLDSTAMP` partly as `STAMP`, producing invalid `OLD2` source; that harness failure is retained and fixed by substituting longer placeholders first. It was not an RF2 compiler defect or an accepted application pass.

These are generated and controlled recorded-data inputs. There is no sensor hardware, field deployment, model-token saving, cross-platform qualification or Python/runtime speed advantage established by these tests. Python can perform this task too. The demonstrated RF2 value is a checked, single native delivery using reusable RF2 text/I/O plus a strict reusable fixed-point parser and accumulator; broader adoption advantage remains a separate experiment.

`reference.py` is a standalone Python standard-library comparator. It uses the same independently written exact mathematical oracle, strict file admission and final v2 wire contract, without importing the test harness, starting servers, sleeping or adding artificial work. It also passes the same 149-case corpus. It is comparison tooling, not a dependency of the RF2 executable. Runtime timing must be performed separately after concurrent tests stop; none is claimed here.
