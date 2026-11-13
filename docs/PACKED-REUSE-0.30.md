# Optional packed function reuse, development 0.30

RF2 can now read eligible native function templates from one checked container instead of opening one file per helper. This targets daily rebuild cost for programs with many reusable scalar functions. It does not add language semantics, change the stable download, or expand MCP permissions.

## Use

Build the current compiler from an explicitly qualified native compiler, then sign it using normal macOS signing. This experiment is qualified on Apple Silicon Mac only.

```sh
rf2c native/compiler/compiler.rf2 new-rf2c --opt --compact
codesign -s - new-rf2c
mkdir -m 700 function-units
./new-rf2c examples/sha40/main.rf2 new-app --opt --compact --reuse-pack function-units
```

The directory must already exist and be private to the current user. Choose a new output on every invocation. The existing `--reuse-cache DIR` loose-unit format remains supported; combining the two options refuses. Neither mode is enabled by default. Clean compilation remains the preferred route for the small workloads measured here.

## Complete compile measurements

31 rotated trials per route, one Mac, warm filesystem, including compiler startup, executable-file hashing, validation and output creation. Every unsigned output matched the previous 0.29 compiler byte for byte. These are compilation costs, not application execution speeds.

| Workload | 0.29 clean | Candidate clean | Retained loose files | Empty pack | Retained pack |
| --- | ---: | ---: | ---: | ---: | ---: |
| Small example | 1.688 ms | 1.703 ms | 1.913 ms | 1.990 ms | 1.960 ms |
| File checksum | 2.445 ms | 2.435 ms | 2.708 ms | 2.791 ms | 2.647 ms |
| SHA40 | 29.910 ms | 29.882 ms | 5.747 ms | 50.821 ms | 5.735 ms |
| Generated 96-helper numeric fixture | 4.693 ms | 4.638 ms | 4.259 ms | 7.006 ms | 3.356 ms |

The numeric fixture's retained pack took about 21% less time than retained loose files and 28% less than candidate clean compilation. SHA40 was essentially unchanged between cache modes. Small examples still lose to clean builds. An empty pack remains slower because it compiles, captures and publishes templates. These results establish neither universal compiler superiority nor token or energy savings.

[Raw trials and input identities](PACKED-REUSE-0.30-MEASUREMENTS.json) · [Paired exploratory intervals](PACKED-REUSE-0.30-ANALYSIS.json)

## Validation and failure behaviour

A pack namespace binds the actual compiler file digest, declaration context and both image options. Each function retains its current raw-source key, shape check, RF2FN002 integrity digest, local count, branch relocation and return-instruction checks. A matching pack cannot bypass the current function key. The scalar linear eligibility restrictions from [0.29](FUNCTION-REUSE-0.29.md) remain unchanged; calls, loops, effects, ownership and structured results use ordinary compilation.

The container is bounded at 1,114,112 bytes. Its 96-byte header contains RF2FP001, namespace, digest, function count, exact total size and reserved zero. A 48-byte directory entry per function records offset, size and source key. Payloads are contiguous RF2FN002 units. Before any hit, the reader validates the whole container, count, lengths, contiguity and directory-to-unit keys. Structural corruption causes full misses; a malformed individual unit causes that function to recompile. No matching units are blindly marked complete.

The held directory descriptor and nonblocking exclusive lock, no-final-symlink opens, regular-file checks, current UID, 0600 file mode and single-link policy remain enforced. An unchanged healthy pack is not rewritten. New units are written to an exclusive private temporary and atomically renamed after successful image generation. This reconstructible cache is not fsynced. A later cache or report publication error can leave the already valid compiled image; this is not an all-artifact transaction.

Hashes provide corruption detection, not authentication against a malicious writer with the same user identity. Ancestor directories and the local compiler executable path remain trusted. Two bounded pack buffers add about 2.2 MiB of reserved image data space. Compact output omits zero-filled file bytes; this is not a measured resident-memory or energy improvement.

## Executed checks

- [79 packed-cache controls](PACKED-REUSE-0.30-VERIFICATION.json): exact clean bytes, signed execution, entry/helper/declaration changes, partial unit corruption, truncation, rehashed malformed offsets, oversize, symlinks, hardlinks, FIFO, mode and lock failures, failed source preservation and warm no-rewrite.
- [79 existing loose-cache controls](PACKED-REUSE-0.30-LOOSE-VERIFICATION.json): preserved original cache compatibility.
- [Independent maintained encoder and native fixed point](PACKED-REUSE-0.30-COMPILER-VERIFICATION.json): three identical unsigned compiler generations, runtime byte oracle, runtime corpus and official MCP SDK checks. The reference encoder is maintained development tooling, not a user runtime dependency.
- [44 compact-image execution cases](PACKED-REUSE-0.30-COMPACT-VERIFICATION.json).
- [117 Number Lab HTTP checks](PACKED-REUSE-0.30-APP-VERIFICATION.json) executed the retained-pack image, including state, arithmetic, malformed HTTP, origin/revision protection, request deadlines and cleanup. This controller does not validate browser rendering.

The first exploratory timing run overlapped other validation jobs and is not the table above. A first app-controller extension reused the existing loose-test directory name and failed at test setup after HTTP checks; it was corrected to use a distinct pack directory and rerun completely. Neither event is presented as a passing final qualification.

## Next work

Measure larger real projects before selecting any automatic cache policy. Investigate declaration-scoped invalidation and more function shapes with the same clean-build oracle. Keep cache authority local until a separately reviewed authenticated design exists. Qualify other hosts before portability or general speed claims.
