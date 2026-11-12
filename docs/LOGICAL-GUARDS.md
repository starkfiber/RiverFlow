# Logical guards, 0.16

The trusted systems compiler now accepts `true`, `false`, `all(left,right)`, `any(left,right)` and `not(value)`. These are native compiler intrinsics, not calls into an AI model or a replacement for checked Core's existing grammar.

* false is 0; true is 1. Any nonzero scalar is truthy.
* all returns 0 without evaluating right if left is 0. Otherwise it evaluates right and normalizes it to 0/1.
* any returns 1 without evaluating right if left is nonzero. Otherwise it evaluates right and normalizes it to 0/1.
* not evaluates once and returns 1 for 0, otherwise0.

The result is an ordinary u64 scalar, not a separate Boolean type. Existing eager bitwise `&` and `|` retain their behavior. Both operands must still be syntactically and statically valid, including code skipped at runtime. A skipped branch cannot hide an unknown name, an owner escape or an unhandled typed result.

```rf2
if all(count>=8,header[7]==10)
 # The second expression runs only after the count guard succeeds.
end
```

These intrinsics lower to branches and scalar normalization. No helper executes for their own logical operation. Pure logical expressions can read live views, while an actual function/I/O call in either operand still meets the existing view-freeze rules, even if the operand would be skipped. Names true, false, all, any and not are now reserved for locals, parameters, functions and nominal type declarations. Existing code using those names must rename them.

## What a small logical basis means

NAND can be written `not(all(a,b))`. A small Boolean basis can express arbitrary finite Boolean circuits. That mathematical fact does not implement every required data structure, lifetime rule, library, operating-system interface or machine backend. RF2 has bounded storage and finite target support; it does not gain unlimited computing resources or universal language compatibility from these operators.

The practical next foundations remain growable typed storage, structured results, ownership transfer, floating point, concurrency and additional targets. [Current capability map](CAPABILITY-MAP.md).

## Real program and evidence

The native file-kind tool uses guarded prefix checks to identify seven header families, after acquiring a read-only owned file. It reads at most 16 bytes, handles short reads, and releases on ordinary success/error paths. It reports a prefix match, never that an entire file is structurally valid, safe or executable. [App contract](../examples/file-kind/README.md).

The first literal candidate refused `set x=x+true` under optimization because the old register/coalescing paths treated the new constant as a local name. Those paths now fall back to ordinary literal lowering, including direct/reduction-loop bounds. The original candidate/source remains in local evidence. Existing arithmetic meaning is unchanged.

The native suite uses independently computed truth-table expectations, random expression trees, side-effect counters, taken/skipped bounds traps, live views, static refusals and exact file-prefix outcomes in default and optimized modes. [Receipt](LOGIC-0.16-VERIFICATION.json). It provides finite executed evidence, not a whole-compiler proof or universal security guarantee. No new speed or token-saving result is claimed.
