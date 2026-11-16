# Passage Desk Python starting helpers

Use Python 3 and only its standard library. `text_sdk.py` and `mcp_sdk.py` are warm, supplied libraries. Neither contains the application entry, report assembly or renderer. Implement `app.py`, tests and README yourself. No shelling out to a prebuilt app or another language.

`from text_sdk import read_regular, measure, search`

- `read_regular(path, limit=1048576)` returns bytes after a bounded read of a regular file. It refuses final-component symlinks and nonregular files. It raises `OSError`/`ValueError` on failure. Parent directories are trusted.
- `measure(data: bytes)` validates strict UTF-8 and the task's text control policy, then returns a dict with `scalars`, `lines`, `words_ascii_breaks`. See TASK.md for precise definitions. Invalid data raises `UnicodeError`/`ValueError`.
- `search(data: bytes, query: bytes)` returns `matches` and `first_byte` (int or None), with overlapping exact-byte semantics, a validated 1..128-byte text query. Validate/measure the input first. It does not assemble a report.

Use `json.dumps` for complete JSON, `html.escape` for visible query text, `sys.argv` for application arguments, `sys.stdout`/`sys.stderr` for output. Python integers in this task stay within exact ordinary JSON bounds. Handle validation/read errors before emitting a success. Broken output transport may have emitted bytes; catch output errors where possible, no rollback claim.

`from mcp_sdk import serve`

`serve(server_name, version, tool_name, description, zero_arg_callback)` implements the supplied bounded legacy read-only protocol. The callback returns a dict or raises; the helper converts callback failures to `isError:true` tool results without successful structuredContent. It handles explicit empty arguments, initialization, refusals and later recovery. The callback must read only the launch-selected file, produce the exact report dict, and not print to stdout itself. The generic helper does not read files. No complete application entry is supplied.

No Python native compile is required. Deliver `launch.json` exactly `["python3","app.py"]` and test the actual commands. The installed interpreter is Python 3.9; avoid newer syntax/features. This native Mac comparison does not establish other-platform qualification.
