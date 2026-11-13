# Search bytes with a reusable RF2 library

Find exact text or byte sequences in standard input. The native CLI reports a count and the first matching byte offset. It reads the input without changing or creating files.

```sh
printf 'banana banana' | ./text-search ana
# {"bytes":13,"query_bytes":3,"matches":2,"first_byte":1}
printf 'banana banana' | ./text-search ana --overlap
# {"bytes":13,"query_bytes":3,"matches":4,"first_byte":1}
printf 'தமிழ் தமிழ்' | ./text-search தமிழ்
# {"bytes":31,"query_bytes":15,"matches":2,"first_byte":0}
```

Use `./text-search --help` for the short guide. With no match, `matches` is 0 and `first_byte` is null. An empty query matches every byte boundary, including the end: input with n bytes has n+1 empty matches. Overlap does not change empty-query results.

This is exact byte matching. UTF-8 text works when its encoded bytes match. Offsets are not letters, graphemes or screen positions. There is no case folding, normalization, accent handling, regex or fuzzy search. Arbitrary input bytes, including NUL and invalid UTF-8, are accepted. An operating-system argument cannot contain NUL; the library API supports binary needles.

## Build

From the repository root, explicitly select a qualified Apple Silicon Mac native compiler:

```sh
./tools/build-program.sh /absolute/path/to/rf2c examples/text-search/main.rf2 text-search-build --opt
./text-search-build/program --help
```

The program and library run natively without Python, Node or npm. The tests use Python as an independent oracle; it is not a runtime dependency. This is a trusted systems application, not an additional bounded MCP tool.

## Library contract

`lib/search.rf2` is the reusable module; `main.rf2` supplies the CLI and I/O. The current RF2 module resolver uses paths relative to the entry source directory and forbids parent traversal. To reuse the module in another project, copy it into that project's `lib/` directory and use `"lib/search.rf2"`; there is no automatic global library path or dependency installer.

`byte_search(data,n,needle,m,overlap,prefix,out)` fills a caller-owned `ByteSearch(status,matches,first)` record. It uses explicit byte lengths rather than NUL termination. The caller supplies readable data and needle ranges a separate writable output record and a typed `SearchPrefix` workspace. Create one with `let prefix=SearchPrefix()`. Data and needle may overlap each other; output must not alias those ranges or scratch memory. Raw pointers are trusted; this API cannot validate arbitrary pointer provenance.

Supported budgets are n <= 1,048,576 bytes, m <= 128 bytes, and overlap 0 or 1. A violated budget returns status 1, matches 0 and first=18446744073709551615 before dereferencing either input. A successful call returns status 0. An absent match has matches 0 and the same sentinel; an empty needle has matches=n+1 and first 0. A nonempty match advances by m bytes normally or by one byte with overlap 1.

The implementation uses the established Knuth–Morris–Pratt prefix algorithm. Prefix construction plus scan takes O(n+m) operations under this contract; this is an algorithmic bound, not a measured claim against other language libraries. It does not invent a new search algorithm. It deliberately avoids the quadratic repeated-prefix failure mode of a naive scan. After eight failed starts, a bounded eight-byte zero-detection scan can skip ranges containing no possible first byte. Every word read remains inside the declared range; scalar KMP still decides actual matches. This is an established byte-search technique, not a novel instruction or hardware claim. The plain KMP comparator is retained in `tests/comparators/text_search_kmp.rf2`.

The caller supplies a bounded 1024-byte `SearchPrefix` array, and RF2 checks each array access. The module contains no hidden shared scratch buffer. Distinct operations need distinct workspaces if their lifetimes overlap. The existing language does not provide threads or transferable allocator ownership, so this interface does not establish concurrency support or whole-language memory safety.

## Input, output and failures

The CLI accepts up to 1 MiB of input and a 128-byte query. It reads one extra byte to detect excessive input before writing results. It does not perform a file, network, shell, mutation or background-worker operation. stdin/stdout are borrowed and stay open. Full output writes handle short writes; a closed stdout returns a failure.

| Exit | Meaning |
| --- | --- |
| 0 | Complete result, or `--help` |
| 2 | Invalid argument, flag or query size |
| 3 | Input read failed |
| 4 | Input exceeded 1 MiB |
| 5 | Output write failed |

`--help` is reserved when it is the only argument. `--help --overlap` searches for those literal query bytes. Processing waits for EOF; the application does not impose a wall-clock timeout on an unending input stream. POSIX errors, including interrupted reads, fail visibly rather than silently inventing a result. An I/O error after a partial stdout write can leave partial JSON; the nonzero exit is authoritative.

## Reproduce the evidence

```sh
RF2_TEST_COMPILER=/absolute/path/to/rf2c python3 tests/standalone/text_search_verify.py
```

The developer controller builds both ordinary and optimized native images. It compares results with Python's independently implemented `bytes.find`, including binary needles, repeated-prefix inputs, empty queries, overlapping matches, multibyte text, size refusals and descriptor failures. Separate native harnesses place inputs directly next to inaccessible guard pages on either side. Passing those cases does not prove validity for arbitrary raw pointers or all executions.

The 128-byte query budget leaves headroom under the current compiler's combined 256-local-slot limit when the caller owns a typed prefix array. Larger structured workspaces need further language implementation; this library does not silently widen those bounds.
