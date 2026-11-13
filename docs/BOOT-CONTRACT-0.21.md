# RF2 0.21: owned mappings and an authenticated bounded guest boot contract

13 November 2026. Development source with local Apple Silicon evidence. This is a guest-entry contract, not Linux, ELF, UEFI, a physical boot sector or measured secure boot.

## Owned memory

`resource Pages(IO,mapping)` declares a function-local VM child. `own code=Pages(vm,65536,16384,5)` allocates host memory and maps it into that VM. GPA and size are checked for 16 KiB alignment and bounds; permissions are limited to guest R, RW or RX. Copying, scalar/raw-pointer extraction and parent release before children refuse. `mapping_store32` and `mapping_read64` check lifetime, alignment and range and return handled results.

A live vCPU prevents mapping mutation/release. Compiler checks are supplemented by runtime guards, including when a conditional CPU release was skipped. Older low-level VM mapping operations cannot bypass live mapping/CPU children. Ordinary cleanup destroys the vCPU, unmaps guest memory, releases host memory and finally destroys the VM. Map acquisition failure rolls back host allocation and preserves the primary error. Cleanup errors replace success but preserve an existing primary error.

If guest unmap fails, host memory is deliberately retained rather than freed while the guest might still reference it. Raw syscalls/platform interference and fatal traps/signals remain outside checked ownership. This is not a general move/borrow system, arbitrary foreign-call memory safety or proof of physical page reclamation.

## Authenticated image and entry contract

The RF2A021 envelope is little endian. It has a 128-byte header, 4..4096 bytes of admitted ARM64 code and a 32-byte HMAC-SHA256 tag over the complete header and code. The eight-byte magic separates this message format from other receipts. The header includes a 16-byte SHA-256 key identifier, code length and aligned entry, ISA, reserved fields, fixed code/data GPAs (65536/81920), 16 KiB pages, CPSR965, effects-profile7 and a maximum slice of 1..1000 ms. All policy fields are authenticated and independently checked; a valid MAC cannot authorize an unsupported policy.

The host supplies u32 X0/X1 inputs and fixes X2 to the writable data page. Code is guest RX. The admitted instructions are NOP, ADD X0,X0,X1, STR X0,[X2], HVC #1 and immediate B within the image. The validated subset cannot disable the virtual timer or change X2. A requested slice cannot exceed the authenticated maximum. The loader validates a private snapshot and authenticates it before acquiring VM/mapping resources. Links, oversized/truncated inputs and unsafe key files refuse.

The native `rf2-guest keygen new-key` creates a 32-byte owner-only key. `rf2-guest seal raw.rf2g key new-image` validates the unsigned input, constructs the fixed contract and authenticates it. Existing output paths refuse. `rf2-guest image key milliseconds left right cancel` verifies and runs it. All three execute natively in RF2. Developer build/test orchestration is separate. See [run instructions](../examples/auth-vm-runner/README.md).

This is shared-key authentication using the existing RF2 HMAC implementation, not a public signature, publisher identity, hardware attestation, secret-memory guarantee, key rotation service or anti-rollback mechanism. Replay is allowed and tested. The caller must supply the intended trusted key; an attacker who can replace that key controls this trust decision. Authentication does not establish that guest logic is useful or correct.

## What the stronger tests found

The older HVC #0 guest exit exposed an input-specific discrepancy. For inputs3611736829 and3930998975, guest memory held7542735804 but the reported X0 was4294967295 with a different exception syndrome. The frozen0.20 runner reproduced it. A matched HVC #1 control preserved the register and produced the expected exit. The exact internal platform handling of HVC #0 is not established. The current contract requires HVC #1 and rejects HVC #0 even with a valid MAC. Frozen old artifacts and their observations remain local; historical passing samples are not broadened into universal validation.

An initial fault-test oracle also assumed a second guest unmap would fail. The platform accepted it idempotently. That expectation was corrected; actual cleanup-error tests instead deliberately destroy the VM through the raw API. Do not describe the incorrect oracle as a compiler defect.

## Executed evidence

The final authenticated suite passed34guest runs,77image refusals and23mapping/lifetime scenarios in default and optimized modes. Cases include all32tag-byte changes, changed code/header fields, wrong keys, valid MAC with invalid policy, unsigned legacy exit, size/time limits, links/FIFOs, key length/permissions, native signer versus Python HMAC, and allowed replay. Mapping cases cover overlap/partial acquisition, bounds/value errors, conditional-release guards, raw escape, parent/child order and cleanup errors. Another VM and mapping are acquired in the same process after each admitted mapping scenario.

Six additional signed-binary instruction substitutions exercised host allocation/cleanup failures and primary-error preservation. They simulate errno12; they are not actual kernel OOM or physical-memory measurements. Compiler fixed-point/reference/runtime SDK, previous VM, owned-file, WASM and authenticated MCP checks are retained separately with exact artifact identities. WhatIF completed60loopback GET checks of the existing browser application; its source scanner skips RF2 and supplies no RF2 audit verdict. Reverse Lab inspected actual native metadata/signing; its JavaScript coverage adapter does not establish native API coverage.

Reports: [boot](BOOT-CONTRACT-0.21-VERIFICATION.json), [controlled faults](MAPPING-FAULTS-0.21.json), [compiler](COMPILER-0.21-REGRESSION.json), [regressions](REGRESSIONS-0.21.json), [benchmarks](BENCHMARKS-0.21.md). The new results are local, not a relabelled hosted run. Stable0.17 and the exact frozen0.18 archive remain unchanged. No new Core/MCP hardware authority is added.

Next gates are public-key image provenance, an explicitly specified wider guest ABI, concurrent cancellation and qualified interrupt/device models. Any added instruction that can change timer state requires a new cancellation argument before broadening the current guarantee.

Primary construction reference: [RFC2104](https://www.rfc-editor.org/rfc/rfc2104), together with the existing SHA-256 conformance tests. Apple supplies virtualization and VM mapping operations; RF2 supplies the compiler-owned lifecycle, format validation, authentication workflow and host entry policy.
