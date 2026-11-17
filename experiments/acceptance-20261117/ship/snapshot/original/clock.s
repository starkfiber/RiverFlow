# QEMU PC/Q35 lab HPET contract: fixed mapped address, 64-bit counter and period.
# Not ACPI discovery, physical clock calibration or hostile-hypervisor time.
Lclock_init:
 cmpq $1,0x5a28
 jne Lclock_fail
 cmpq $0,0x4290
 jne Lclock_fail
 movl $1,%eax
 cpuid
 testl $0x10000,%edx
 jz Lclock_map
 movl $0x277,%ecx
 rdmsr
 shrl $24,%eax
 testb %al,%al
 jnz Lclock_fail
Lclock_map:
 movabsq $0x80000000fed0001b,%rax
 movq %rax,0x4290
 invlpg 0x52000
 movq 0x52000,%r8
 testl $0x2000,%r8d
 jz Lclock_unmap_fail
 movq %r8,%rcx
 shrq $32,%rcx
 testq %rcx,%rcx
 jz Lclock_unmap_fail
 cmpq $100000000,%rcx
 ja Lclock_unmap_fail
 movq %rcx,0x5a58
 movq 0x52010,%rax
 testb $2,%al
 jnz Lclock_unmap_fail
 orq $1,%rax
 movq %rax,0x52010
 testq $1,0x52010
 jz Lclock_unmap_fail
 movabsq $3000000000000000,%rax
 xorl %edx,%edx
 divq %rcx
 testq %rdx,%rdx
 jz Lclock_lifetime
 incq %rax
Lclock_lifetime:
 movq %rax,0x5a68
 movq 0x520f0,%r8
 movl $1000000,%ecx
Lclock_progress:
 movq 0x520f0,%rax
 cmpq %r8,%rax
 jb Lclock_unmap_fail
 ja Lclock_started
 loop Lclock_progress
 jmp Lclock_unmap_fail
Lclock_started:
 movq %rax,0x5a60
 movq $1,0x5a50
 xorl %edx,%edx
 retq
Lclock_unmap_fail:
 movq $0,0x4290
 invlpg 0x52000
Lclock_fail:
 movq $2,0x5a50
 callq Lnat_revoke
 movl $37,%edx
 retq
Lclock_now:
 cmpq $0,0x5a50
 je Lclock_init
 cmpq $1,0x5a50
 jne Lclock_fail
 movl 0x52004,%eax
 cmpq 0x5a58,%rax
 jne Lclock_fail
 movq 0x52010,%rax
 andl $3,%eax
 cmpl $1,%eax
 jne Lclock_fail
 movq 0x520f0,%rax
 cmpq 0x5a60,%rax
 jb Lclock_fail
 movq %rax,0x5a60
 xorl %edx,%edx
 retq
Lclock_report:
 pushfq
 cli
 callq Lclock_now
 popfq
 leaq Lclock_text(%rip),%rsi
 callq Lputs
 movq 0x5a50,%rax
 callq Lhex
 leaq Lclock_period_text(%rip),%rsi
 callq Lputs
 movq 0x5a58,%rax
 callq Lhex
 leaq Lclock_count_text(%rip),%rsi
 callq Lputs
 movq 0x5a60,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lclock_text:
 .asciz "HPET state=0x"
Lclock_period_text:
 .asciz " period-fs=0x"
Lclock_count_text:
 .asciz " counter=0x"
