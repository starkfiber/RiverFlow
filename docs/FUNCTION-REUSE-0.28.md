# Safe scalar-function reuse: RF2 0.28 candidate

The native compiler can now reuse a restricted function's pre-relocation machine-code template. This is an explicit trusted-local compiler option. It is separate from whole-target caching, the diagnostic `.functions` sidecar and bounded MCP execution.

This candidate establishes a tested correctness mechanism. The measured opt-in route is currently slower than clean compilation on the tested workloads. Use the ordinary compiler by default. The complete measurements include validation and file I/O; skipping those costs would misrepresent the development experience.

## Usage

Select a qualified current native compiler, create a private directory and use new output names:

```sh
mkdir -m 700 .rf2-functions
/path/to/rf2c examples/function-changes/main.rf2 output/first --opt --compact --reuse-cache .rf2-functions
/path/to/rf2c examples/function-changes/main.rf2 output/second --opt --compact --reuse-cache .rf2-functions
cat output/second.reuse.json
```

The successful explicit reuse route emits a `.reuse.json` report containing `reused`, `compiled`, `ineligible` and `compilerSHA256`. Compiled counts admitted helpers generated on a miss; ineligible functions use normal generation. Signing and execution remain explicit separate operations. No Node, Python or C++ runtime is needed by the compiler or produced application. The comparison controllers are developer tools.

## Admitted subset

A helper must have only scalar parameters, no extra locals, no structured return or cleanup, and exactly one return expression. Atoms are integer literals and that helper's scalar parameters. Ordinary arithmetic, bitwise operations, shifts, comparisons, unary minus/complement and parentheses follow the existing compiler's precedence, comparison-chain and depth rules. `main`, function/intrinsic calls, strings, buffers, memory operations, records, arrays, branches, loops and ownership constructs are excluded. Excluded bodies compile normally.

The full source is scanned every time. A separate whitelist parser validates the current helper body on every proposed hit. This deliberately does not treat an unchanged diagnostic fingerprint as permission to skip arbitrary semantic checking. `--functions` requests normal generation throughout so its diagnostic maps match clean maps; the reuse report explicitly records zero hits in that mode.

## Identity, relocation and state

Each key binds the kernel-reported executable-path file SHA-256, compiler mode, image mode, complete nonbody declaration/signature context and canonical function tokens. Body changes cannot reuse the old helper. Unchanged helpers may be reused after another body changes. Declaration, type, import-expanded signature, function-order or option changes can conservatively invalidate all units. A different compiler file identity gets a separate key space.

The compiler queries its own Darwin process path rather than trusting caller-selected `argv[0]`. It opens the kernel-reported path without following a final symlink and hashes the bounded regular file. This is executable-path file identity, not an attestation of already-loaded pages against same-UID file replacement after execution. The private local caller and ancestor paths remain trusted. Apple's [libproc implementation](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.c) provides the primary background for the process-path query. Failure to establish this identity refuses explicit cache use.

Units store pre-resolution instruction bytes, a relative exit-label position and one exit-branch relocation. A hit allocates the current exit label, copies the template, restores the current body cursor and scalar expression state, and adds a fixup against that current label. All other current-program relocations still resolve normally. Capture requires exactly one new label, one matching exit fixup and zero registered objects. Unsupported effects cannot silently become reusable templates.

The binary unit header is `RF2FN001`, followed by key, integrity digest, byte count, exit offset and branch offset. The integrity digest covers those three metadata fields together with the code bytes. Length, alignment, range, expected branch opcode and final return checks precede copying. Code length is bounded to 64 KiB and complete program code to 1 MiB. These are implementation bounds, not arbitrary-language reuse.

## Cache and failure behavior

The directory must already exist, belong to the caller and exclude group/other POSIX permissions. Final directory symlinks refuse and a nonblocking exclusive lock prevents cooperative writers from racing. Entries must be private, caller-owned regular files with one hard link. Missing, malformed, mismatched or corrupted units fall back to normal compilation; cache-root or identity failures refuse.

Units are captured privately before resolution and published only after complete source generation and the output image succeed. Writes use exclusive temporary files and an atomic rename under the directory lock. Existing application outputs are never replaced. Temporary unit files are reconstructible; no power-loss transaction or authenticated shared cache is claimed. A later report or unit-publication error may leave a valid newly emitted application image. Image, unit and sidecar publication is not a single atomic transaction.

SHA integrity does not protect against a malicious same-UID cache owner who can rewrite both bytes and digest. ACLs, ancestor directories, arbitrary concurrent source mutation and untrusted multi-user execution are not proved safe by these controls. Do not publish or share a cache as a trusted distribution mechanism.

## Executed qualification

The independent controller requires both byte-for-byte clean-image equality and signed execution equality. It checks actual positive hit counts, body/declaration/type/order/dependency changes, preserved-mtime edits, numeric semantics, compiler identity, corrupted code and bounded metadata, partial files, unsafe directory permissions, symlinks, lock recovery and no unit publication for invalid source. Spoofed `argv[0]` and diagnostic-map coexistence have explicit controls. All 81 cases passed for the final candidate; source identities and exact outcomes are in the linked receipt.

The cached native runtime and real modular SHA file app match clean builds. The runtime retains nine bounded MCP tools and passes native corpus plus official SDK discovery, result, refusal and recovery controls. One scalar helper in each of those two applications is reusable in the current subset; most functions remain on normal generation. These are scoped observations, not broad application coverage.

[Function controls](FUNCTION-REUSE-VERIFICATION.json) · [Integration](NATIVE-0.28-INTEGRATION.json) · [Complete measurements](FUNCTION-REUSE-MEASUREMENTS.json) · [Compiler stores](COMPILER-STORE-0.28.md).

## Complete compile measurements

Twenty-one rotated trials per route on one Apple Silicon Mac, warm filesystem. All times include process startup, new output creation, and the selected route's validation and I/O. The retained unit cache is initialized separately. Lower is better.

| Task | Direct clean | Empty function cache | Retained function cache |
| --- | ---: | ---: | ---: |
| small-example | 2.217 | 11.535 | 11.322 |
| file-checksum | 3.211 | 12.325 | 12.252 |
| numeric-helper-fixture | 6.564 | 45.901 | 36.372 |

Times are median milliseconds. The numeric-helper case is a generated compiler workload, not field data. Every output matched its direct clean oracle. Positive hit counts confirm actual code reuse, but the complete route is slower on all three cases. Executable-file hashing, canonical-token/context processing and per-unit I/O are included; a causal breakdown of their individual costs has not been measured. Keep this route opt-in for correctness research rather than claiming a development-speed improvement.

## Next work

Reduce identity/fingerprint and cache I/O overhead without removing verification, then measure again. Broader reuse requires stable symbolic call/object identities, semantic and object-effect replay, ABI invalidation and independently tested relocation linking. Linux/Windows backends and GUI toolkit equivalence need their own implementations and executed acceptance gates. This Mac-only candidate does not establish universal Python/C/assembly compatibility, runtime superiority, energy savings, AI intelligence or billed-token reductions.
