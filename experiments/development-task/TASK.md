# Frozen task: Study Rooms

Build a complete local study-room reservation application with CLI, browser GUI and read-only MCP access. The application must run on this Mac. Work only inside this isolated trial directory. Do not read other workspaces, authentication files, remote services or prior attempt outputs. Do not publish or install packages. No invented results, token estimates, human trials or speed claims. Use the supplied SDK and the stated language; do not delegate to another implementation language or shell out to a prebuilt application.

The room model is positive canonical decimal-string u64 IDs, rooms1..16, Gregorian dates0001-01-01 through9999-12-31, and half-open same-day 24-hour minute intervals. Adjacent bookings are allowed; overlapping bookings in the same room/day refuse. Different rooms/days are independent. End24:00 is allowed only as end of day. Dates/times must use exactly YYYY-MM-DD/HH:MM. At most256 current reservations. No timezone conversion or recurring bookings.

## Launch contract

Write launch.json containing one JSON array of command words, relative to this directory, for the executable entry. RF2 must compile a native app named app and use ["./app"]. Python uses ["python3","app.py"] with only the standard library. No shell wrapper. The grader appends the following arguments:

- `init DB`: exclusively create a new workspace, refuse existing paths.
- `list DB`: return the current revision and all saved bookings.
- `reserve DB REV ID ROOM DATE START END`: validate, compare the saved revision, reserve one room, return updated saved state.
- `cancel DB REV ID`: compare revision, cancel the exact ID, return updated saved state.
- `serve DB`: serve only the selected existing workspace on127.0.0.1, an ephemeral port, and print its exact http://127.0.0.1:PORT/ URL as the first line. Keep serving until terminated.
- `mcp DB`: newline JSON-RPC stdio server, the selected existing workspace only; never print a banner to stdout.

Successful CLI JSON is {"revision":N,"bookings":[{"id":"1","room":1,"day":ORDINAL,"start":540,"finish":600},...]}. The initial revision is1. The SDK may also return its numeric version field; no other extra fields. Preserve insertion order; cancellation removes just that row. Operation failures exit2 and print {"error":CODE} JSON on stdout. Codes: invalid22, exists17, not-found404, conflict/stale409, busy35. Other storage errors must remain failures, never success. CLI runs in fresh processes and durable state must survive reopening. Do not bypass SDK locking/revision rules.

## Browser interface

GET / shows the saved reservations and visible labelled room/date/start/end inputs. Provide a usable responsive layout, focus styles and readable light/dark CSS. No external network assets/scripts. A reserve form POSTs to /action with exactly fields action=reserve,rev,id,room,date,start,end,token. A cancellation form POSTs to /action with action=cancel,rev,id,token. Forms include the current revision and an unpredictable process-local CSRF token. Cancellation must be an explicit button. Date/time values are user-readable strings.

Check Host and POST Origin against the actual loopback endpoint. Invalid token/origin, duplicate/unknown fields and malformed input must not modify data. Success and storage/overlap errors must be visible, with useful instructions. Retain failed reserve input. Refresh actual saved state after a stale form. Both browser operations use the same domain/storage SDK as the CLI. No public internet server or authentication claim.

## Read-only MCP interface

Support legacy2025-11-25 initialize, notifications/initialized, ping, tools/list and tools/call over stdio. Advertise exactly one tool `booking_list`, inputSchema object/no properties/additionalProperties:false. Calls accept an explicit empty arguments object; return the selected workspace state as structuredContent and a short text content. No write, arbitrary path, source execution, network or migration tool. Unknown methods/args, malformed JSON and duplicate decoded keys refuse. A tool-call notification cannot mutate data. Keep the connection usable after a rejected request. Request lines bounded to65536bytes. Tool errors use isError:true rather than claiming success.

## Delivery

Write README.md explaining build/run, one working example, storage/portability limits and the provided SDK. Keep all generated source and tests. Build and run your own checks before finishing. The controller runs separate frozen acceptance tests afterward; never edit its files or claim to have passed an unseen test. No changes outside this trial, no GitHub writes, no remote Memory or shared compute. Stop when the complete app and your tests are delivered. You have one bounded attempt, no human repairs during it.
