// Two-span block-chain encoding oracle. Existing SHA2, no new crypto algorithm.
 .text
 .globl _kernel
_kernel:
 orr x8, x2, x4
 cbz x8, 4f
 mov x6, x3
 mov x7, x4
 mov x3, x5
 mov x4, #1
 ldp q0, q1, [x0]
 cbz x2, 2f
1:
 mov v2.16b, v0.16b
 mov v3.16b, v1.16b
 ldp q4, q5, [x1]
 ldp q6, q7, [x1, #32]
 rev32 v4.16b, v4.16b
 rev32 v5.16b, v5.16b
 rev32 v6.16b, v6.16b
 rev32 v7.16b, v7.16b
 ldr q18, [x3, #0]
 add v16.4s, v4.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v4.4s, v5.4s
 sha256su1 v4.4s, v6.4s, v7.4s
 ldr q18, [x3, #16]
 add v16.4s, v5.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v5.4s, v6.4s
 sha256su1 v5.4s, v7.4s, v4.4s
 ldr q18, [x3, #32]
 add v16.4s, v6.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v6.4s, v7.4s
 sha256su1 v6.4s, v4.4s, v5.4s
 ldr q18, [x3, #48]
 add v16.4s, v7.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v7.4s, v4.4s
 sha256su1 v7.4s, v5.4s, v6.4s
 ldr q18, [x3, #64]
 add v16.4s, v4.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v4.4s, v5.4s
 sha256su1 v4.4s, v6.4s, v7.4s
 ldr q18, [x3, #80]
 add v16.4s, v5.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v5.4s, v6.4s
 sha256su1 v5.4s, v7.4s, v4.4s
 ldr q18, [x3, #96]
 add v16.4s, v6.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v6.4s, v7.4s
 sha256su1 v6.4s, v4.4s, v5.4s
 ldr q18, [x3, #112]
 add v16.4s, v7.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v7.4s, v4.4s
 sha256su1 v7.4s, v5.4s, v6.4s
 ldr q18, [x3, #128]
 add v16.4s, v4.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v4.4s, v5.4s
 sha256su1 v4.4s, v6.4s, v7.4s
 ldr q18, [x3, #144]
 add v16.4s, v5.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v5.4s, v6.4s
 sha256su1 v5.4s, v7.4s, v4.4s
 ldr q18, [x3, #160]
 add v16.4s, v6.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v6.4s, v7.4s
 sha256su1 v6.4s, v4.4s, v5.4s
 ldr q18, [x3, #176]
 add v16.4s, v7.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 sha256su0 v7.4s, v4.4s
 sha256su1 v7.4s, v5.4s, v6.4s
 ldr q18, [x3, #192]
 add v16.4s, v4.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 ldr q18, [x3, #208]
 add v16.4s, v5.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 ldr q18, [x3, #224]
 add v16.4s, v6.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 ldr q18, [x3, #240]
 add v16.4s, v7.4s, v18.4s
 mov v17.16b, v0.16b
 sha256h q0, q1, v16.4s
 sha256h2 q1, q17, v16.4s
 add v0.4s, v0.4s, v2.4s
 add v1.4s, v1.4s, v3.4s
 add x1, x1, #64
 subs x2, x2, #1
 b.ne 1b
2:
 cbz x4, 3f
 mov x1, x6
 mov x2, x7
 mov x4, #0
 cbnz x2, 1b
3:
 stp q0, q1, [x0]
4:
 mov x0, #0
