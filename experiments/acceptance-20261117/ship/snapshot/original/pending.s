# Four64-byte neighbor slots; one2048-byte owned packet per slot. SingleCPU.
Lpending_init:
 movabsq $0x8000000000056003,%rax
 movq %rax,0x42b0
 addq $4096,%rax
 movq %rax,0x42b8
 addq $4096,%rax
 movq %rax,0x42c0
 addq $4096,%rax
 movq %rax,0x42c8
 invlpg 0x56000
 invlpg 0x57000
 invlpg 0x58000
 invlpg 0x59000
 movl $0x56000,%edi
 movl $2048,%ecx
 xorl %eax,%eax
 rep stosq
 retq
Lpending_revoke:
 pushq %r8
 pushq %r9
 movl $0x56000,%r8d
 movl $4,%r9d
Lpending_count_cancel:
 cmpq $0,(%r8)
 je Lpending_count_next
 incq 0x540d0
 movq $45,0x550a8
Lpending_count_next:
 addq $2048,%r8
 decl %r9d
 jnz Lpending_count_cancel
 movl $0x55100,%edi
 movl $32,%ecx
 xorl %eax,%eax
 rep stosq
 movq $0,0x550a0
 movl $0x56000,%edi
 movl $2048,%ecx
 rep stosq
 popq %r9
 popq %r8
 retq
# r8=entry,r9=index. Erase matching pending owner before slot reuse.
Lneighbor_erase:
 pushq %rdi
 pushq %rcx
 movq %r8,%rdi
 movl $8,%ecx
 xorl %eax,%eax
 rep stosq
 movq %r9,%rdi
 shlq $11,%rdi
 addq $0x56000,%rdi
 cmpq $0,(%rdi)
 je Lneighbor_erase_empty
 incq 0x540d0
Lneighbor_erase_empty:
 movl $256,%ecx
 rep stosq
 popq %rcx
 popq %rdi
 retq
# eax=0 valid,39 stale; requires current timestamp53f18.
Lneighbor_valid:
 cmpq $0,(%r8)
 je Lroute_absent
 movq 0x55000,%rax
 cmpq 40(%r8),%rax
 jne Lroute_absent
 movq 0x50ac8,%rax
 cmpq 32(%r8),%rax
 jne Lroute_absent
 movq 0x53f18,%rax
 subq 24(%r8),%rax
 jc Lroute_absent
 cmpq 0x5a68,%rax
 jae Lroute_absent
 xorl %eax,%eax
 retq
Lneighbor_get:
 movl 0x55080,%r11d
 movl $0x55100,%r8d
 xorl %r9d,%r9d
 movq $-1,%r10
Lneighbor_scan:
 callq Lneighbor_valid
 testl %eax,%eax
 jz Lneighbor_live
 callq Lneighbor_erase
 cmpq $-1,%r10
 jne Lneighbor_advance
 movq %r8,%r10
 jmp Lneighbor_advance
Lneighbor_live:
 cmpl 8(%r8),%r11d
 jne Lneighbor_advance
 movq %r8,0x55098
 cmpq $2,(%r8)
 jne Lroute_absent
 movq 16(%r8),%rax
 movq %rax,0x55088
 xorl %eax,%eax
 retq
Lneighbor_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_scan
 movq %r10,0x55098
 jmp Lroute_absent
Lneighbor_source:
 movl $0x55100,%r8d
 xorl %r9d,%r9d
Lneighbor_source_next:
 cmpq $2,(%r8)
 jne Lneighbor_source_advance
 callq Lneighbor_valid
 testl %eax,%eax
 jnz Lneighbor_source_advance
 movq 6(%rdi),%rax
 shlq $16,%rax
 shrq $16,%rax
 cmpq 16(%r8),%rax
 jne Lneighbor_source_advance
 movq %rax,0x55088
 xorl %eax,%eax
 retq
Lneighbor_source_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_source_next
 jmp Lroute_absent
Lneighbor_probe:
 movq 0x55098,%r8
 cmpq $-1,%r8
 je Lpending_full
 movq %r8,%r9
 subq $0x55100,%r9
 cmpq $192,%r9
 ja Lnat_policy
 shrq $6,%r9
 shlq $11,%r9
 addq $0x56000,%r9
 cmpq $0,(%r9)
 jne Lpending_full
 cmpq $1514,0x5ac8
 ja Lnat_bad
 movq 0x5ac8,%rax
 movq %rax,8(%r9)
 movq 0x53f18,%rax
 movq %rax,16(%r9)
 movq %rax,24(%r8)
 movq 0x502c8,%rax
 movq %rax,24(%r9)
 movq 0x50ac8,%rax
 movq %rax,32(%r9)
 movq %rax,32(%r8)
 movq 0x55000,%rax
 movq %rax,40(%r9)
 movq %rax,40(%r8)
 movl 0x55080,%eax
 movl %eax,48(%r9)
 movl %eax,8(%r8)
 pushq %rdi
 movq %rdi,%rsi
 leaq 64(%r9),%rdi
 movq 0x5ac8,%rcx
 rep movsb
 popq %rdi
 movq $1,(%r9)
 movq $1,(%r8)
 incq 0x540c0
 pushq %rdi
 movl $60,%ecx
 xorl %eax,%eax
 rep stosb
 popq %rdi
 movl $-1,(%rdi)
 movw $-1,4(%rdi)
 movl $0x32465202,6(%rdi)
 movw $0x0400,10(%rdi)
 movw $0x0608,12(%rdi)
 movw $0x0100,14(%rdi)
 movw $8,16(%rdi)
 movw $0x0406,18(%rdi)
 movw $0x0100,20(%rdi)
 movl $0x32465202,22(%rdi)
 movw $0x0400,26(%rdi)
 movl $0x026433c6,28(%rdi)
 movl 0x55080,%eax
 movl %eax,38(%rdi)
 movq $60,0x5ac8
 movq $4,0x507e8
 xorl %eax,%eax
 retq
