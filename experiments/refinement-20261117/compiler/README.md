# Source-context diagnostic hints

The previous model-generated programs failed on two real syntax errors with only
“expected newline” or “unsupported statement” feedback. This source-bound compiler
candidate preserves those messages and rejection behaviour, adding specific
advisory codes/hints only when the parser cursor proves the relevant spelling:

- `RF2E_TRY_STATEMENT`: a bare identifier-token `try` in statement position.
  Inside an IO function use `do try ...` to discard success or `let value=try ...`;
  scalar callers need explicit `handle` branches.
- `RF2E_ELSE_IF`: “expected newline” with current identifier `if` immediately
  after identifier `else`. Put the nested `if` on the next line and close both
  blocks. It does not silently admit new grammar.

Every token read is guarded by parser phase, token count and kind. Early CLI,
source-read, lexical and generic errors retain their categories. Ordinary invalid
statements still have `RF2E_COMPILE`; the generic fallback is not relabelled as
one particular fix. The JSON schema stays rf2.diagnostic.v1; consumers must treat
hints as advice rather than executable instructions or an automatic repair.

`prepare.py` requires explicit qualified 0.50 source, verifies its hash, applies the
already-reviewed import guard, verifies that intermediate identity, then adds only
these diagnostic cases. It does not modify default builders, release source or
Core/MCP authority. `build.py` requires the pinned native compiler and records exact
self-generation with identical output basenames. Source/logs stay persistent;
reproducible images live in the guarded work cache. An initial comparison used
different basenames, creating different ad-hoc signing identifiers: all differences
were proven inside LC_CODE_SIGNATURE and preserved before the corrected replay.

Executed: 40 focused human/JSON rejection and corrected-program controls, all169
existing diagnostic-wire/boundary controls through a path-only adapter, byte-equal
valid app output and signed self-generation. No model call used this candidate;
there is no measured claim that these hints reduce AI tokens. Stable/default
compiler/runtime files are unchanged.
