# 29. Small foundations, useful decisions

Boolean logic has a small foundation. NAND alone can express arbitrary finite Boolean circuits. In RF2 it can be written not(all(a,b)). But expressing logic is different from shipping every library, data structure and target interface that an application needs. Storage, ownership and failure rules still matter.

Release 0.16 adds true, false, all, any and not to the trusted systems compiler. False is zero; true is one; any nonzero scalar is truthy. Logical results are normalized ordinary u64 values. A separate Boolean type is not introduced.

## Evaluate only what is needed

```rf2
if all(count>=8,header[7]==10)
 return 1
end
```

The second expression runs only if the first is true. The any intrinsic skips its right side if the first is already true. The not intrinsic evaluates once and reverses truthiness. Existing bitwise operators stay eager; changing them would change programs that deliberately evaluate both sides.

Skipped code is still checked. A constant false cannot hide an unknown name, an invalid owner use or an unhandled result. Pure logical expressions can read live views, but actual calls in either operand still obey view lifetime restrictions. The five new names are reserved, so old programs using them as identifiers must rename them.

The compiler emits branches directly. This makes behavior inspectable but does not establish a speed or token advantage. The first candidate exposed an optimizer admission problem: a new true constant was mistaken for a local variable. Literal-aware fallback paths corrected it, including optimized loop conditions.

## Inspect a real file

The file-kind application opens a named input through an owned-file declaration, reads up to sixteen bytes and matches guarded signatures. It handles short reads and reports PNG, PDF, ELF, GIF, JPEG, ZIP, Mach-O64 or unknown. It changes no input bytes.

A recognized header does not prove that the rest of a file is valid or safe. The tool does not execute content or disassemble instructions. Its purpose is to make a bounded byte-level decision with clear errors and cleanup.

Tests compare normalized truth tables and generated expression trees with separately computed expectations. Side-effect counters confirm that skipped right sides do not execute. Taken and skipped invalid indexes test the actual branch behavior, while malformed operands must still refuse. File tests cover complete signatures, truncations, arbitrary bytes and I/O errors in both compiler modes.

The next foundations remain growable storage and structured outcomes, followed by broader ownership and target support. A small mathematical basis gives a way to express computations; real applications require the rest of the engineering to be implemented and tested.
