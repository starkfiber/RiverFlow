# Collections of owned structured values, candidate 0.46

The completion audit found that the earlier R04 badge was too broad: 0.44 admitted recursive inline ownership but limited collection rows to flat scalar records. The fixed tracker was reopened. This implementation adds consuming collections of rows that own text, number collections, nested records and earlier declared collections. The old source/receipts and 0.45 download remain unchanged.

## Executed qualification

| Check | Result |
| --- | --- |
| New owned-row suite | 480 checks, default and optimized modes |
| Fresh independent row-operation streams | 240 streams, included above; order, identities, bounds and Unicode/numeric payloads matched |
| Unicode catalog application | 150 valid manifest cases, invalid inputs and closed output, included above |
| Earlier nested/flat-row suite | 452 checks; explicit extension mode replaces only the now-obsolete owned-row declaration refusal with positive execution |
| Function-boundary ownership | 432 checks |
| Owned aggregate/text values | 460 checks |
| Borrowed application values | 687 checks |
| Heap adversarial controls | 78 checks |
| Typed Booking persistence | 1,350 checks |
| Booking HTTP | 178 checks, including80 oversized refused bodies |
| Booking agent | 794 checks, including independent legacy SDK exchanges |
| Fresh local archive and actual public download | 93 checks each; exact signed compiler and all four application rebuilds |
| Original runtime MCP SDK | Discovery, valid results, refusal and recovery passed; nine tools unchanged |
| Compiler self-generation | Exact signed executable bytes reproduced |

All tests ran on one Apple Silicon Mac. Faults and address probes use explicitly modified disposable test images, not actual OOM, disk failures or physical hardware. No new performance, AI-token saving, energy, reviewer, learner or universal safety claim follows. [Source-bound receipt](OWNED-ROWS-0.46.json).

## Ownership and relocation

The [API](../experiments/owned-rows/README.md) uses `rows_push(items,move(row))`, owned-result `rows_take(items,index)`, `rows_reserve`, `rows_clear` and `release`. Row types are nominal and declared before their containing collection. This admits owned text and collections directly as rows as well as recursive records. Ordinary scalar `records_*` calls refuse these owners.

Each private collection descriptor carries its inline row width, row limit, compiler-created shape table and cleanup state. Shape entries distinguish scalar words, internal links and child-owner roots. Successful allocation/retirement precedes publication of a new storage pointer. Existing row links are rebuilt against the new mapping. Row transfer rebuilds destination links and disarms source storage; compaction moves complete rows without retaining source-frame pointers.

Insertion consumes the source's static binding regardless of outcome. Before successful reserve/transfer, the source's runtime ownership remains registered for scope cleanup, and failed insertion preserves existing logical rows. This is explicit consuming-call behavior, not a claim that callers can retry the same binding after error. Dead direct owners refuse with error9 before insertion; moving an explicitly released collection also returns error9.

Extraction checks the index before writing caller-owned result storage. It publishes one complete owned result, compacts/rebases remaining rows and decrements length. There are no borrowed indexed row references to become stale after reserve or extraction. An owned result handler is mandatory.

Clear and release visit all live child owners even if one drop fails. Partially completed cleanup quarantines collection mutation/extraction with error16, retaining its cleanup obligations. A later clear/release retries retained children. Successful clear sets length zero while retaining row capacity; successful release also retires row storage and pending speculative mappings. Persistent kernel refusal, fatal traps, signals, raw Systems interference and process exit remain outside guaranteed retirement.

## Actual application

`rf2-labels LABEL...` creates a JSON Unicode-label manifest without reading or modifying files. All labels are validated and stored as owned records before output begins. Each record owns its decoded label and numeric scalar sequence. The catalog is returned and consumed across function boundaries, then rows are extracted for rendering. Limits are64 labels,256 Unicode scalar values/1,024 UTF-8 bytes per label. Scalar counts are not grapheme counts; scalar_sum is arithmetic, not cryptographic identity. A failed output can leave a written prefix, while invalid input produces no JSON.

The same compiler rebuilt the existing shared Booking CLI, browser GUI and bounded agent. Their storage rules and authority are unchanged. The bundle retains the original nine-tool 0.17 runtime. The new collections do not grant trusted Systems execution through MCP.

## Failures and corrections retained

The initial source-preparation match assumed parentheses absent at two dispatch sites and refused before creating a candidate. The patch now targets their exact text and retains hash-pinned baseline checks. Early test programs used unsupported `%`/`break` syntax and a function-local binding outside its scope; those test-source errors were corrected before qualification. Two refusal expectations omitted existing diagnostic punctuation/wording; actual rejection/no-image behavior was retained and the expected diagnostics corrected.

The first catalog placed a record declaration inside a handler, which the compiler correctly refused. Its Stats storage now lives at function scope and resets the empty-label total explicitly. The first historical regression run also correctly showed the intentionally expanded admission: its owned-row declaration now compiles. The baseline test mode still expects the original refusal; only explicit `RF2_OWNED_ROWS_EXTENSION=1` selects the new positive declaration control. The old failed run remains in local evidence.

Additional audit controls reproduced dead-root admission and constructor-move failures in the initial candidate and closed them before final qualification. The private helper namespace now checks original source position, matching the existing injected-runtime guard; direct calls and definitions refuse before image emission. The initial smoke candidate and its receipts remain separate from the final source/image.

The final Booking HTTP regression also exposed a genuine close/reset problem:33 of40 oversized rejected requests reset while unread body bytes remained, without creating a file. The new close path shuts down output, drains at most36,864 bytes with a50ms poll budget, then closes. Tests retain the original failure and require complete400 responses plus subsequent valid requests. Timing arithmetic uses one guarded age sample per iteration to avoid unsigned deadline subtraction underflow. This is bounded local HTTP handling, not a public-service denial-of-service proof.

## Remaining boundaries

The source graph is acyclic; 32 nominal types include compiler helpers. Records retain16 fields, functions eight parameters,256 local slots and16 leaf cleanup registrations. Inline rows are at most255 words and collections65,536 words. Ordinary owned/borrowed signature restrictions remain. No owned file fields, user destructors, cycles, borrowed indexed views, concurrency or panic/signal cleanup are implemented. Stronger heap abstraction, typed persistence for arbitrary new row types and other hardware targets remain broader platform work. Booking's two codecs do not become a generic serializer merely because these new values exist.

The old four-attempt construction comparison remains historical; this change does not establish that RF2 now uses fewer tokens or beats Python. GitHub Linguist acceptance still requires genuine external adoption and upstream review.

## Published download

SFE published [v0.46.0-dev](https://github.com/starkfiber/RiverFlow/releases/tag/v0.46.0-dev) at source2764e7abf4bdb6b6d8578cdb5174d0d7b4ca5e74. The fresh browser download matched671c2a1b36055550ed85cd24bc9ad3284691807f4955581720ace0e67d75ea08 and passed all93 extraction/source-rebuild checks again. The archive is a development edition for Apple Silicon Mac, ad-hoc signed and not notarized. Stable0.17 and earlier0.45 assets are unchanged. This resolves the reopened R04 evidence gap; actual upstream Linguist acceptance remains unfinished.
