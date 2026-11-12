# Native website and Linux guest laboratory

13 November 2026. RF2 0.18 development candidate. This is a working bounded application experiment, not a new hypervisor or a general language ranking.

## What actually runs

The native RF2 VM controller executes installed QEMU with Apple's HVF accelerator. QEMU supplies the virtual machine and device model. Ubuntu 24.04.5 ARM64 boots from a disposable copy-on-write disk and runs the same Python 3.12.3 website on guest port 8080, forwarded only to host 127.0.0.1:18782. The controller does not implement virtualization instructions, a Linux device model or a replacement for QEMU.

The RF2 website is compiled directly to ARM64 and listens only on 127.0.0.1:18780. Python on the same Mac listens on 18781 as a control. All three serve identical HTML bytes, the same integer recurrence, one worker, backlog 128, close-after-response and TCP_NODELAY. The browser renders shared HTML/CSS/JavaScript. The server is RF2; the entire operating system and browser are not RF2.

## Observed results

| Request | RF2 native, ms | Python host, ms | Python Linux guest, ms |
| --- | --- | --- | --- |
| Shared page | 0.150 | 0.172 | 0.247 |
| 10,000 recurrence steps | 0.177 | 0.758 | 0.787 |

Full response latency includes a new loopback connection and the Python measurement client. Fifteen seeded, shuffled rounds measured twenty requests per cell, two routes and concurrency one/four: 3,600 checked responses. The 63 preflight checks cover shared bytes, known recurrence answers, framing refusals, invalid iterations and disconnect recovery. At concurrency four, guest tail latency was unstable: static p95 73.38 ms versus its median 0.232 ms. Do not describe the guest as uniformly slower or scale these numbers into internet capacity.

The recurrence endpoint's median was 4.29 times lower than the host Python implementation and 4.45 times lower than the guest implementation at concurrency one. The static-page difference against host Python was only about 0.022 ms. Runtime, parser, OS and networking differences are confounders; this is evidence about these implementations on one physical Mac. There is no measured energy, token, optical, transistor, quantum, cross-platform or universal-speed result.

Three WhatIF suites each sent sixty bounded loopback GET requests in baseline, parallel and repeat measurements. All passed and their evidence hashes verified. They establish smoke behavior only, not complete security, capacity or fault recovery.

## Reproduce and inspect

Build with a qualified native compiler:

```sh
python3 tools/build-stack-lab.py output/my-stack-lab
./output/my-stack-lab/rf2-site
```

The Python command is a developer packaging helper; the emitted RF2 server/controller do not launch Python or Node. Another terminal can run the host control:

```sh
python3 examples/stack-lab/python_server.py --port 18781 --deployment host --site examples/stack-lab/index.html
```

For the guest, obtain the official Ubuntu image recorded in artifacts/virtual-lab/image-provenance.json, verify its HTTPS manifest SHA-256, then prepare the seed with tools/prepare-vm-lab.py. Existing disk/seed evidence is never overwritten. The current base image SHA-256 is 3dc8370d923978d4b610fa7964d1b36ba040eefb43198809ca5bc8ac51777b18. GPG signature verification was not performed. No private key, host shared directory or user records enter the VM. The guest uses outbound user-mode networking for normal boot; no claim of an air-gapped guest is made.

```sh
./output/my-stack-lab/rf2-vm /opt/homebrew/bin/qemu-system-aarch64 /opt/homebrew/share/qemu/edk2-aarch64-code.fd /ABSOLUTE/artifacts/virtual-lab/guest-overlay.qcow2 /ABSOLUTE/artifacts/virtual-lab/seed.iso
python3 tools/measure-stack-lab.py
```

The controller fixes a 1 GiB, two-vCPU HVF guest. It does not silently fall back to emulation. Stop the foreground server/controller with Ctrl+C. The experiment is local and disposable; do not expose the bounded HTTP subset as a production web framework.

## Release fault found by another host

The pinned 0.17 compiler crashed inside macOS 15 dyld's legacy relocation analysis before entering RF2. Adding explicit empty LC_DYLD_INFO_ONLY metadata allowed that bootstrap to run. A second repair is necessary for the first compiler image emitted by the old seed; the new compiler then emits the metadata itself. Source encoding, executable code and data are not changed by the repair before re-signing. Signing changes container metadata and file hashes.

The native emitter and retained development encoder now agree on the command. Local compiler tests passed three-stage unsigned-image fixed points, byte comparisons to the development encoder, runtime corpus and independent SDK checks. The second hosted ARM Mac passed HMAC 194, engine 554, trust 520, verifier 262,144 observations and engine 262,144 finite checks. That is a second environment of the same architecture, not an independent compiler or bare-metal hardware qualification. Failed runs remain recorded; the first empty-metadata attempt also failed because the old emitter still produced an old-format compiler container.

Additional local protocol/key testing passed 245 checks. The service pins its key at startup. Key rotation requires restart. Shared-key holders can authenticate claims; the separate semantic verifier still checks the claimed byte result. It is not public-key signing, replay prevention, hardware attestation or protection from a compromised same-user process.

## Evidence and remaining work

- STACK-LAB-0.18-MEASUREMENTS.json retains all timings, checked outputs and controller/source hashes.
- COMPILER-0.18-COMPATIBILITY.json retains native compiler fixed-point and execution evidence.
- SECOND-HOST-0.18.json retains the first successful hosted run; SECOND-HOST-0.18-FINAL.json adds the final owner-triggered run and 245 extra key/protocol checks.
- TRUST-0.18-PROTOCOL-KEYS.json retains extra malformed-input and key-type tests.
- Local artifacts/virtual-lab/whatif-* retain reviewed scenarios, summaries and child hash evidence.

Stable downloads remain 0.17. Prepare a separately labelled 0.18 candidate package, qualify the exact packaged bytes and rerun final hosted tests before promoting a stable release. A true RF2 hypervisor needs foreign calls or a platform adapter, VM lifecycle/resource ownership, interrupt/device handling, guest-memory isolation and separate acceptance tests. This lab supplies a useful baseline for that work; it does not claim those missing mechanisms.

## Candidate package and live showcase

The separate local archive output/rf2-trust-0.18.0-candidate-macos-arm64.tar.gz includes five native programs, a file manifest and public laboratory sources. No keys or VM disks are bundled. Its trust programs passed 520 trust checks, 245 additional key/protocol checks and the independent MCP SDK locally. The packaged website/controller passed the 63 preflight checks after a fresh guest boot. Exact archive bytes have not been qualified remotely; the final hosted run rebuilt the public source. The package is ad-hoc signed, not Developer-ID signed or notarized.

The three loopback services remain running for inspection, with a 1 GiB guest. Use python3 tools/stop-stack-showcase.py to stop only the recorded process identities. It refuses reused PIDs. This is an explicit local demonstration, not a background production deployment.
