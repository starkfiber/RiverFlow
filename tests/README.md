# RiverFlow verification

`standalone/` contains native compiler, runtime, ownership, ABI, application and protocol controllers. These build and execute RF2 programs against independent expected results. Root JavaScript tests exercise the historical reference implementation and developer SDK.

## Select the exact compiler

Set RF2_TEST_COMPILER to an existing native candidate for applicable standalone controllers. Set RF2_BOOTSTRAP_COMPILER for compiler_verify.py. Defaults in historical controllers identify the original experiment; they do not select the newest compiler automatically. Read each controller before running it.

| Change | Relevant starting checks |
| --- | --- |
| Incremental target builds | incremental_verify.py with explicit RF2_BUILD_BIN, RF2_TEST_COMPILER and optional RF2_OLD_COMPILER |
| Compiler lowering or shared dispatch | compiler_verify.py, intrinsic_leaf_verify.py, compiler_dispatch_verify.py |
| Raw memory or SHA | memory_intrinsics_verify.py, sha_chain_verify.py, sha_acceleration_verify.py |
| Typed files and storage | ownership/resource/vector/result controllers matching the changed contract |
| MCP transport or trust | protocol/trust controllers and independent SDK verification |
| Optimizer | control_optimizer_verify.py, conditional_reduction_verify.py, register_abi_verify.py |

Both compiler modes matter. A refusing test needs a valid nearby control so an unrelated parser error cannot masquerade as the desired safety check. Retain full output and exact source/binary identities locally; publish only reviewed non-secret receipts.

Fixtures and old comparators preserve their original semantics. Do not update expected output just to make a failing candidate pass. No whole-language proof or independent academic approval follows from a green suite.

For compact images, use compact_image_verify.py with RF2_TEST_COMPILER. To rerun incremental scenarios in compact mode, set RF2_INCREMENTAL_COMPACT=1 and choose compilers that support --compact. The diagnostic function-map tests remain distinct from executable image and MCP acceptance tests.

0.28: `standalone/function_reuse_verify.py` compares opt-in function reuse with clean images and execution; `standalone/compiler_store_verify.py` checks explicit private stores and retained-inode behavior. Both require explicit RF2_TEST_COMPILER and the store suite also RF2_BUILD_BIN. Existing cache, compact-image, compiler and native MCP gates remain required.

0.29: `compiler_hash_verify.py` checks hardware/fallback digests and reference encoding; `function_reuse_extended_verify.py` checks linear readiness/memoized admission; NumberLab CLI/HTTP controllers and `sha40_verify.py` execute real apps with independent result oracles. Native reports belong to new artifact paths, not historical verification files.

## Heap ownership and `.flow` applications, development0.33

`heap_collection_verify.py` checks bounded allocation/data/moves; `heap_ownership_redteam_verify.py` independently challenges native lifetimes, reentrant borrows, private helper refusal and injected syscall failures. `collection_apps_verify.py` checks both real numeric apps against independent integer/JSON oracles. `flow_modules_verify.py` checks mixed .flow/.rf2 imports and refuses unsupported targets. Set RF2_TEST_COMPILER explicitly. See [contract and exact final receipts](../docs/HEAP-COLLECTIONS-0.33.md); no embedded hardware, universal memory-safety or speed result is established.

## ESP32-C3 development0.34

`embedded_verify.py` independently qualifies generated RV32 instructions/images, actual vendor-QEMU ROM boot, arithmetic/call frames and refusals. `esp32c3_uart_verify.py` executes UART TX/RX and timeout cases. The board example's host and RV32 controllers keep scripted sensor-bus responses separate from real sensor acquisition. See [exact contracts, commands and evidence](../docs/ESP32C3-0.34.md). A different CPU/emulator is not physical hardware qualification.
