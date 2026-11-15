# Study Rooms

A Python standard-library application with CLI, server-rendered browser forms and read-only newline JSON-RPC MCP. All application runtime logic is Python. The supplied `booking_sdk.py` remains unchanged and owns domain validation, SQLite transactions, locking, revision comparison and durable persistence. `app.py` adds canonical calendar/time parsing and the three frontends.

## Build and run

Use Python 3.9 or newer. No install or package download is needed. Run commands from this directory. `launch.json` contains `["python3","app.py"]`.

```sh
PYTHONPYCACHEPREFIX="$PWD/.pycache" python3 -m py_compile app.py booking_sdk.py test_app.py
python3 app.py init rooms.db
python3 app.py reserve rooms.db 1 1 3 2026-11-15 09:00 10:00
python3 app.py list rooms.db
python3 app.py cancel rooms.db 2 1
python3 app.py serve rooms.db
```

The reserve example returns revision 2 with one booking: `{"id":"1","room":3,"day":739935,"start":540,"finish":600}`. Cancel returns revision 3 and an empty list. Initializing an existing path refuses. Each command is a fresh process; use the last saved revision for a write.

`serve` prints its exact `http://127.0.0.1:PORT/` URL first and serves until terminated. Open that URL in a browser. The browser shows readable dates/times and explicit cancellation buttons. Forms carry the current revision and a random process-local token. Failed reservation values are retained, and the saved state is reread after every submission. Check the displayed error and refreshed revision before retrying. POSTs require the exact endpoint Origin and Host; opening via alternate hostnames is intentionally refused.

CLI failures print `{"error":CODE}` and exit 2. Standard codes are invalid 22, exists 17, not-found 404, stale/overlap 409 and busy 35. Capacity exhaustion maps the SDK's 27 to invalid 22; missing paths map 2 to 404. Other SDK/storage errors remain errors, including corruption 9001 and uncertain outcomes 9002. Read current data before retrying uncertain outcomes.

## Read-only MCP

```sh
python3 app.py mcp rooms.db
```

Send one UTF-8 JSON-RPC object per line, for example:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"local-client","version":"1"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"booking_list","arguments":{}}}
```

The sole tool returns the selected workspace state as structuredContent plus short text. It accepts exactly an explicit empty arguments object. There is no path selection or write tool. Ping is supported. Duplicate decoded keys, malformed JSON, unknown methods and invalid arguments refuse; valid later lines remain usable. Request lines are limited to 65536 bytes, including newline. Notifications receive no response. Storage failures in tool execution return `isError: true`.

## Storage and limits

The DB is a SQLite file, not an RF2 journal. IDs are canonical positive decimal u64 strings; rooms range 1–16; dates range 0001-01-01 through 9999-12-31. Intervals are half-open, same-day minutes; end `24:00` is allowed. Adjacent bookings are allowed, overlaps refuse, and at most 256 current reservations are stored. Saved order is insertion order. SQLite files may be moved between compatible Python/SQLite environments while the application is stopped; keep the DB and any transaction sidecars together after an interrupted write and let SQLite recover them. Back up only a quiescent workspace or use SQLite-aware backup tooling.

This is a local loopback server, with no public hosting or authentication claim. It does not claim isolation from a hostile same-user process. It uses a single-thread HTTP server; it is intended for local interactive use, not untrusted network traffic. No timezones or recurring reservations are implemented. Modern CSS light/dark support provides theme adaptation with readable light fallback. Visual rendering, accessibility with assistive technology and human usability have not been manually qualified.

## Actual verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 test_app.py
```

Final run: **5 test groups, 4 passed, 1 skipped**. Passing coverage includes fresh-process persistence, canonical input, date/time limits, overlap/adjacency, insertion order, stale revisions, cancellation, capacity 256, SQLite write-lock busy errors, HTTP handler rendering and POST checks using in-memory streams, MCP initialization/list/read, duplicate JSON keys, oversized-line recovery and invalid arguments.

The live HTTP test was attempted but the execution sandbox denied loopback socket bind with EPERM. `serve` returned exit 2 and `{"error":1}`; no live browser or real-socket HTTP success is claimed. The in-memory test invokes the actual HTTP request handler but cannot establish socket-level behavior. It automatically skips the live test only for that explicit bind error.

Compilation succeeded with the cache redirected inside this directory. The first compile attempt failed because this environment's default Python cache points outside the permitted workspace. An initial in-memory HTTP test exposed a percent-sign formatting bug in CSS; that was corrected and the test rerun successfully. No external acceptance tests were accessed or claimed.
