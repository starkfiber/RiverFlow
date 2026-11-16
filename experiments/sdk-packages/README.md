# Explicit versioned RF2 source SDK, candidate 0.50

The native systems compiler can import one explicitly selected source package
without copying its modules into each application directory. This does not add
a network package manager, runtime dependency, namespace system or Core MCP
authority. Existing local imports retain entry-directory resolution.

```
profile RF2_SYSTEM_A64_V1
use "@rf2/v1/text.flow"
fn main(argc,argv)
 let info=TextInfo(0,0,0,0)
 do text_measure("hello",5,info)
 return info.words-1
end
```

Build with an explicit absolute package directory:

```
rf2c main.flow new-program --sdk-root /absolute/path/rf2-sdk-v1 --opt
codesign -s - new-program
```

`--check main.flow --sdk-root /absolute/path/rf2-sdk-v1` performs the same
package admission but creates no executable. `--sdk-root` cannot be repeated.
No environment search path, local fallback, download, dependency installation or
code execution occurs while resolving imports. Apps built by the compiler have
no runtime dependency on the source SDK or Python/Node.

## Package format and trust

The selected directory contains `rf2-sdk.manifest`. Its exact first line is
`rf2-sdk-v1`, followed by one or more LF-terminated lines of 64 lowercase SHA-256
digits, one ASCII space and one module path. The compiler validates the whole
manifest before loading source, rejects duplicate entries and verifies the
bytes of every imported SDK source against its listed digest. The root and
manifest are owner-selected trusted inputs; SHA-256 identity is not publisher
authentication. Altering both a module and its manifest is possible for anyone
who controls the selected package. No signature, registry trust or hostile
same-user isolation is claimed.

Only `@rf2/v1/` is supported. A manifest module path uses the same identifier,
digit, hyphen and slash segments as local imports and ends in `.flow` or `.rf2`.
Dots, `..`, absolute paths, backslashes and empty segments reject. SDK sources
use explicit versioned imports for other SDK modules. A plain `use "x.flow"`
inside any module still means the entry application's directory. Do not mix
local copies of the same global declarations with their SDK imports; duplicate
symbols intentionally reject. Namespace-qualified paths do not namespace
functions or types.

The package root must be absolute and shorter than 768 bytes. Package manifest
and module files use nonblocking, no-follow final-component opens and native
regular-file checks, refusing directories/devices/FIFOs; parent directory components
and the root are trusted. This is not filesystem containment. The manifest is
at most 32 KiB with at most 32 distinct module entries. Existing 32-source-file,
16-active-import-depth and 512-KiB combined/expanded-source budgets remain.
Only imported source content is hash-verified, not unused package files.

Imported diagnostics identify the actual selected SDK root and module path.
The complete expanded source continues to bind cache dependency identity; a
package edit cannot silently reuse old compiled application bytes.

## Supplied package and API

`python3 experiments/sdk-packages/package.py NEW-SDK-DIRECTORY` is the optional
development packager. It produces the manifest, provenance and six reviewed
modules from the Document Audit SDK snapshot. Exact import lines become
versioned SDK imports. The text module also gains a separately named overlapping
search helper. Package edition `0.50B-transport` adds the explicit checked output
helper and recoverable MCP transport policy below. Provenance records each
transformation and its additional source hashes. The original warm study SDK A
is retained byte-for-byte in its recorded experiment artifacts; its grades and
usage are not relabelled as package B results. No complete
application, document corpus assembly or HTML renderer is supplied.
The native compiler consumes this source package directly.

| Module | Reusable interface |
| --- | --- |
| `io.flow` | `IO`, `Writer`, bounded final-component-no-follow `io_regular`, unchanged `io_write_all`, explicit `io_write_no_sigpipe` |
| `text.flow` | Strict UTF-8/C0 validation, ASCII-break words, byte searches, line cursors, percent decoding, HTML/JSON escaping |
| `json.flow` | Bounded JSON parser and decoded field helpers |
| `mcp.flow` | Existing bounded read-only launch-selected legacy MCP helper; caller supplies `mcp_execute(out:Writer):IO` |
| `collections.flow` | Bounded owned integer storage, sorted insertion and four-word rows |
| `sha256.rf2` | Existing source SHA-256 implementation |

