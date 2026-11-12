# Buffered byte audit

`rf2-buffer-audit file` reads a named file into a bounded growing byte vector, then makes a second pass over the completed collection. It returns a structured report containing byte count, line count, NUL-byte count and an FNV-1a 64-bit fingerprint. Input files are opened read-only and remain unchanged.

```sh
./rf2-buffer-audit document.bin
```

To build from trusted source:

```sh
tools/build-program.sh ./rf2c examples/buffer-audit/main.rf2 new-build --opt
./new-build/program document.bin
```

The app demonstrates larger-than-fixed-array storage, a later pass over stored bytes, owned file/vector cleanup and a record returned by value. It does not claim that buffering is faster or more memory-efficient than a streaming summary. The fingerprint is noncryptographic and does not prove authenticity or collision resistance.

## Exact input and result contract

* Exactly one filename is required. There is no implicit stdin mode. Ordinary read-only OS open semantics apply, including symlinks; this is not a filesystem sandbox. A FIFO or special device may block, so no deadline is promised.
* Bytes are preserved without Unicode decoding. NUL, malformed UTF-8, CR and all values from 0 through 255 are ordinary bytes.
* Lines equal the LF-byte count, plus one if nonempty input has no final LF. Empty input has zero lines. CR is not a separator; a terminal LF does not create an extra line.
* The fingerprint starts at 14695981039346656037 and, for each byte, computes `(fingerprint xor byte) * 1099511628211`, wrapping modulo 2^64. Empty input retains that initial value.
* The vector limit is 1 MiB. Its backing is a fixed virtual reservation with a growing usable prefix, not an unbounded heap or a resident-memory measurement. Logical length is distinct from capacity and the OS page granularity.
* Reads use a fixed 255-byte chunk. A file exceeding the vector limit returns error 22 rather than a truncated success. The current read may have consumed a bounded chunk beyond the first unaccepted byte before cleanup. No successful report or partial statistics are returned on an input/storage/cleanup failure.

Success prints one JSON object with `bytes`, `lines`, `zeros` and `fingerprint`, followed by a newline, and exits 0. An ordinary input/storage/cleanup failure prints `{"error":number}` and exits 1. Usage errors print a message on stderr and exit 1. OS read/open errors are positive errno values; the owned cleanup protocol can report `65536 + errno` for an automatic release failure after otherwise successful work. A primary error is preserved.

The `collect` helper owns the file and vector. Its scalar I/O result allows automatic failure propagation and cleanup. The `audit_file` wrapper returns `Report(Stats,u64)`; the success record is copied by value into the caller's annotated handler. No vector pointer or wrapper-frame record pointer is returned.

Output helpers handle positive short writes and report failed/zero writes through exit status 1. No successful short-write event was forced in the tests. Output failure can leave partial JSON. Signals such as SIGPIPE, explicit process exit and fatal compiler traps retain the language's existing cleanup exclusions. The audit helper has already completed ordinary cleanup before main starts printing.

## Verification

`tests/standalone/buffer_audit_verify.py` compiles default and optimized executables. Full JSON output is compared with an independent Python byte/line/FNV oracle across empty data, NULs, UTF-8, all byte values, seeded random inputs and chunk/growth boundaries. It checks exactly-at-limit and over-limit files, usage/open/read errors, symlink behavior, unchanged input and failed stdout writes.

In-process probes check file-descriptor reuse after ordinary success, read failure and over-limit failure. They do not directly observe virtual mapping release; vector-specific compiler tests cover that separate contract. These are finite local software fixtures, not field results, a memory-safety proof, a physical-memory benchmark or a speed/token claim.
