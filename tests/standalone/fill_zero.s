// Development encoding oracle; not a runtime assembler dependency.
 .text
 .globl _kernel
_kernel:
 cbz x1, 3f
 movi v0.16b, #0
 cmp x1, #16
 b.lo 2f
1:
 str q0, [x0], #16
 sub x1, x1, #16
 cmp x1, #16
 b.hs 1b
2:
 cbz x1, 3f
4:
 strb wzr, [x0], #1
 subs x1, x1, #1
 b.ne 4b
3:
 mov x0, #0
