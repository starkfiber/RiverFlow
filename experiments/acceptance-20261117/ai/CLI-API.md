# Shared text-report CLI source SDK

Import `@rf2/v1/text-report-cli.flow`; it includes text, IO and Report dependencies.
Implement exactly `fn text_report_fields(input:TextReportInput,report:Report,out:Writer):IO`.
This callback is called once synchronously after validated input and report_begin.
Append ordered typed fields using report_text/report_number; return ok(0) or err(code).
Do not call report_begin/report_end, read files, parse args, reset Writer/Report or
write stdout in the callback. Native library owns that shared flow and checks errors.

TextReportInput's scalar fields are path (NULterminated argument), query (0when
absent, otherwise NULterminated validated1..128byte query), data (read-only input
pointer), size (byte count), format (0JSON/1HTML), lines/words (TextInfo metrics).
Use io_size on path/query, never on data; use input.size. No methods. Use existing
TextCursor/TextSpan or TextPrefix/TextMatches in callback for task-specific work.
All record locals still belong at function-body root, outside branches.

`fn main(argc,argv)` returns `text_report_entry(argc,argv,TITLE,TITLE_BYTE_LENGTH,QUERY_REQUIRED)`.
QUERY_REQUIRED0means exact `app json|html PATH`;1means `app json|html PATH QUERY`.
The library validates args/mode, bounded4096byte regular input/no symlink/FIFO,
UTF8/C0 and optional query; builds a32768byte output; handles checked output/short
writes/no-SIGPIPE with explicit nonzero failure. It adds LF and the same exact
Report JSON/HTML shapes. Title/path/text escaping stays centralized.

Trusted single-invocation Systems library with static buffers, no concurrent/reentrant
guarantee, sandbox, new Core MCP tool or arbitrary callback-effect enforcement.
Inputs/records must not escape the synchronous callback. This API removes shared
CLI plumbing; it does not calculate longest lines, search matches or invent fields.
