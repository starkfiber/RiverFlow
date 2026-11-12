# Read-only file header inspector

`rf2-file-kind file` reads at most 16 bytes and reports one prefix family: png, pdf, elf, gif, jpeg, zip, macho64 or unknown. It uses owned-file acquisition, handled byte I/O and the native all/any guards. The input is unchanged.

This is signature recognition, not a file parser, antivirus, disassembler, architecture validator or proof of safe content. PNG uses its 8-byte signature; PDF uses %PDF-; ELF uses its 4-byte prefix; GIF uses GIF87a/GIF89a; JPEG uses FFD8FF; ZIP uses PK0304,PK0506 or PK0708; Mach-O64 uses either byte order of its 4-byte magic. Later content is not inspected. Unknown is a successful classification, including empty input.

The implementation reads one byte per I/O operation until 16 bytes or EOF, so short reads do not silently truncate a requested header. This is a bounded implementation with no speed claim. A special file/FIFO can block; no timeout or filesystem containment is promised. Symlinks follow normal read-only OS open semantics.

Exactly one filename is required. Complete classification prints a lowercase name and newline, exit 0. Usage, read/open/cleanup/output errors exit 1. Output writes retry positive short writes; signals such as SIGPIPE and fatal process traps remain outside ordinary cleanup. No successful partial-output write was forced in the tests. Automatic cleanup errors follow the owned-file result protocol.

Build with tools/build-program.sh and the trusted native compiler. Native tests in tests/standalone/logic_verify.py compare complete output against independently declared signatures, truncations, random data and error cases in both modes. Samples are programming fixtures, not field results or security certification.
