# Python trial SDK

Use Python3 and only the standard library. booking_sdk.py is the frozen conventional domain/storage SDK, backed by SQLite. Modify it only inside this trial if necessary; all modifications count as generated work. No complete CLI/GUI/MCP app entry is supplied. Use the standard datetime, json, http.server, html, secrets, urllib.parse, threading, sqlite3 and other standard modules as needed. No pip installs or third-party framework/network dependencies.

`from booking_sdk import execute, BookingError`

`execute(path, action, expected=0, id=None, room=0, day=0, start=0, finish=0)` returns `{"revision":N,"bookings":[...]}` after successful commit/read, or raises BookingError with numeric `.code`. Actions are init/list/reserve/cancel. ID is a canonical decimal string; room, day(ordinal), start/finish(minutes) and expected are ints. SDK validates nominal business rules, capacity, expected revision and performs an atomic SQLite transaction. A caller must not issue success before execute returns. The persistent format is SQLite, not the native RF2 journal. Read current data before retrying any uncertain outcome. Public server/authentication and hostile same-user path isolation are not claimed.

Construct a complete app frontend following TASK.md. Python datetime.date has fromisoformat(), toordinal(), fromordinal(), with range1..9999; require canonical source spelling yourself. For times use explicit HH:MM validation and allow24:00 only for end. Error codes from SDK: invalid22, exists17, notfound404, conflict/stale409, busy35, corrupt9001 and uncertain9002.

http.server.HTTPServer plus BaseHTTPRequestHandler can bind127.0.0.1, port0 and expose server_address. Request processing, exact field validation, Host/Origin/token checks and form retention remain your responsibility. Use secrets.token_hex(16) for an unpredictable process-local token and html.escape for user-supplied text. urllib.parse.parse_qsl with strict/duplicate checks can parse bounded forms. Build a readable responsive labelled GUI, no external scripts/fonts/assets.

For read-only MCP use newline-delimited JSON RPC over stdin/stdout, initialize2025-11-25 then notifications/initialized, ping/tools/list/tools/call. Python json.loads supports object_pairs_hook for duplicate-key rejection. Validate explicit empty arguments and never accept path/source/network/mutation tools. Tool results include text content and structuredContent, operation failure isError:true. Bound input lines65536 and keep valid later requests usable after refusal. No complete MCP application entry is supplied.
