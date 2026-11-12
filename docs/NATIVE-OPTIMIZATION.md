# Native optimisation, 0.11

RF2 emits its own ARM64 instructions. This release improves the optional --opt path without changing source semantics or expanding MCP permissions. Default compilation retains the previous unoptimised emission path. No LLVM/C backend is introduced.

## General passes

Named locals use registers where admitted. Leaf functions use caller-saved x9 through x15; conservative call detection keeps other functions on callee-saved x19 through x26, saved/restored in their own frame. Record storage slots remain memory-backed. Values beyond the selected register set retain stack slots. This implements part of the AAPCS64 register contract; it is not a general foreign-function interface or other-target ABI qualification.

Direct register and immediate arithmetic avoids unnecessary stack temporaries. In-place increments use a native immediate instruction. Rotated loops retain the entry guard and evaluate the condition at the bottom after each completed iteration, including side-effecting condition calls. Expression coalescing requires exactly one, leftmost read of the assignment target, no calls, fields or strings, and a supported emitted-instruction class. Repeated-target and other alias-sensitive expressions retain their ordinary path.

A final u32 mask can select word instructions for a restricted polynomial/bitwise expression. Division, right shifts, comparisons and other operations whose high bits influence low bits are excluded. Constants, shifts introduced by multiplication, stack operations and zero-extension are handled separately. This is a restricted modular-arithmetic rule, not a general type inference or memory-safety proof.

## Guarded periodic reduction

The admitted serial u64 recurrence is:

```rf2
while index < bound
 set total = total + (index & mask)
 set index = index + 1
end
```

The exact pure two-statement body must match. Index, accumulator and bound must be distinct where relevant; mask+1 must be a power of two with at most 32 bits of period exponent. Literal or runtime-local bounds are accepted. Other comparisons, masks or effects retain ordinary loops. Source names and a particular iteration count are not used to select the rule.

For P=2^k and r=n mod P, define F(n)=floor(n/P)*P*(P-1)/2+r*(r-1)/2. If index<bound, the new accumulator is total+F(bound)-F(index) modulo 2^64, and the new index is bound. Otherwise both are unchanged. The residual product fits in u64 for k<=32; the full-cycle multiplication wraps exactly as repeated accumulator addition. This replaces an eligible linear recurrence with fixed-size arithmetic. It does not reduce arbitrary loops, preserve undefined data races or prove an entire compiler correct.

## Executed evidence

OPTIMIZER-0.11-VERIFICATION: 240 cases checked by direct iteration, 80 large arbitrary-precision expectations and 60 fallback cases; 300 comparisons with 0.10. INSTRUCTION-SELECTION: 2,205 edge cases and old-version comparisons. CONTROL-OPTIMIZER: 180 alias/call/spill/recursive/control cases and 5 side-effecting-condition cases. NARROWING: 340 adversarial integer cases. Module/type, Core, application, compiler-generation, SDK and native ABI regressions are separate receipts. REGISTER-ABI and optimised compiler-bound tests exercise actual native calls and maximum frames. These are host-executed checks, not independent human peer review or a whole-program proof.

## Matched runtime-input measurements

| Runtime-input workload, 20 million steps | RF2 0.10 ms | RF2 0.11 ms | Clang O3 ms |
| --- | --- | --- | --- |
| periodic | 24.878 | 1.842 | 3.841 |
| mix | 57.312 | 22.496 | 22.232 |
| branches | 22.486 | 20.216 | 6.501 |

All variants receive start, bound and seed at runtime. C uses -O3 -mcpu=native. Seven rotated fresh-process trials follow a retained cold/warmup launch; medians include process startup. All outputs are checked. The full report retains 1,000, 2 million and 20 million-step workloads, minima/maxima, sources and raw trials.

The equally specialised periodic C formula measured 2.367 ms at 20 million steps, compared with RF2's 1.842 ms. At the smaller sizes the ordering reverses. Those short times are dominated by process startup, so they do not establish that RF2 evaluates the same formula faster. RF2's eligible loop improves substantially over 0.10 and the loop-based C baseline. Mixed arithmetic is close in point medians; branch-heavy code retains a large gap against Clang. No language-wide victory, AI inference speed, energy result or universal exponential claim follows.

Prior development runs are retained locally rather than selected for the smallest time. Raw final evidence: OPTIMIZER-MEASUREMENTS-0.11.json. tools/measure-optimizer.py rebuilds the sources and strongest stated baselines. No hardware or participant outcome is inferred.

## Research and ABI references

The design uses explicit candidate guards, output checks and retained fallbacks. Register allocation, strength reduction and loop optimisation are established technique classes; this release claims a tested RF2 implementation, not new mathematics. Private research manuscripts are not part of the software release.

Arm, AAPCS64, section 6.1.1: https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst . LLVM vectorisation and diagnostic remarks: https://llvm.org/docs/Vectorizers.html . The remaining branch gap warrants instruction/loop analysis and SIMD work with its own qualification. It is not resolved by calling the language AI-native.
