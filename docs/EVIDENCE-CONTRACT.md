# Evidence Contract: challenge output before publishing it

Research candidate built with the unchanged RF2 0.17 native compiler. This is a bounded native application written in RF2, not five new compiler keywords. The public 0.17 download remains unchanged. Original author: Ilangkhumanan Thirunavokkarasu. Publisher: SFE.

## Five mechanisms, one experiment

| Hypothesis | Implemented mechanism | What would disprove it |
| --- | --- | --- |
| H1: readable authority and work contracts can be enforced | Closed ADD/XOR/REVERSE vocabulary; masks, operands and abstract cost checked before executing | A denied operation or excessive budget executes |
| H2: rejected transformations preserve state | Private reference and candidate buffers; commit only after full agreement | Any rejected plan changes any original byte |
| H3: independent computation catches candidate errors | Reference pass per operation versus candidate fused per output byte; compare every active byte | A deliberately different candidate publishes success |
| H4: evidence identifies the computation | Domain-separated SHA-256 over source identity, exact plan bytes, output and result fields; separate build manifest identifies compiler and executable | Changing a bound field retains the same independently reconstructed receipt |
| H5: stale evidence fails and failures can be replayed | Self-contained RF2C1 capsule or exact plan plus JSON witness, source identity and optional expected receipt; each invocation is a fresh process | Changed inputs reuse old successful evidence, or the same pinned implementation reproduces a different witness |

All five mechanisms have prior art. See [independent hypothesis review](FIVE-HYPOTHESES-REVIEW.md), including effect systems, transactions, translation validation, build provenance and deterministic replay. The research question is whether their compact integration improves practical repair and review. No world-first, new transistor instruction, universal safety, speed or token advantage is established.

## Build and run

The development builder needs Python's standard library, the already built native compiler and macOS codesign. The resulting executable needs none of Python, Node, npm or C++. The compiler is not replaced by another language runtime.

```sh
python3 tools/build-contract.py output/bin/rf2-contract --opt
output/bin/rf2-contract examples/evidence-contract/demo.plan
```

The builder refuses an existing output. To rebuild, choose a new filename. Its adjacent `.build.json` records the compiler hash, executable hash and every admitted source file. It regenerates the source identity module before compiling. A direct compiler invocation after editing source without refreshing that module can produce stale identity; use the builder and verify its manifest.

The demo plan is deliberately short:

```text
RF2E1
allow 7
budget 18
input 3 1 2 3
steps 3
add 5
reverse
xor 2
```

It returns `[10,5,4]`, code 0 and work 18. Operations have permission bits ADD=1, XOR=2 and REVERSE=4. Only set bits grant those operations. ADD is checked byte addition; XOR uses a byte operand. REVERSE has no operand. At most 128 input bytes and 32 operations are admitted; the file is capped at 8192 bytes. Decimal numbers are canonical unsigned 64-bit values with no leading zeros except `0`. The parser accepts ASCII space, tab, CR and LF, exact field order and no comments or trailing tokens.

This can preview a small binary-data transformation without overwriting its input. It is not a general document editor, file transaction service, operating-system sandbox or authorization system.

## Error and commit contract

| Code | Meaning |
| --- | --- |
| 0 | Two executions agree and output is available |
| 1 | Invalid plan, authority mask or operand |
| 2 | Operation permission denied |
| 3 | Budget below the required abstract work |
| 4 | Reference checked byte addition overflow |
| 5 | Candidate disagrees with reference |

Parser and I/O errors have a JSON `error` string and nonzero exit status. Engine errors include the first relevant step/index, expected/actual values, work, complete original input and unchanged output. The process exit code is not used to encode the full witness. Preflight runs before transformation. A valid reference result is required before candidate comparison.

The reference visits each operation over the full array. The candidate chooses each source element using total reversal parity and applies uniform pointwise maps in sequence. Global reversal commutes with these uniform maps. Other operations are not automatically eligible. Full-byte comparison occurs before the only writes to the engine's caller array.

The budget is `2 * input_count * steps`: an abstract element-operation measure across both paths. Bounds precede multiplication. Overflow can terminate reference work early. This does not measure CPU instructions, wall time, memory traffic, power, or total program overhead.

