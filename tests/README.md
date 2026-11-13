# RiverFlow verification

`standalone/` contains native compiler, runtime, ownership, ABI, application and protocol controllers. These build and execute RF2 programs against independent expected results. Root JavaScript tests exercise the historical reference implementation and developer SDK.

## Select the exact compiler

Set RF2_TEST_COMPILER to an existing native candidate for applicable standalone controllers. Set RF2_BOOTSTRAP_COMPILER for compiler_verify.py. Defaults in historical controllers identify the original experiment; they do not select the newest compiler automatically. Read each controller before running it.

| Change | Relevant starting checks |
| --- | --- |
| Compiler lowering or shared dispatch | compiler_verify.py, intrinsic_leaf_verify.py, compiler_dispatch_verify.py |
| Raw memory or SHA | memory_intrinsics_verify.py, sha_chain_verify.py, sha_acceleration_verify.py |
| Typed files and storage | ownership/resource/vector/result controllers matching the changed contract |
| MCP transport or trust | protocol/trust controllers and independent SDK verification |
| Optimizer | control_optimizer_verify.py, conditional_reduction_verify.py, register_abi_verify.py |

Both compiler modes matter. A refusing test needs a valid nearby control so an unrelated parser error cannot masquerade as the desired safety check. Retain full output and exact source/binary identities locally; publish only reviewed non-secret receipts.

Fixtures and old comparators preserve their original semantics. Do not update expected output just to make a failing candidate pass. No whole-language proof or independent academic approval follows from a green suite.
