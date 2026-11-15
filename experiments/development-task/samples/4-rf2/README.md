# Study Rooms in RF2

A local reservation application with JSON CLI, browser forms and read-only JSON-RPC MCP. All application runtime logic is RF2. `main.flow` is the entry point; `application.flow` implements validation, CLI commands, HTML rendering, form actions and MCP. `launch.json` selects the compiled native `./app`.

Build on this Mac with the supplied compiler and Apple's existing signing tool:

```sh
./rf2c main.flow app --opt
/usr/bin/codesign -s - app
```

The delivered `app` is already built and ad hoc signed. The compiler refuses to overwrite an existing output: remove the generated `app` before rebuilding it. No packages, downloads or remote services are needed.

Try a new filename (initialization refuses any existing path):

```sh
./app init artifacts/example.db
./app reserve artifacts/example.db 1 1 2 2026-11-15 09:00 10:00
./app list artifacts/example.db
./app cancel artifacts/example.db 2 1
./app serve artifacts/example.db
```

The reserve result is:

```json
{"revision":2,"version":2,"bookings":[{"id":"1","room":2,"day":739935,"start":540,"finish":600}]}
```

`serve` prints `http://127.0.0.1:PORT/` as its first line, using an ephemeral loopback port. Open that URL in a browser. It serves the selected existing workspace until terminated; use Ctrl-C to stop. This environment denies listening socket binding, so live listener startup was not verified here. It currently returns `{"error":5}` with exit 2 under that restriction. The native HTTP parser and browser handlers were tested using inherited local socket pairs instead.

The responsive HTML has room/date/start/end controls, visible saved reservations, explicit cancellation buttons, keyboard focus styles and system light/dark CSS. Failed reservation values are escaped and retained; stale forms display actual saved state and a fresh revision. Forms enforce the actual endpoint Host and POST Origin, a random process-local CSRF token, exact field sets and duplicate rejection. The app loads no external assets. It is a local tool, with no authentication or public-hosting claim.

CLI commands use the task's argument order:

```text
init DB
list DB
reserve DB REV ID ROOM DATE START END
cancel DB REV ID
serve DB
mcp DB
```

Successful CLI output contains `revision`, the SDK's numeric journal `version`, and insertion-ordered `bookings`. IDs are positive canonical decimal u64 strings, rooms are 1–16, dates are exact Gregorian YYYY-MM-DD, and times are exact HH:MM. Same-room, same-day half-open intervals cannot overlap; adjacent intervals are allowed. Only an end time may be 24:00. At most 256 current reservations are accepted. No recurrence or timezone conversion occurs. Cancellation removes exactly the matching ID. Mutations compare the supplied revision under the SDK lock. Failures print only `{"error":CODE}` and exit 2; invalid input is 22, existing/duplicate ID is 17, missing is 404, stale/overlap is 409, and lock contention is 35. Other storage failures keep distinct numeric errors and never report success.

MCP uses newline-delimited JSON-RPC on stdin/stdout, with no banner:

```sh
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"example","version":"1"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"booking_list","arguments":{}}}' | ./app mcp artifacts/example.db
```

Supported methods are initialize (2025-11-25), notifications/initialized, ping, tools/list and tools/call. Exactly one tool, `booking_list`, accepts an explicit empty arguments object and returns saved state as structuredContent plus a brief text item. Tool failures use isError. There are no write/path/execution tools. Malformed JSON, duplicate decoded keys and lines over 65536 bytes are rejected; subsequent lines remain usable. Notifications produce no response or mutation. No batch JSON-RPC API is offered.

The supplied libraries remain the domain/storage foundation, rather than a prebuilt app: `booking.flow` owns typed row rules; `store.flow`, `storage.flow` and `sha256.rf2` implement locked, revisioned, digest-chained snapshots; `datetime.flow` parses/formats Gregorian dates and minute intervals; `forms.flow`, `transport.flow` and `app-server.flow` implement bounded HTTP I/O and token/form parsing; `ui.flow` supplies reusable CSS and rendering helpers; `json.flow` supplies bounded UTF-8 JSON parsing. Application handlers use this same storage engine for CLI and browser operations, and its read path for MCP.

Trial-local SDK edits enlarge journal allocation/admission from 1 MiB to 4 MiB, allowing a sequence of 256 reservations to reach the stated current-row capacity. The serialized journal format, lock behavior, digest chain and revision checks are unchanged. The server's supplied 4096-request lifetime cap was removed. The SDK's extra recovery/migration actions are not exposed by this app.

Storage is a native binary append-only snapshot journal, not JSON or SQLite. Each successful mutation adds a snapshot, so the 4 MiB journal limit can be reached even with few current reservations. Such writes fail; no compaction, migration or recovery command is exposed. Preserve the file and use a new workspace when needed. The SDK refuses symlinks and non-regular/multiply-linked workspace files. Its cooperative file locking does not defend against hostile same-user pathname replacement. Hardware power-loss durability was not independently qualified. The compiler profile and syscall layouts target this Mac's Darwin/ARM64 environment; Linux, Windows and Intel execution are not qualified. File-format interchange with other implementations is not promised.

Self-tests are local black-box checks. Python is used only as a standard-library test driver, never for application runtime. `http-selftest.flow` is a separate RF2 test entry that feeds the same production HTTP parser/handlers through an inherited descriptor, using a fixed token/endpoint only in that test executable. Production `app` does not import this test entry and obtains random tokens from the OS.

```sh
./rf2c http-selftest.flow http-selftest --opt
/usr/bin/codesign -s - http-selftest
python3 selftest.py
```

Remove the generated `http-selftest` before rebuilding it. The delivered binaries were rebuilt after the final source changes. The final run passed **30 checks**, including 12 invalid-input cases inside one check, fresh-process persistence, revision/overlap refusal, exact cancellation, lock contention, concurrent writers, the 256-row boundary, corrupt storage refusal, MCP framing/recovery/admission, HTTP Host/Origin/token/field checks, browser saves, retained stale inputs and cancellation. See `artifacts/selftest.txt`.

Earlier failed runs are preserved in `artifacts/`: the compiler initially refused overwriting an existing binary, which left the old binary's multiline MCP output under test; rebuilding corrected that. Listener testing then encountered the sandbox bind denial. A later HTTP harness assertion incorrectly assumed every HTML name attribute was unquoted; the assertion was corrected to accept valid quoted attributes. Early RF2 compile errors about local declarations and explicit result handling were corrected before the first executable was produced.

Limits of verification: no live listener/end-to-end browser navigation, visual screenshot inspection, human trial, hardware durability test, or other-platform run was performed. Socket-pair HTTP checks do not qualify the accept/poll listener loop. The separate frozen acceptance tests have not been seen or run.
