// Development encoding oracle; not a runtime assembler dependency.
 .text
 .globl _kernel
_kernel:
 cbz x2, 3f
 cmp x2, #4
 b.lo 2f
1:
 ldr q0, [x1], #16
 rev32 v0.16b, v0.16b
 str q0, [x0], #16
 sub x2, x2, #4
 cmp x2, #4
 b.hs 1b
2:
 cbz x2, 3f
4:
 ldr w3, [x1], #4
 rev w3, w3
 str w3, [x0], #4
 subs x2, x2, #1
 b.ne 4b
3:
 mov x0, #0