Lpending_full:
 incq 0x540d8
 movl $44,%eax
 retq
Lneighbor_reply:
 cmpq $1,0x5ad0
 jne Lnat_policy
 cmpq $60,0x5ac8
 jne Lnat_bad
 cmpw $0x0608,12(%rdi)
 jne Lnat_bad
 cmpw $0x0100,14(%rdi)
 jne Lnat_bad
 cmpw $8,16(%rdi)
 jne Lnat_bad
 cmpw $0x0406,18(%rdi)
 jne Lnat_bad
 cmpl $0x32465202,(%rdi)
 jne Lnat_policy
 cmpw $0x0400,4(%rdi)
 jne Lnat_policy
 cmpl $0x32465202,32(%rdi)
 jne Lnat_policy
 cmpw $0x0400,36(%rdi)
 jne Lnat_policy
 cmpl $0x026433c6,38(%rdi)
 jne Lnat_policy
 movl 6(%rdi),%eax
 cmpl %eax,22(%rdi)
 jne Lnat_policy
 movzwl 10(%rdi),%eax
 cmpw %ax,26(%rdi)
 jne Lnat_policy
 testb $1,6(%rdi)
 jnz Lnat_policy
 movl 6(%rdi),%eax
 movzwl 10(%rdi),%edx
 orl %edx,%eax
 jz Lnat_policy
 movl $0x55100,%r8d
 xorl %r9d,%r9d
Lneighbor_reply_next:
 cmpq $1,(%r8)
 jne Lneighbor_reply_advance
 movl 28(%rdi),%eax
 cmpl 8(%r8),%eax
 jne Lneighbor_reply_advance
 callq Lneighbor_valid
 testl %eax,%eax
 jnz Lnat_policy
 movq 6(%rdi),%rax
 shlq $16,%rax
 shrq $16,%rax
 movq %rax,16(%r8)
 movq 0x53f18,%rax
 movq %rax,24(%r8)
 movq $2,(%r8)
 incq %r9
 movq %r9,0x550a0
 movl $42,%eax
 retq
Lneighbor_reply_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_reply_next
 jmp Lnat_policy
# Transfer one pending owner into staging, clear original before revalidation/TX.
Lpending_flush:
 cmpq $1,0x5a28
 jne Lpending_done
 cmpq $0,0x550a0
 je Lpending_done
 pushq 0x5ad0
 pushq 0x5ad8
 pushq 0x5ac0
 pushq 0x5ac8
 movq 0x550a0,%r15
 movq $0,0x550a0
 decq %r15
 cmpq $3,%r15
 ja Lpending_restore
 shlq $11,%r15
 addq $0x56000,%r15
 cmpq $1,(%r15)
 jne Lpending_restore
 callq Lclock_now
 testl %edx,%edx
 jnz Lpending_cancel
 movq %rax,0x53f18
 subq 16(%r15),%rax
 jc Lpending_cancel
 cmpq 0x5a68,%rax
 jae Lpending_cancel
 movq 0x502c8,%rax
 cmpq 24(%r15),%rax
 jne Lpending_cancel
 movq 0x50ac8,%rax
 cmpq 32(%r15),%rax
 jne Lpending_cancel
 movq 0x55000,%rax
 cmpq 40(%r15),%rax
 jne Lpending_cancel
 movq 8(%r15),%rcx
 cmpq $60,%rcx
 jb Lpending_cancel
 cmpq $1514,%rcx
 ja Lpending_cancel
 movq %rcx,0x5ac8
 leaq 64(%r15),%rsi
 movl $0x51040,%edi
 rep movsb
 movq %r15,%rdi
 movl $256,%ecx
 xorl %eax,%eax
 rep stosq
 movq $0,0x5ad0
 movq $1,0x5ad8
 movq $2,0x507e0
 movq $0,0x507e8
 callq Lnat_transform
 testl %eax,%eax
 jnz Lpending_result
 movq $1,%rax
 callq Lrelay_select
 testl %eax,%eax
 jnz Lpending_result
 movq $1,0x5c28
 callq Lrelay_transmit
 testl %eax,%eax
 jnz Lpending_tx_failed
 callq Lnat_commit
 jmp Lpending_save
Lpending_tx_failed:
 pushq %rax
 callq Lshutdown
 callq Lnat_revoke
 popq %rax
Lpending_save:
 movq %rax,0x550a8
 callq Lrelay_save
 movq 0x550a8,%rax
Lpending_result:
 movq %rax,0x550a8
 testl %eax,%eax
 jnz Lpending_failed
 incq 0x540c8
 jmp Lpending_clear_stage
Lpending_failed:
 incq 0x540d0
 jmp Lpending_clear_stage
Lpending_cancel:
 movq %r15,%rdi
 movl $256,%ecx
 xorl %eax,%eax
 rep stosq
 incq 0x540d0
 movq $45,0x550a8
Lpending_clear_stage:
 callq Ltcp_scratch_clear
 movl $0x51000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
Lpending_restore:
 popq 0x5ac8
 popq 0x5ac0
 popq 0x5ad8
 popq 0x5ad0
Lpending_done:
 retq

# Called by the continuous service, so expired owners do not await new traffic.
Lneighbor_sweep:
 movl $0x55100,%r8d
 xorl %r9d,%r9d
Lneighbor_sweep_next:
 callq Lneighbor_valid
 testl %eax,%eax
 jz Lneighbor_sweep_advance
 callq Lneighbor_erase
Lneighbor_sweep_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_sweep_next
 retq
