# RF2 0.29: checked reuse, lower overhead and working learning apps

## Implemented changes

The compiler uses guarded ARM SHA instructions for source/cache hashing, with a software fallback. The maintained Python reference encoder independently encodes the existing SHA block primitive; it and the prior native compiler produce matching default images. Native self-generation remains separately tested. Hardware paths and forced software paths match independent hashlib across padding boundaries, unaligned inputs and1MiB inputs. This is standard SHA-256 and standard ARM instructions, not new cryptography or transistor behavior.

Declaration-context hashing now walks source-ordered function spans once instead of scanning every function for every token. Reuse keys hash a bounded immutable raw function span directly. Diagnostic maps retain canonical token hashing; comments/whitespace inside a raw function conservatively miss its unit cache.

Reuse now supports scalar straight-line `let` and `set` statements before a final return. It excludes calls, memory operations, ownership, structured values, branches and loops. Misses fully validate the whitelist and normal compiler semantics before admission. Exact body bytes, declaration context, compiler-file identity and modes bind a previously checked eligibility result; a matching hit can reuse that result. Full lexical/declaration scanning and metadata checks still occur. This is memoized semantic eligibility in a trusted private cache, not an authenticated proof against a malicious owner.

RF2FN002 units have a104byte header and code payload. The digest covers length, exit offset, fixup offset, local count and code. Stored local count must match current scanning. Hits restore local readiness/scope and remap the exit branch to the current label. A miss clears capture permission and runs full validation; malformed or old units cannot inherit admission. Counters expose `validationReused` and `fullValidationChecks`. Per-unit code remains bounded to64KiB; larger bodies compile normally. `--functions` still uses normal generation so diagnostic maps match clean maps.

Use the same explicit private-directory CLI from [0.28](FUNCTION-REUSE-0.28.md); this version supersedes its single-expression-only admission and every-hit-body-parser description. Private UID/mode/link checks, locks, exclusive output creation, same-UID trust limits and nontransactional sidecar publication remain. Native MCP still has nine bounded tools and admits no systems compilation or arbitrary network/filesystem effect.

## Complete compilation measurements

Twenty-one rotated trials on one Mac, warm filesystem. Median milliseconds include compiler startup, hashing/validation, selected cache I/O and new output creation. Signing and application execution are outside the timer. All outputs match fresh clean images. Initial cache population is separate from warm reuse.

| Task | Clean | Empty function cache | Warm function cache |
| --- | ---: | ---: | ---: |
| small-example | 1.800 | 2.235 | 2.031 |
| file-checksum | 2.629 | 2.966 | 2.889 |
| sha40 | 30.435 | 51.520 | 6.173 |
| numeric-helper-fixture | 4.948 | 15.940 | 4.748 |

The larger SHA40 workload improved from30.435 to6.173ms (about4.93x). Small examples remain slower with function caching; the numeric-helper fixture's advantage is small. Paired intervals and all trials are retained, including regressions. This does not establish a language-wide performance score.

Actual entry-function code edits, retaining SHA40 kernels, measured clean44.405ms versus reuse7.718ms (about5.75x). Every edited image matched clean bytes, every accepted40byte message matched a complete independent digest, and the changed error code was executed and checked. Candidate-minus-clean paired bootstrap interval: -32.021 to-28.072ms. These are compilation results, not hashing throughput, provider bills or energy measurements.

[All compile trials](FUNCTION-REUSE-0.29-MEASUREMENTS.json) · [paired analysis](FUNCTION-REUSE-0.29-ANALYSIS.json) · [actual partial edits](FUNCTION-REUSE-EDIT-0.29-MEASUREMENTS.json).

Explicit [compiler stores](COMPILER-STORE-0.28.md) remain useful across new project caches. Current measurements retain first-ever setup separately; it is not eliminated. [Store trials](COMPILER-STORE-0.29-MEASUREMENTS.json).

## Real applications and failure correction

[Number Lab CLI](../examples/number-lab/) and [browser playground](../examples/number-lab-web/) calculate binary, hex, ASCII and Boolean gates, with quizzes and recovery. The browser app serves self-contained HTML/CSS from native RF2 on a private loopback port. It is not AppKit/Tkinter or a public service. Actual browser testing caught a POST Origin refusal that HTTP mocks missed. ReferrerPolicy:same-origin fixed browser compatibility while strict Origin/token/revision checks stayed enforced. Desktop, keyboard and390px responsive checks passed. No education-effectiveness study is claimed.

[SHA40](../examples/sha40/) computes complete SHA-256 digests for exactly40bytes using readable scalar rounds. Its four helpers intentionally recompute compression for separate output pairs. It is a substantial compile/reuse workload, not a recommended crypto library or runtime optimization. Optimized helpers fit64KiB; default ones exceed it and correctly fall back. Independent full-digest and refusal controls cover both routes.

## Qualification and scope

81 base reuse cases,172 extended eligibility/state/corruption cases,1,196 hash cases,51 CLI app scenarios and117 HTTP app scenarios passed. Memory/ABI, guest probes, compact images, target caches, native runtime corpus and official MCP SDK checks remain separately recorded. The connected WhatIF runner passed32 bounded GET probes and7file hash verification. It did not certify security or capacity. The final-candidate randomized campaign passed792 generated scalar programs plus their changed-entry variants before its declared deadline. An earlier1,060-program run used a superseded candidate and is retained separately, not added to final-candidate coverage.

[Base reuse](FUNCTION-REUSE-0.29-VERIFICATION.json) · [extended reuse](FUNCTION-REUSE-0.29-EXTENDED.json) · [hash](COMPILER-HASH-0.29-VERIFICATION.json) · [native integration](NATIVE-0.29-INTEGRATION.json) · [CLI](NUMBER-LAB-0.29-VERIFICATION.json) · [HTTP](NUMBER-LAB-WEB-0.29-VERIFICATION.json) · [browser](NUMBER-LAB-BROWSER-0.29.json) · [WhatIF](NUMBER-LAB-WHATIF-0.29.json) · [SHA40](SHA40-0.29-VERIFICATION.json) · [fresh workload campaign](FUNCTION-REUSE-STRESS-0.29.json).

Three actual AI subagents handled hashing, adversarial review/tests and applications. They are not100 agents or human platform/academic approvals. Qualification remains Apple Silicon macOS. Existing bounded Core/WASM and process-owned Hypervisor controls do not prove Linux boot, Windows compatibility or arbitrary GUI parity. No complete AI-generation/token-billing experiment or electrical-energy saving was measured. Future work includes broader symbolic call/object reuse, batching small-unit I/O, integrated cold-build paths, platform implementations and controlled AI-task trials.
