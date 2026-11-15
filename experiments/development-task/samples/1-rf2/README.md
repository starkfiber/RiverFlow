# Study Rooms — RF2

A local room reservation application with a native CLI, server-rendered browser
forms, and a read-only newline JSON-RPC MCP endpoint. All application runtime
logic is RF2. No external assets, packages, scripts, or application subprocesses
are used by the application. `launch.json` selects the compiled `./app`.

## Build and run

On an Apple Silicon Mac, from this directory:

```sh
./build.sh
./app init example.db
./app reserve example.db 1 1 2 2026-11-15 09:00 10:00
./app list example.db
./app serve example.db
```

The reserve example produces revision 2 with ID `"1"`, room 2, Gregorian ordinal
739935, start 540 and finish 600. Successful output also includes the SDK's
numeric `version:2`. `serve` prints its exact loopback URL as the first line;
open it in a browser. The server selects an ephemeral port, accepts only its
actual Host/Origin, and runs until terminated. Stop with Ctrl-C. A process-local
random token protects forms; restarting the server invalidates old forms.

Other commands:

```sh
./app cancel example.db 2 1
./app mcp example.db
```

`init` exclusively creates a file and refuses an existing path. All other
commands require an existing workspace. Mutation arguments include the last
observed revision. Errors exit 2 and emit `{"error":CODE}`; refresh with `list`
after stale/conflict errors (409), and retry later after busy (35). Invalid
values use 22, existing IDs/paths 17, and missing records/paths 404. Other I/O
and journal failures remain errors. No save is reported before SDK completion.

The browser shows current saved state, labelled room/date/start/end fields,
and an explicit cancel button for each reservation. Failed reserve input stays
visible; stale changes reload the current revision and rows. Dates are exact
YYYY-MM-DD and times exact HH:MM. End `24:00` is supported in the text end field.
There are 16 rooms and at most 256 current reservations. Intervals are half-open:
09:00–10:00 and 10:00–11:00 may share a room and date. There is no recurrence,
timezone conversion, or account authentication.

MCP accepts protocol version `2025-11-25`. For example, send these lines to its
stdin (stdout contains only JSON-RPC responses, one per line):

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"example","version":"1"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"booking_list","arguments":{}}}
```

Only `booking_list` is advertised. It takes an explicit empty arguments object
and reads only the command-line workspace. Tool refusals/read failures return
`isError:true`. Malformed JSON, duplicate decoded keys, unknown methods and
unknown arguments refuse; later requests can still be used. Lines are bounded
to 65536 bytes. Notifications produce no response and cannot write.

## Source and SDK

- `main.flow`: native entry.
- `study.flow`: CLI routing, validation, browser rendering/actions, MCP routing.
- `lib/`: supplied starting SDK for typed bookings, storage, text, dates, forms,
  HTTP transport, JSON parsing and SHA-256. These are used directly by all three
  application interfaces; no alternate persistence engine is present.
- `http-test.flow`: test-only entry exercising the same native HTTP parser and
  application dispatcher through an inherited socket pair.
- `tests/selftest.py`: standard-library test driver, never used at app runtime.

SDK adjustments: missing file errno 2 maps to the task's not-found 404; the
journal ceiling and its buffers are 16 MiB rather than 1 MiB; the HTTP server's
4096-request lifetime cap is removed; the UI header is app-specific, without
unimplemented SDK navigation/appearance controls. Journal encoding, hashing,
locking, revision comparison and fsync confirmation remain the shared SDK's.

## Verification and limitations

Run:

```sh
./build.sh
python3 tests/selftest.py
```

Actual result in this trial: **PASS: 366 assertions**. Checks cover fresh-process
persistence, canonical/u64 IDs, Gregorian/time boundaries, adjacency/overlap,
room independence, insertion order, exact cancellation, concurrent writers,
lock refusal, all 256 reservation slots and reuse after cancellation, corruption
refusal, browser forms and Host/Origin/token/duplicate/unknown-field rejection,
failed-input retention, stale refresh, and MCP framing/schema/error recovery.

**This execution sandbox denies loopback bind with EPERM.** `serve` consequently
returns an error here. The test driver confirmed that bind restriction with a
separate socket probe and exercised HTTP through local socket pairs and the
native test entry instead. These tests passed, but a live TCP browser session,
ephemeral-port announcement, and visual browser inspection were not verified.
The socket-pair test uses a fixed test token; production uses `/dev/urandom`.
No unseen/controller acceptance tests or human trials are claimed.

The binary targets the supplied RF2 macOS arm64 systems profile and Darwin
syscalls, with ad-hoc code signing. It is not a portable Windows/Linux or Intel
binary. Storage is a regular single-link, no-symlink file with cooperative
flock locking and an append-only, digest-chained journal. The 16 MiB journal
ceiling is separate from the 256-current-booking ceiling; sufficiently many
edits can exhaust the journal. There is no compaction, migration or recovery UI.
Corrupt/incomplete journals refuse rather than silently resetting state. Keep
backups; this trial has no power-loss or hardware durability qualification.
Same-user hostile pathname replacement is outside the SDK's isolation model.
The server is local-only and has bounded requests/timeouts, not public hosting
or an authentication service.

Initial self-tests exposed missing-path error mapping and MCP multiline framing;
both were corrected before the passing run. Compilation also exposed RF2's
function-local name uniqueness and record declaration requirements; generated
sources now compile with the supplied ownership checker. The project continuity
files referenced by AGENTS.md were absent from this isolated trial. No remote
services, other workspaces, installs or delegated agents were used.
