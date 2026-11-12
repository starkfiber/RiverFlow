# RF2 systems platform ABI, 0.9

`syscall6(number, a, b, c, d, e, f)` is available only in trusted RF2_SYSTEM_A64_V1 source. The compiler moves the call number to x16 and six arguments to x0 through x5, emits Darwin svc #0x80, and normalizes BSD carry-set errors to negative errno in a u64. Mach calls and multiple-return-register contracts need separately specified wrappers. Raw values are not portable handles or automatic permission checks.

`fork_process()` wraps Darwin fork. A child is identified by the kernel's x1 flag, then receives zero; the parent receives the PID. Treating only x0 as a normal POSIX return was wrong and produced a duplicate controller in an early app test. The corrected primitive is executed by a test that makes the child exit 7 and verifies the parent's wait status. The editor reaps its browser-opener child at shutdown.

The native compiler and independent seed encoder produce equal unsigned images for the platform fixtures. Tests execute PID/UID queries, negative errno, six-argument mmap/store/load/munmap and fork/wait. They also refuse wrong syscall arity. These are host ABI receipts, not independent compiler verification, process isolation or direct transistor control. The platform ABI does not expand Core/MCP effects.

The editor uses RF2 wrappers for sockets, poll, process launch and timeouts. OS frameworks, the kernel, CPU and browser still provide their specified services. RF2 emits machine code; this does not establish a new processor design, x86 backend or universal systems library.
