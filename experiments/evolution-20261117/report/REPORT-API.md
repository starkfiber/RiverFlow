# Report composition source API

Use `use "@rf2/v1/report.flow"`; dependencies include text and IO. No runtime
installation. This is one explicit candidate SDK supplied by the controller.
Do not redefine its records/functions. `Report(format:u64,fields:u64,state:u64)`:
construct `let report=Report(0,0,0)` and a Writer once per output, directly in the
function body. `report_begin(report,out,format,title,n)` opens the report; format0
JSON,1HTML. `report_text(report,out,name,n,value,m)` adds typed text;
`report_number(report,out,name,n,u64)` adds a number; `report_end(report,out)`
closes with LF. Use `do` for these calls, then check `out.error` before publishing.
Title, labels, values use explicit byte lengths; no implicit UTF8 or pointer length.
The writer owns no memory: caller supplies buffer/capacity, checks error and writes
through IO. State/refusal/capacity errors are sticky; no partial success is published
by a conforming caller. Up to1024fields, text at most1MiB, subject to caller output
capacity. UTF8/C0 validation and JSON/HTML escaping are library operations. It
emits the exact task's JSON/HTML shapes including typed array fields. No file read,
format detection, text counting or I/O is hidden inside the report API. Names
report_field/report_field_end are internal composition helpers, not app APIs;
do not mutate Report fields yourself or invent higher-level capabilities.
