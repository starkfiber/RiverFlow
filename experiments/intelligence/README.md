# RF2 compiler import guard and host intelligence experiments

Explicit source candidate on top of the exact 0.50 compiler. This does not
replace stable 0.17, published development downloads, the installed plugin, or
the frozen source preparers used to reproduce earlier compilers.

## Build and verify the real compiler correction

```sh
python3 experiments/intelligence/build.py QUALIFIED-050-COMPILER NEW-BUILD
python3 experiments/intelligence/import_verify.py \
  QUALIFIED-050-COMPILER NEW-BUILD/program NEW-IMPORT-EVIDENCE
```

The selected 0.50 compiler must match the documented SHA-256. The builder
reproduces its pinned source, extends the regular-file guard from SDK imports
to local imports, compiles/signs it, then checks signed self-generation with
identical image flags and executable basename. Failed builds retain logs.

Local imports previously opened an idle FIFO in blocking mode. The candidate
uses Darwin `O_NOFOLLOW | O_NONBLOCK` and `fstat` before reading. Nonregular
inputs close and refuse; SDK-specific refusal wording remains. This fixes the
observed local-FIFO wait, not arbitrary filesystem delays or hostile-host
containment. Parent directories remain trusted. No file-type check removes
concurrent regular-file mutation. The source budget and Core effects do not change.

## Host intelligence tools

```sh
python3 experiments/intelligence/harness.py capabilities TRUSTED-RF2-RUNTIME
python3 experiments/intelligence/harness.py inventory .
python3 experiments/intelligence/harness.py review ROOT CONTEXT.json RESPONSE.json
python3 experiments/intelligence/harness.py select-build MEASUREMENTS.json
python3 experiments/intelligence/test_harness.py
```

These are dependency-free Python **development controllers**, not new RF2
runtime dependencies or MCP effects. `capabilities` executes the explicitly
selected trusted runtime's status and MCP discovery, binding their actual
schemas to its binary hash. It never infers a hardware backend from a name.

`inventory` reads only Git-indexed `.flow`/`.rf2` paths. It refuses/records
nonregular files and leaf symlinks, caps individual files at1MiB, the selected
set at1000 files/8MiB, and marks lexical
declarations/effect leads. It is not a parser, SAST audit, complete data-flow
analysis or sandbox. The selected repository and ancestor directories are trusted.
Untracked files are deliberately outside coverage. Malformed UTF-8 refuses.

`review` requires a complete provider response, strict JSON, matching
context/source identities and valid source references. Duplicate keys, nesting
beyond32 levels, mismatched identities and out-of-range references refuse. Findings
remain hypotheses with a next test. It applies no patches, executes no model
commands and grants no authority. Empty findings mean only no proposals; they
do not establish security. Supplied context hashes are consistency checks, not
signatures or protection from a malicious same-user source/context replacement.
There is no model call, provider retry, retained remote session or automatic
publication in this tool.

The model content contract is:

```json
{"schema":"rf2.review-proposals.v1","contextSHA256":"SHA256_OF_CANONICAL_CONTEXT","findings":[{"path":"relative/file.flow","line":1,"sourceSHA256":"EXACT_SOURCE_SHA256","hypothesis":"Possible issue to investigate","nextTest":"Discriminating experiment"}]}
```

Canonical context bytes use sorted JSON keys, ASCII escaping and compact
separators, as implemented by `canonical`. Wrap that content string in a normal
provider `choices[0].message.content` with `finish_reason: "stop"`.

`select-build` uses paired `clean`/`cache` rows containing positive finite `ms`
and matching 64-character lowercase `sha256`. Five through 100 trials per
workload are required. It recommends an explicit reuse candidate only with at
least 10% median improvement and 80% paired wins. Otherwise it retains clean.
This is advisory, not compiler dispatch or a general performance guarantee.
Input receipts are trusted local experiment data, not authenticated benchmarks;
the caller still needs task/compiler/environment identity and hold-out validation.

WhatIF 3.1's built-in source scanner covers these Python controllers, not RF2
syntax. Native compiler behavior is tested with the explicit local controllers;
do not label their results as a built-in WhatIF native engine or libFuzzer run.
No production traffic, hardware flashing, inference or shared-memory write occurs.

See [reviewed results](../../docs/INTELLIGENCE-IMPORT-GUARD.md) and
[the prior paper audit](../../docs/PAPER-AUDIT-20261117.md).