The CLI's data is private in-process memory. An expected-receipt mismatch refuses to publish successful output. No input file is overwritten. Partial stdout writes, fatal signals, power loss, network effects, concurrent readers and arbitrary RF2 systems programs are outside this atomicity contract.

## Exact receipt encoding

The native SHA-256 implementation is reused from the compiler, then independently tested. Define `LE64` as an unsigned 64-bit little-endian word. The receipt is SHA-256 of this concatenation, with no terminators:

1. ASCII `RF2-EVIDENCE-CONTRACT-1`.
2. Source identity, exactly 64 lowercase ASCII hexadecimal bytes.
3. SHA-256 of the exact plan file, 32 raw bytes.
4. SHA-256 of the returned active output bytes, 32 raw bytes.
5. Six `LE64` words: code, step, index, expected, actual, work.

The profile and field widths are fixed by this version. The exact plan hash binds original input, operations, permissions and budget, including whitespace. Error output is the unchanged original input.

Source identity uses SHA-256 with domain `RF2-CONTRACT-SOURCE-1` followed by one NUL byte. For every `.rf2` file below the example directory except the generated identity module, sorted by path: `LE64(path byte length)`, UTF-8 relative POSIX path, `LE64(source byte length)`, exact source bytes. The generated module is excluded to avoid circular hashing. The build manifest separately records actual compiler and signed executable digests. The receipt itself is source-bound, not an authenticated statement of the executable currently running. Compiler changes and malicious binaries require checking the external build manifest and trusted build process; this is a remaining H4 boundary, not completed remote attestation.

Preserve the original plan file and returned JSON together as the replay capsule. The JSON alone does not reconstruct whitespace or operations and is not accepted as a plan. Replay with the same built executable and plan in a fresh process:

```sh
output/bin/rf2-contract examples/evidence-contract/demo.plan EXPECTED_64_CHARACTER_RECEIPT
```

Replace that final argument with the receipt returned by the first run. Any change to the exact plan or bound source identity rejects that old digest. A deliberately altered expected receipt also rejects. SHA-256 is integrity relative to a trusted expectation, not a signature, proof of correct execution, authorship or hardware attestation.

## Self-contained native replay

The RF2C1 export/replay route now packages the exact plan, source identity and expected receipt in one bounded file. See [replay, negative controls and measurements](CONTRACT-REPLAY-RESEARCH.md) for the format and executed evidence.

```sh
output/bin/rf2-contract capsule examples/evidence-contract/demo.plan > demo.rf2c
output/bin/rf2-contract replay demo.rf2c
```

Receipts remain unsigned. An isolated test demonstrated that a shared defect in both engines can pass agreement, and a recomputed unsigned receipt can accompany a different accepted plan. These are documented boundaries, not authentication or formal correctness. Named input is opened with Darwin O_NONBLOCK after an idle-FIFO hang was reproduced. This is not a universal I/O timeout.

## Verification and limits

Independent Python controllers are development oracles only. Run:

```sh
python3 tests/standalone/contract_engine_verify.py
python3 tests/standalone/contract_cli_verify.py
```

The engine suite checks all 128 state bytes and complete witnesses against an independently written oracle, in default and optimized native builds. Source corruption is compiled and executed in isolated fixtures: disagreement must preserve original state. The CLI suite checks parsing, boundary conditions, independently reconstructed SHA-256 receipts and fresh-process replay. Initial candidate result: 554 engine checks plus 290 CLI checks passed (844 total). The existing MCP SDK discovery/result/refusal/recovery check passed, as did 33 prepared creations, 65 applications, 75 refusals and 32 releases. These counts describe executed cases, not universal correctness.

Full local case records are under `artifacts/top-ten-five-hypotheses/`; public results are summarized in `EVIDENCE-CONTRACT-VERIFICATION.json`.

WhatIF's heuristic source-review tool does not recognize `.rf2`: it returned zero files, which is no source audit coverage. Native adversarial tests supply the executed evidence here. REA inspected the compiled ARM64 Mach-O and its ad-hoc signature; deep decompiler providers were unavailable. Neither inspection proves program behavior. The existing nine bounded MCP tools remain separate and unchanged; this trusted systems CLI is not silently exposed as an MCP effect.

The next meaningful experiment is an independently reproduced implementation, richer structured operations and an explicit safe MCP schema, followed by matched developer tasks against established tools. Do not describe this profile as language parity, a hardware breakthrough or number-one adoption.
