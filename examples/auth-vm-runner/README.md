# Native authenticated guest runner

Source is [guest.rf2](../evidence-contract/guest.rf2), colocated with the reused SHA-256/HMAC modules so compiler imports remain local. No duplicated crypto implementation or uploaded key is needed.

Developer build:

```sh
python3 tools/build-auth-vm.py new-build-directory
```

Native user commands (substitute the built executable path):

```sh
rf2-guest keygen new-guest.key
rf2-guest seal examples/vm-runner/add.rf2g new-guest.key new-add.rf2a
rf2-guest new-add.rf2a new-guest.key 10 19 23 0
```

Run stdout is an80-byte little-endian machine receipt: reason, X0, first data word, run ticks, budget ticks, ticks/second, status, reserved, loaded bytes, entry. It is not terminal prose. Exit0 means the checked host workflow completed; it does not certify guest usefulness. Cancel1 requests cancellation before entry. A looping admitted image exits through the virtual timer. Developer tests decode the receipt.

The fixed authenticated maximum is100ms for native seal. A smaller caller slice is admitted; a larger one refuses. The verifier admits a header maximum up to1000ms from a trusted key holder, but still rejects any unsupported ABI or instruction. The current exit instruction is HVC #1; HVC #0 from older fixtures refuses.

Keys must be regular files, exactly32bytes, mode0600 and owned by the current real user (getuid); links/FIFOs refuse. Store keys outside the repository and never commit them. Authentication uses a shared key, not a public signature or anti-rollback service. Native seal refuses existing outputs; a failed partial new output remains for explicit inspection. No Node, npm, Python, C++ or QEMU runtime is needed by the executable. Apple Silicon macOS and the explicit hypervisor entitlement are required. See [the complete contract and limits](../../docs/BOOT-CONTRACT-0.21.md).

Test with `RF2_AUTH_VM_DIR=/absolute/build python3 tests/standalone/auth_vm_verify.py`. The injected-failure controller is `tests/standalone/mapping_fault_injection.py`; its substitutions do not constitute actual kernel failures.
