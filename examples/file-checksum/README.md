# Native file checksum

Source: examples/file-checksum.rf2. This is a read-only trusted CLI example using the RF2 SHA library. It accepts one regular file up to 1 MiB and optionally a 64-digit hexadecimal expected digest. It does not authenticate origin, snapshot a concurrently changing file, sign a manifest or expose filesystem access over MCP.

Build with an explicitly qualified candidate compiler through tools/build-program.sh. A fresh output directory is required. The local tested executable is output/file-checksum-0.24 and has no Node, npm, Python or C++ runtime dependency.

Usage: `file-checksum-0.24 path [expected_hex_digest]`

stdout contains the actual lowercase digest and newline. Exit 0: success or match. Exit 1: mismatch. Exit 2: input, I/O or usage failure. Final-component symlinks, directories, FIFOs and oversized files refuse. The input is never written. The Darwin descriptor layout and system calls are target-specific.
