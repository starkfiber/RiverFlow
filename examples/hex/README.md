# Native byte inspector

`rf2-hex` prints a read-only file as hexadecimal bytes beside an ASCII gutter. It is a useful small binary-inspection tool built in RF2, rather than an invoice-specific language demonstration. It exposes byte representation; it does not disassemble instructions, infer a file format or decode Unicode characters.

```sh
./rf2-hex document.bin
```

From trusted source:

```sh
tools/build-program.sh ./rf2c examples/hex/main.rf2 new-build --opt
./new-build/program document.bin
```

The entry accepts exactly one filename. It does not read stdin automatically and does not create or modify input files. Named paths follow ordinary read-only operating-system open semantics, including symlinks; this is not a filesystem sandbox. A FIFO or special device may block, so no deadline guarantee is claimed.

## Exact format

Every output row is 86 bytes: sixteen uppercase hexadecimal offset digits, two spaces, sixteen three-character byte cells, one space, `|`, sixteen ASCII positions, `|` and LF. Each present byte cell contains two uppercase hexadecimal digits and a space. Missing cells are spaces. The gutter renders bytes 32 through 126 directly and all other present bytes as `.`; missing positions are spaces. The offset counts source bytes and begins at zero. There is no final byte-count-only row.

For example, the three input bytes `41 00 5A` produce one padded row whose gutter is `A.Z`. NUL, tabs, LF and UTF-8 bytes are data, never line delimiters or terminators for this tool. Raw byte order is preserved. The output does not interpret multibyte values or assume an integer endianness.

## Owned input and visible errors

`hex_file` returns the nominal `IO` result. It acquires a noncopyable `File` internally with `own`, reads through `read_owned`, handles each outcome, and lets the compiler close the owner at ordinary function exit. The descriptor is never returned or passed to a raw I/O operation. There is no manual-close/reused-descriptor path in the application. Automatic cleanup failure is returned according to the resource contract, rather than silently replacing a successful outcome with success.

Output uses the borrowed standard-output descriptor. The write loop checks negative errors and handles short writes by shifting the unwritten bytes before retrying. A zero-byte write is an I/O error. There is no automatic close of borrowed stdout. Actual forced short-write injection is not part of the current receipt; the loop's logic and ordinary output/error paths are tested separately. Signals such as SIGPIPE and fatal process traps remain outside ordinary error/cleanup guarantees.

Complete success exits 0. Usage, open, read, output, cleanup or input-limit failure exits 1. Usage prints `Usage: rf2-hex file`; other failures print `RF2 hex input/output failure` on stderr. The CLI deliberately reports a concise message; the reusable `hex_file` typed result retains the numeric error. Output already emitted before failure remains partial and is not rolled back.

The processed-input cap is 1 MiB. Exactly 1 MiB is accepted after a subsequent EOF check. More data returns error 1000 after emitting the first 1 MiB. A bounded read may consume up to sixteen additional bytes to discover that more input remains. This is an input-size policy, not a limit on output bytes or execution time.

## Verification

`tests/standalone/hex_app_verify.py` compiles default and optimized versions. Its independent Python formatter compares complete output for all 256 byte values, NUL, Tamil/emoji UTF-8, random files, exact row boundaries, multiple rows and partial final rows. It checks missing files, directories, usage, spaces/Unicode in filenames, symlinks, unchanged input bytes and the input cap.

In-process probes check descriptor reuse after successful output, read failure and output failure. They establish closure while the process is still alive, rather than relying on process termination. These are finite local software checks, not a speed/token benchmark, formal ownership proof or security certification.