The `text_search` helper counts **nonoverlapping** exact byte matches and uses a
u64-max absent-offset sentinel internally. An application requiring overlapping
matches or JSON `null` must implement that distinct conversion explicitly.
Case folding is optional ASCII only. No grapheme, normalization or semantic
search claim follows from this package. The generic MCP helper preserves its
65,536-byte payload cap and does not grant file/network mutation.

`text_search_overlapping` has the same parameters and caller-owned prefix/output
types but accepts only 1..128-byte queries, at most 1 MiB of input and fold 0/1.
After a match, its KMP state returns to the longest matching prefix instead of
zero, so `aaa` searched for `aa` yields two matches. Invalid arguments return
zero **before changing output or prefix workspace**. Inputs are read only;
successful results use the same internal absent-offset sentinel as the original
helper. UTF-8 validation and JSON `null` conversion remain caller tasks.

## Checked output and MCP transport, package B

Application construction exposed a real SDK limitation. The earlier generic
MCP helper called `exit(1)` after a transport read/write failure, bypassing the
normal `IO` return and caller cleanup. On a closed reader pipe, Darwin's default
SIGPIPE policy could also terminate an application before its writer could
return EPIPE. Original SDK A, its passing frozen grades and the later
supplementary output failures remain separately recorded.

Package B changes only transport failure handling, preserving the existing
JSON-RPC parser, methods, tool schema, callback contract and payload budget.
`mcp_serve` now returns `err(errno)` on read/write failure. It stops reading after
an output failure, suppresses further output attempts after the first failure,
and lets the caller map that ordinary error to its own diagnostic/exit status.
A callback failure remains an `isError:true` tool response; it does not end an
otherwise healthy connection. This does not add file/network authority.
The helper supports one active process-local session. A transport failure ends
that serving call; session reentry or resuming a failed connection is not qualified.

The Darwin implementation saves stdout's descriptor-local `F_GETNOSIGPIPE`
value, sets `F_SETNOSIGPIPE` while serving, and attempts to restore the old value
before every ordinary return after activation. It does not install or change a
process-global signal handler. A primary transport error takes precedence over
a simultaneous restore failure. A restore-only failure is
`err(65536 + errno)`. Fatal traps, process exit, signals and concurrent descriptor
closure/reuse/flag changes remain outside this ordinary-return contract. The
borrowed descriptor must be used exclusively for the duration of this call.

For CLI output, applications can explicitly use
`io_write_no_sigpipe(fd,p,n):IO`. It applies the same save/set/write/restore
policy around the unchanged `io_write_all` loop. It returns the complete byte
count on success; a zero-byte request returns `ok(0)` without touching even a
closed descriptor. Existing `io_write_all` behavior is unchanged. Errors do not
promise zero bytes were delivered: a peer can close after receiving a prefix,
and a restore-only failure may follow a completed write. Do not blindly retry a
whole output after either error. No atomic stream rollback or cancellation
cleanup is claimed.

The supplied native transport controls exercise regular files, pipes, both
initial flag states, actual EPIPE/EBADF/EAGAIN, partial delivery followed by peer
closure, ordinary caller cleanup and callback recovery. Restore-failure
precedence uses explicitly labelled source hooks, not a fabricated kernel
failure. Constants are checked against the local Apple SDK headers. This is a
Mac/Darwin policy; no owned TTY, Linux/Windows target or cross-platform signal
qualification follows from these tests.

`prepare.py` exposes `apply(source)` so the diagnostics candidate can compose
its source changes before native compilation. This is an isolated source
candidate; existing downloads are unchanged. Qualification receipts and any
remaining limits are recorded by the parent sprint before publication.
