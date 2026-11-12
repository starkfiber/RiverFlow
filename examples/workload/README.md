# Workload analyser

A complete non-invoice application written in RF2, using reusable source modules and nominal records. It reads a local CSV file and reports input-order deadline accounting. It does not select an optimal scheduler or measure a device, business or OS workload by itself.

Build with the macOS ARM64 package:

```sh
./tools/build-program.sh ./rf2c examples/workload/main.rf2 workload-build --opt
./workload-build/program examples/workload/jobs.csv
```

The three-row programming fixture produces 3 jobs, 1 late completion, 9 elapsed ticks and a peak duration of 4 ticks. These are computed fixture results, not field measurements.

Each row is `job_id,duration_ticks,deadline_ticks`, all positive canonical u32 integers. No header, quotes, decimal values, spaces, blank rows or extra columns. LF and CRLF are accepted, with an optional final newline. At most 1,000 rows and 65,536 file bytes. Duplicate IDs are permitted; rows represent sequential entries. An empty file has zero totals. The example reads a named local file and writes JSON to stdout, with no output file creation or network access.

All jobs are available at tick zero and run in file order without preemption. A job is late when cumulative duration exceeds its deadline, strictly. Units must be supplied consistently by the caller. This is deterministic accounting for a trace, not an EDF implementation, workload collection system or claim of scheduling superiority.

`lib/io.rf2` provides simple output; `lib/csv.rf2` provides bounded parsing; `lib/workload.rf2` defines Job, Summary and accounting functions. Imports resolve from the entry directory and deduplicate by their restricted relative path. See docs/MODULES-TYPES.md for the exact language boundary.
