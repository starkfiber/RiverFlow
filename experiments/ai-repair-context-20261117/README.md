# Multi-error RF2 repair context

`context.py` collects bounded lexical advice from explicitly supplied source. It
addresses construction mistakes found in actual DeepSeek C/CLI output: duplicate
function-local declarations, unsupported `break`, word `and`/`or` operators, inline
`else if`, and `try` in untyped functions. It also identifies keyword local names
and unterminated strings. Native compiler errors remain the acceptance authority.

```sh
python3 -B context.py main.flow --out new-context.json
```

The output binds the exact source SHA256 and includes one-based line/UTF8 byte
column, function name, bounded source context and a correction principle for each
advisory. Duplicate bindings include their earlier location. Inputs are at most
65,536 bytes, diagnostics at most128, and the observed count/truncation are
explicit. Output paths must be new. No code is rewritten or executed, no imports
are resolved, and importing the module has no operational effect.

The scanner masks quoted strings, escaped quotes/backslashes and `#` comments
before token inspection. Function parameter/local binding identities are tracked
independently per function. The known compiler's duplicate-local check is
function-wide; handler payload declarations participate in that name boundary.
Simple if/while/handle stacks avoid treating nested handler `end` as function end.

This is deliberately not a full parser, type/effect checker or permission gate.
Malformed headers, unusual grammar forms and missing/misbalanced ends can make
scope inference incomplete. An unterminated string suppresses following token
advice rather than guessing it is executable code. It does not detect every
unsupported form, undefined symbol, runtime logic error or API misuse. A clean
advice result is not a successful compile or correct program.

23 offline unittest methods pass, covering positive/negative syntax, comments and
strings, distinct functions, parameters, branch redeclarations, nested handlers,
whitespace, malformed input and bounded output. Project-local receipts are under
`artifacts/ai-repair-context-20261117/controls-1`. Actual C/CLI source inspection
is retained as `C-cli-round1.json`; its original provider source is untouched.

This is a new opt-in repair aid. Previous studies, frozen prompts/controllers and
their results are unchanged. Using this evidence in a new provider repair needs a
separately reviewed campaign amendment; it does not retroactively qualify an old
AI condition or establish token savings. No provider calls, Memory/KHC retention
or stable/default compiler changes occur here.
