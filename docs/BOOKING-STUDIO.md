# Booking and Studio: RF2 Workbench 0.38 development edition

This edition adds a one-room booking application and a small learning IDE. Both servers are RF2 native programs with local browser forms. There is no browser JavaScript and no Node/npm/Python user runtime. The existing native compiler and nine-tool MCP runtime are unchanged.

## Jitra's first application

Download the [Workbench Mac bundle](../dist/workbench-0.38/README.md). This development build supports Apple Silicon macOS. Extract it, open Terminal in its folder, then run:

```sh
./booking init "$HOME/Downloads/my-room.rf2book"
./booking-web "$HOME/Downloads/my-room.rf2book"
```

Open the printed local URL. Enter a name, date, start time and end time. Confirm the booking. The saved card appears only after the journal write and sync succeed. Restart the program with the same file to reload it. Cancel a card to release its time slot. Adjacent bookings are allowed; overlapping bookings on the same date are refused.

`init` creates a new file and refuses an existing one. The CLI also supports:

```sh
./booking list "$HOME/Downloads/my-room.rf2book"
./booking reserve "$HOME/Downloads/my-room.rf2book" 2027-01-10 09:00 10:00 "Test Student"
./booking cancel "$HOME/Downloads/my-room.rf2book" 1
```

These names and dates are programming inputs, not actual customer reservations.

## Write your first program

Create an empty private project folder. Use absolute paths for the three Studio arguments:

```sh
mkdir -m 700 "$HOME/Downloads/My RF2 Project"
./studio "$HOME/Downloads/My RF2 Project" "$PWD" "$PWD"
```

Open its printed URL. Start with the Sum lesson and `[1,2,3]`. Run checked code returns 6. Change `sum input` to `squares input`; it returns 14. Check explains rejected source. Build native emits an executable without running it. Run native builds and executes the checked program. Each action saves a new source revision and diagnostics in your chosen folder; it never silently overwrites an earlier revision.

The IDE currently supports bounded Core number programs, not arbitrary systems source. Booking itself uses the general systems profile and is built explicitly with the trusted developer tools. A full project editor, language server, debugger, visual GUI builder and general application execution still need implementation. The IDE does not make those language capabilities exist automatically.

## Shared libraries

All application entries use the same physical module root, `examples/documents`, to share the existing text, collections, IO and HTTP modules. New modules add:

| Module | Contract |
| --- | --- |
| `lib/datetime.flow` | Gregorian date validation and ordinal conversion; same-day minute intervals |
| `lib/storage.flow` | Regular single-link files, advisory nonblocking locks, bounded append, sync and rollback outcomes |
| `lib/booking.flow` | Journal replay, overlap checking, reservation and cancellation |
| `lib/forms.flow` | Bounded form decoding, exact origin/host, session token and field checks |
| `lib/process.flow` | Fixed trusted argument vectors, captured output, five-second tool budget and child reaping |
| `lib/app-server.flow` | Shared loopback application transport |
| `lib/workbench-ui.flow` | Shared accessible labels, focus states and responsive layout |

## Storage and failure boundaries

Booking uses one stable journal inode with a 32-byte header and 128-byte events. Each event has an FNV corruption checksum, not an authentication signature. There are at most 512 events including cancellations. Compaction is not implemented. Names are at most 64 UTF-8 bytes. Dates are years 1–9999; times are same-day minutes, with 24:00 accepted as a CLI end time. Browser time controls normally expose 00:00–23:59. No timezone conversion, overnight booking, recurring reservation, accounts, payments or hosted deployment is included.

Cooperating processes lock the file around reload, conflict checking, append and sync. A second writer can receive busy error 35 or conflict 409 and must refresh. GUI forms also carry the journal revision, so a stale form cannot silently overwrite newer state. Locks do not protect against a malicious same-user process replacing the path or ignoring the protocol.

An unsuccessful append attempts truncation and sync to the previous length. Error 9002 means the outcome is uncertain: inspect saved state before retrying. Corrupt or torn journals return 9001 without erasing evidence. A successful save does not establish power-cut durability or storage hardware correctness. Production recovery and hostile file replacement require further work.

Studio invokes only fixed trusted tools after the bounded source check, with direct argument vectors, not user-built shell command strings. It is not an operating-system sandbox. Tool descendants that escape the process group and uninterruptible kernel operations are outside the tested timeout contract. Invalid HTTP requests may be closed before a complete response; no state-changing action is accepted from them.

## Qualification

Run the independent development controllers with a selected native compiler/runtime bundle:

```sh
RF2_TEST_COMPILER=/absolute/bundle/rf2c python3 tests/standalone/booking_verify.py
RF2_TEST_HOME=/absolute/bundle python3 tests/standalone/booking_faults_verify.py
RF2_TEST_HOME=/absolute/bundle python3 tests/standalone/workbench_http_verify.py
```

Python is a development oracle only. Tests cover separate native booking processes, real file-size-induced partial writes, disposable source-injected sync/rollback failures, HTTP state protection and checked/native result parity. Fault injection is labelled separately from actual OS failures. No universal speed, token saving, production security or physical hardware claim follows.
