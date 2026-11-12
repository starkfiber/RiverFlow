# Guarded conditional periodic reduction

This post-0.11 compiler candidate extends the optional native optimizer. It is committed development work, not an installed 0.12 release. The published 0.11 downloads remain unchanged.

## Exact admitted source

```rf2
while index < bound
 if (index & A) == 0
  set total = total + K
 else
  set total = total + (index & B)
 end
 set index = index + 1
end
```

A and B are integer literals of the form 2^a-1 and 2^b-1, with 0<=a<=b<=32. K is a u64 literal. The serial loop body, parenthesized masks, increment and comparison must match exactly, with scalar distinct index/accumulator/bound where required. Bounds can be literals or local values. Calls, extra statements, other comparisons and unsupported masks retain ordinary compilation. Renaming locals does not change selection; no benchmark name or fixed iteration count is inspected.

The initial condition is checked. False entry leaves both accumulator and index unchanged. Otherwise the final index equals bound, and the accumulator wraps modulo 2^64 exactly as repeated source addition does. This transformation is not valid for arbitrary effects, changing bounds, concurrent observation or undefined data races.

## Derivation

Let P=B+1 and Q=A+1. Define the sum of the first n masked indices:

```text
r = n mod P
F_P(n) = floor(n/P) * P*(P-1)/2 + r*(r-1)/2
m = ceil(n/Q)
G(n) = F_P(n) + m*K - Q*F_(P/Q)(m)
```

The original masked values repeat every P indices. The selected indices are exactly the multiples of Q. There are m of them below n, and their original masked sum is Q times the masked sum of their quotient indices. G replaces those contributions with K. The loop therefore adds G(bound)-G(start). The machine implementation computes the ceiling through a shift and a nonzero remainder, avoiding overflow from n+Q-1. Individual products used before division fit at the admitted 32-bit period bound; accumulator and full-cycle products use defined wrapping arithmetic.

This is a derivation and tested implementation of established finite-sum reasoning, not a new mathematical theorem or machine-checked whole-compiler proof.

## Executed checks

The dedicated test executes 384 direct-iteration cases, 128 large arbitrary-precision cases, 72 fallback cases and 18 literal-bound cases. It compares all 384 small cases with the frozen 0.11 compiler. Those calls also check twelve preserved caller locals, including spilled locals. Constants include zero, seven, 2^63 and u64 maximum. Periods range from one through 2^32; false/empty entry, overflow and near-u64-maximum final indices are covered. The large cases use an independently written arbitrary-precision expression; they are not brute-force execution of 2^64 iterations.

An initial CSET encoding emitted an invalid instruction and failed execution. The instruction was checked against assembler output, corrected, and the entire dedicated suite rerun. That failed candidate is not the verified binary. The final candidate is pinned by the SHA256 in [the verification receipt](CONDITIONAL-REDUCTION-VERIFICATION.json).

## Comparison and limits

[Raw measurements](CONDITIONAL-REDUCTION-MEASUREMENTS.json) retain three sizes, seven rotated fresh-process trials, cold/warmup observations, minima/maxima, exact sources and checksums. All variants receive the same runtime start, bound and seed. Clang is compiled with O3 and the native CPU setting; scalar-only Clang and an equally specialized C formula are included. Compiler execution costs are recorded separately from program execution.

For 20 million steps on the tested Mac, median total process times were 21.385 ms for RF2 0.11, 1.925 ms for this candidate, 6.196 ms for Clang's vectorized loop, 6.591 ms for scalar Clang and 1.744 ms for the C formula. This is about an elevenfold improvement against the previous RF2 implementation for this admitted family. Formula timings approach the process-startup floor, so their ordering is not a reliable internal-compute speed comparison. No general Clang dominance, SIMD implementation, new token saving, energy measurement or hardware result follows.

Developer reproduction uses the frozen 0.11 compiler and explicit candidate binary: tests/standalone/conditional_reduction_verify.py and tools/measure-conditional-reduction.py. RF2_TEST_COMPILER selects the candidate. Existing 0.11 receipts remain immutable. The candidate's release qualification and remaining feature gaps are separate from this experiment.

## Reproduce from a source checkout

Use the downloaded 0.11 native compiler as the frozen bootstrap and comparison. No fresh timing should overwrite the published report without a separately retained experiment.

```sh
mkdir -p output
./rf2c native/compiler/compiler.rf2 output/rf2c-conditional
codesign -s - output/rf2c-conditional
RF2_TEST_COMPILER="$PWD/output/rf2c-conditional" \
RF2_BASELINE_COMPILER="$PWD/rf2c" \
python3 tests/standalone/conditional_reduction_verify.py
RF2_TEST_COMPILER="$PWD/output/rf2c-conditional" \
RF2_BASELINE_COMPILER="$PWD/rf2c" \
RF2_BENCH_RUN=conditional-reproduction \
python3 tools/measure-conditional-reduction.py
```

These are developer verification commands. The benchmark also requires the installed Apple Clang toolchain as a comparison. The self-contained RF2 benchmark fixture is examples/systems/conditional-sum.rf2; its command-line arguments are controlled test inputs, not a validated public input interface.
