# Typed reports and verified authoring context

This is a reusable source library, not a separate model or runtime. Import
`@rf2/v1/report.flow` from the explicitly generated combined SDK. Use only the
public begin/text/number/end functions documented in REPORT-API.md; internal
field helpers and direct record mutation are not an adversarial safety boundary.
The caller owns buffers and I/O, inspects Writer.error before publishing, and
must start with a fresh Report and Writer. `report_begin` appends; it does not
silently reset a caller's existing output. Text must be readable for its declared
length; raw pointers remain trusted Systems inputs.

```sh
python3 experiments/evolution-20261117/package.py /new/sdk
/qualified/rf2c experiments/evolution-20261117/report/file-summary.flow /new/app --compact --opt --sdk-root /new/sdk
codesign -s - /new/app
/new/app json /selected/synthetic-input.txt
```

`verify.py --compiler /qualified/rf2c --out /new/checks` checks JSON/HTML bytes,
UTF8, states and capacity in both compiler modes; `--accelerated` additionally
stages the span writer. `grade.py --binary /reviewed/app --out /new/grade` tests
the complete frozen file-summary task with synthetic files and real descriptor
faults. No native code was added to the Core MCP authority.

`context.py --compiler /qualified/rf2c --sdk-root /new/sdk --out /new/context`
emits API+style context only after explicit manifest identity checks and native
syntax admission. This is not a signed statement, a code-execution sandbox or a
provider productivity result. It supports the flat module set of this SDK,
not arbitrary package layouts. The 2,029-byte card was native checked; the exact
card has not undergone a separately frozen model comparison.

## Bounded provider experiment

PROVIDER-TASK.md and the same starting language guide defined the four frozen
manual/report/report/manual requests. `provider.py` accepts only attempts1..4,
creates exclusive result directories and makes no automatic retries. Separate
`reasoning.py repair|review` adds exactly one directory per role. Six requests
were run in this campaign. Calls use direct DeepSeek completion endpoints through
an explicitly configured authorized SSH host; credentials remain on that host.
Set RF2_PROVIDER_SSH_HOST and RF2_PROVIDER_REMOTE_ENV_FILE yourself. The latter
names a remote protected file containing OPENAI_API_KEY; never put its contents
or credentials into source, context, Memory or command output.

Provider calls return proposed source/JSON only. They do not compile or execute
model commands. Root manually reviewed each relevant source and used the pinned
compiler; only the successfully compiled reviewed repair was executed against
synthetic files. All four original attempts failed compilation. The separate
V4-Pro repair passed37/37functional checks. No reduction in tokens, developer
time or repaired-success effort has been established.

Historical test-instrumentation failures remain in local artifacts: run2's
3-second launch timeout and first grader's Linux-only /dev/full assumption.
The same optimized binary later completed in2.2ms; interruption cause unknown.
Subsequent fresh controls use explicit10-second observation budgets, read-only
stdout and broken pipes. Do not delete failed directories or relabel repairs as
original-attempt successes. Raw requests/provider usage stay project local.
