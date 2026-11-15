# Typed Booking 0.45 development application

A real native application using the recursive owned-value compiler from [candidate 0.44](../nested-owned/README.md). CLI, loopback browser GUI and bounded stdio agent server import the same Booking rules and typed persistence engine. This is local cooperative storage, not a public reservation service.

```sh
sh tools/build-typed-booking.sh SELECTED-0.44-rf2c NEW-BUILD --opt
NEW-BUILD/booking /absolute/path/to/new.db init
NEW-BUILD/booking /absolute/path/to/new.db list
NEW-BUILD/booking-web /absolute/path/to/new.db
NEW-BUILD/booking-agent /absolute/path/to/new.db
```

Builds require ordinary macOS signing tools; user execution has no Node/npm/Python runtime. Open the GUI URL printed by the native server. The agent is read-only unless explicitly launched with `--write`. Each process has one selected journal; tool arguments cannot change paths, execute source, initialize/migrate/recover files or use a network URL.

The CLI accepts `init`, `init-v1`, `list`, `add REV ID ROOM DAY START FINISH`, `cancel REV ID`, `migrate REV` and `recover REV`. Dates use Gregorian ordinals; times use minutes within one day. IDs are positive u64, represented as JSON strings. There are 16 rooms, at most 256 current reservations and a 1 MiB append-only journal limit.

`lib/booking.flow` defines typed rows and shared validation. `lib/store.flow` validates every snapshot and serializes access through a cooperative file lock and revision check. `lib/ui.flow` supplies reusable server-rendered components. `lib/json.flow` is a namespaced extraction of the existing bounded native JSON parser. `tools.json` records the exact advertised schemas; qualification compares them with actual server responses.

[Full contract, failure cases and executed evidence](../../docs/TYPED-BOOKING-0.45.md). No invented reservations, human learner trial, power-loss trial, general security proof, speed or token improvement is claimed. Test reservations are controller-generated fixtures.
