# Read-only CLI review and proposed supplemental acceptance

No frozen source was changed and no native build, provider call, or acceptance
execution was performed for this supplement. Python syntax was parsed only.

Source review found no immediate prefix-mode/OOB problem: `text_equal` rejects
length mismatch before reading bytes. Exact argc is required before argv loads.
Both IO callback failure and Writer error precede stdout; partial buffered output
must not escape. Native acceptance is still needed for those conclusions.

The lower-level `text_report_run` is trusted, unlike the argument-validating entry:
its callers must supply valid pointers and use the documented boolean option.
Static buffers and callbacks are deliberately not concurrent/reentrant or effect
restricted. The documentation already states this boundary; do not claim a sandbox.
A user name/path may be invalid UTF-8 on POSIX: shared report validation should
refuse output rather than emit invalid JSON. The original grader covers escaping,
not all invalid argv bytes; this supplement adds invalid mode/query bytes.

`boundary_grade.py` accepts an existing reviewed Task B CLI binary plus optional
separately compiled callback-error and writer-error fixtures. It exercises short
mode strings/suffixes, exact ASCII/multibyte 128-byte queries, 129-byte refusals,
malformed UTF-8/control input and callback/Writer failure with no stdout. Fixtures
are synthetic source only; compile only after the timing window is released.
The boundary oracle is separate and never changes frozen `grade.py`.

`study.py` plus `PROTOCOL.md` predeclare two fresh CLI-library calls, A then B,
without repair/retry. Freeze requires the qualified compiler, reviewed SDK root
already containing the exact CLI library, and historical study roots. Initial and
repair receipts, failed generation costs and raw provider usage stay separate.
Each call requires the reviewed FROZEN.json hash; each assessment separately
requires the reviewed returned source hash. Freeze itself performs no compilation
or provider request. Do not run call until root has reviewed the frozen inputs.

Proposed sequence after approval (fresh persistent output paths):

1. `study.py freeze --out ... --compiler ... --sdk-root ... --prior-study ...`
2. Review FROZEN.json and guide.md; supply its SHA256 to `call --approved-freeze-sha`.
3. `call --attempt 1`, review source, then guarded `assess --reviewed-sha`.
4. `call --attempt 2`, review source, then guarded `assess --reviewed-sha`.
5. `summary` preserves historical attempts/repairs and new condition separately.

No source-size saving, matched causal token claim, inferred missing usage, generic
hardware result or release follows. Correct complete software is the outcome.
