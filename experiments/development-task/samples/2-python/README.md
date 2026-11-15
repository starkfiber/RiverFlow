# Study Rooms

A local Python standard-library application with a CLI, browser forms and a read-only MCP stdio interface. All runtime application logic is Python. No dependencies or installation are needed. Tested with the supplied Mac Python 3.9 interpreter.

`launch.json` contains `["python3","app.py"]`. Run commands from this directory. Python does not require a native compilation step; syntax compilation is available with:

```sh
PYTHONPYCACHEPREFIX="$PWD/.pycache" python3 -m py_compile app.py booking_sdk.py test_app.py
```

## Run and example

Use a new filename for initialization:

```sh
python3 app.py init rooms.db
python3 app.py reserve rooms.db 1 1 1 2026-11-15 09:00 10:00
python3 app.py list rooms.db
python3 app.py cancel rooms.db 2 1
python3 app.py serve rooms.db
```

Initialization returns `{"revision":1,"bookings":[]}`. The example reservation returns revision 2 with `{"id":"1","room":1,"day":739935,"start":540,"finish":600}`. Cancellation returns revision 3 with an empty list. These operations are exercised in the self-tests (including reopening from separate processes).

`serve` prints its actual `http://127.0.0.1:PORT/` URL on its first line and serves until terminated. Open that URL in a browser. The selected existing workspace is fixed for the process. Forms show revision, readable dates/times and explicit cancellation buttons; failed reserve values are retained and current saved state is refreshed. The server uses a process-local random CSRF token and checks exact Host and Origin. No external assets or scripts are used. Stop with Ctrl-C.

The CLI accepts exactly:

```text
init DB
list DB
reserve DB REV ID ROOM DATE START END
cancel DB REV ID
serve DB
mcp DB
```

Successful operations emit the saved revision and insertion-ordered bookings as JSON. Failures exit 2 with `{"error":CODE}`. Codes include invalid 22, existing ID/path 17, not found 404, stale/overlap 409, busy 35; other storage failures remain failures. Capacity rejection is mapped from SDK code 27 to invalid 22; filesystem absence is mapped to 404. Review current state before retrying an uncertain storage outcome.

IDs are positive canonical decimal strings through u64 maximum. Rooms are 1–16. Dates require YYYY-MM-DD (years 0001–9999); times require HH:MM. Only end may be 24:00. Intervals are half-open and same-day; adjacent reservations are allowed. At most 256 current reservations. Writes require the exact saved revision; there is no automatic write retry.

## MCP

```sh
python3 app.py mcp rooms.db
```

Use one JSON-RPC object per line, with protocol version `2025-11-25` for initialize. Supports initialize, notifications/initialized, ping, tools/list and tools/call. The sole tool is `booking_list`, with an explicit empty arguments object:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"booking_list","arguments":{}}}
```

Results contain structuredContent with the same state as CLI list, plus short text content. Tool errors have isError:true. Duplicate decoded keys, malformed JSON, unknown tools/arguments and oversized lines are rejected; later valid requests remain usable. Lines are bounded to 65536 bytes. There are no write, path selection, execution or network tools and no stdout banner.

## Storage and limits

`booking_sdk.py` is the supplied domain/storage SDK and is unchanged. Every interface calls its `execute` function. It owns SQLite transactions, revision comparison, locking, durability, capacity and overlap rules. The persistent format is SQLite, not RF2. Keep the database on a writable local filesystem with SQLite locking support; back it up when no operation is active. The SDK rejects symlinks and multiple hard links. There is no migration, recurrence, timezone conversion, public hosting, authentication or hostile same-user isolation claim. The browser server is a simple single-process, sequential local HTTP server.

The interface includes responsive layout, keyboard focus styles and light/dark CSS with a basic fallback for older browsers. Visual rendering and a real browser session have not been verified in this environment.

## Self-test evidence

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_app
```

Final run: **6 tests discovered, 5 passed, 1 skipped**. Passing groups cover durable CLI state and ordering, date/ID/time boundaries, adjacent/overlapping intervals, stale revisions, cancellation, capacity, SDK busy locking, MCP malformed/duplicate/oversized input recovery and tool restrictions. Direct HTTP-handler tests cover GET rendering, reserve/cancel, stale refresh, retained input and rejection of bad Host/Origin/token/duplicate fields.

The live socket/browser integration test is retained but skipped because this execution sandbox rejects `bind(('127.0.0.1', 0))` with `PermissionError: [Errno 1] Operation not permitted`. It will run automatically where loopback binding is permitted. No successful live-server or visual-browser trial is claimed.

Initial verification failures are preserved in `SELF_TEST.md`. Syntax compilation passed with the cache directed inside this trial. No external acceptance tests were accessed or claimed.
