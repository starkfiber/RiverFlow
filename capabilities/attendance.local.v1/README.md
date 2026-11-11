# attendance.local@1

A working batch attendance exporter. Supply student IDs, dates and states; receive a validated CSV and present/absent/late counts. Duplicate student/date pairs reject the export.

```sh
./rf2 attendance capabilities/attendance.local.v1/test-records.json register.csv
```

The included TEST records are programming test inputs, not student observations or research findings. Use a new output path. Existing files and symlinks are refused. Validation finishes before output creation. A successful write creates an owner-only 0600 file and returns counts, byte length and a SHA-256 fingerprint. A write/close failure is a failed export and can leave an incomplete newly created file; crash-safe journaling is not implemented.

Through MCP, call `attendance_export` with a `records` array. The result includes CSV text and counts. It does not write a file, accept a path, grant a teacher role, contact a service or store a database. Filesystem export is available only through the explicit local CLI command. A model host may retain its own context; this service does not promise host-level zero retention.

## Input rules

At most 1,000 records, each with exactly `student_id`, `date` and `status`.

- Student ID: 1 to 64 ASCII characters, beginning with a letter or digit, followed only by letters, digits, hyphens or underscores. IDs are case-sensitive. The format excludes delimiter/control characters and formula prefixes.
- Date: canonical Gregorian `YYYY-MM-DD`, years 0001 through 9999, validated for actual days and leap years.
- State: exactly `present`, `absent` or `late`.
- One record per student ID and date. The same ID on a different date is valid.

The CSV header is `student_id,date,status`, rows preserve input order, and each line ends in LF. These constrained fields need no CSV quoting. The executed round-trip check uses an independent CSV reader; it does not guarantee that every spreadsheet application will preserve IDs when users edit and re-save files.

## Core-backed business logic

The status validator maps present/absent/late to weights 1, 1024 and 1048576. The versioned `tally.flow` program uses a scalar helper and a bounded checked sum to produce packed counters. Because total records cannot exceed 1000, each count fits within its ten-bit field and the u32 sum cannot overflow for admitted records.

`native/attendance-kernel.rf2` is generated from that Core source by `rf2 lower` and compiled into the application. The exporter calls that generated kernel for the counts; it does not substitute a separate hardcoded tally. `capability.json` records source and generated-kernel fingerprints. The fingerprint detects byte differences when checked; it is not a signature or remote attestation.

This capability does not implement an editing UI, authentication, student database, school policy engine or field deployment. It demonstrates one versioned end-to-end application operation using actual Core/native computation and explicit effects.

## Executed checks

`docs/ATTENDANCE-VERIFICATION.json` records successful exports, CSV round trips, Gregorian classification checks, duplicate/schema/unsafe-ID refusals, count correctness, byte fingerprints, output-file protection and recovery into Core tools. The tests include the maximum admitted record count and explicit fictional TEST IDs only. The official MCP SDK also exercises successful export and duplicate refusal.

No claim is made about school outcomes, adoption, speed or token savings.
