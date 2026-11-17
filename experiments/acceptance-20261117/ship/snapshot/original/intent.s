# Experimental plaintext LAN-only UDP9000 endpoint, not authenticated transport.
# State:epoch,seen,pending,length,value,deadline,clock,mode,cap,configured,ifgen,origin.
Lintent_init:
 movabsq $0x800000000005a003,%rax
 movq %rax,0x42d0
 invlpg 0x5a000
 movl $0x5a000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 callq Lsecure_init
 retq
Lintent_revoke:
 movq $0,0x5a010
 movq $0,0x5a018
 movq $0,0x5a020
 movq $0,0x5a028
 movq $0,0x5a048
 retq
Lintent_latest:
 xorl %r15d,%r15d
 jmp Lintent_reset
Lintent_preserve:
 movl $1,%r15d
Lintent_reset:
 movl $20,%r14d
 cmpq $1,0x5a28
 jne Lintent_reset_report
 testq $1,0x5a30
 jz Lintent_reset_report
 callq Lclock_now
 testl %edx,%edx
 jnz Lintent_reset_report
 movq %rax,%r11
 cmpl $-1,0x5a000
 je Lintent_reset_report
 incq 0x5a000
 callq Lintent_revoke
 movq $0,0x5a008
 movq $0,0x5a030
 movq %r15,0x5a038
 movq $1000,0x5a040
 movq $1,0x5a048
 movq 0x502c8,%rax
 movq %rax,0x5a050
 movq %r11,0x5a058
 movl $13,%r14d
Lintent_reset_report:
 leaq Lintent_text(%rip),%rsi
 callq Lputs
 movq %r14,%rax
 callq Lhex
 cmpq $1,0x5a28
 jne Lintent_report_end
 leaq Lintent_epoch_text(%rip),%rsi
 callq Lputs
 movq 0x5a000,%rax
 callq Lhex
Lintent_report_end:
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
# Current observedHPETtick53f18 -> bounded localmilliseconds, never caller time.
Lintent_time:
 movq 0x53f18,%rax
 subq 0x5a058,%rax
 jc Lintent_time_bad
 mulq 0x5a58
 movabsq $1000000000000,%rcx
 cmpq %rcx,%rdx
 jae Lintent_time_bad
 divq %rcx
 cmpq $1000000000,%rax
 ja Lintent_time_bad
 cmpq 0x5a030,%rax
 jb Lintent_time_bad
 movq %rax,0x5a030
 clc
 retq
Lintent_time_bad:
 stc
 retq
Lintent_expire:
 cmpq $1,0x5a048
 jne Lintent_expire_done
 movq 0x502c8,%rax
 cmpq 0x5a050,%rax
 jne Lintent_revoke
 callq Lintent_time
 jc Lintent_expire_done
 cmpq $0,0x5a010
 je Lintent_expire_done
 cmpq 0x5a028,%rax
 jb Lintent_expire_done
 movq $0,0x5a010
 movq $0,0x5a018
 movq $0,0x5a020
 movq $0,0x5a028
 incq 0x5a060
Lintent_expire_done:
 retq
Lintent_plain_request:
 cmpl $0x03004d0a,26(%rdi)
 jne Lnat_policy
 cmpq $114,0x5ac8
 jne Lnat_bad
 cmpq $80,%r12
 jne Lnat_bad
 cmpw $0,40(%rdi)
 je Lnat_checksum_bad
 cmpb $0,22(%rdi)
 je Lnat_ttl
 movabsq $0x2131304349324652,%rax
 cmpq %rax,42(%rdi)
 jne Lnat_bad
 movl $1,%r14d
 cmpq $0,50(%rdi)
 je Lsecure_hello
 movl $2,%r14d
 cmpq $1,0x5a048
 jne Lintent_reply
 movq 58(%rdi),%rax
 cmpq 0x5a000,%rax
 jne Lintent_reply
 movq 0x502c8,%rax
 cmpq 0x5a050,%rax
 jne Lintent_reply
 movl $9,%r14d
 cmpq $0,74(%rdi)
 jne Lintent_reply
 callq Lintent_time
 jc Lintent_reply
 callq Lintent_expire
 movl $8,%r14d
 cmpq $1,50(%rdi)
 je Lintent_submit
 cmpq $2,50(%rdi)
 je Lintent_complete
 cmpq $3,50(%rdi)
 je Lintent_complete
 cmpq $4,50(%rdi)
 jne Lintent_reply
 xorl %r14d,%r14d
 jmp Lintent_reply
Lintent_submit:
 movl $3,%r14d
 movq 66(%rdi),%rax
 testq %rax,%rax
 jz Lintent_reply
 cmpq 0x5a008,%rax
 jbe Lintent_reply
 shrq $32,%rax
 jnz Lintent_reply
 movl $4,%r14d
 movq 90(%rdi),%rcx
 testq %rcx,%rcx
 jz Lintent_reply
 cmpq $8,%rcx
 ja Lintent_reply
 movl $5,%r14d
 movq 82(%rdi),%rdx
 testq %rdx,%rdx
 jz Lintent_reply
 cmpq 0x5a040,%rdx
 ja Lintent_reply
 cmpq $0,106(%rdi)
 jne Lintent_reply
 movl $6,%r14d
 cmpq $0,0x5a010
 je Lintent_store
 cmpq $0,0x5a038
 jne Lintent_reply
Lintent_store:
 movq 66(%rdi),%rax
 movq %rax,0x5a008
 movq %rax,0x5a010
 movq %rcx,0x5a018
 movq 98(%rdi),%rax
 cmpq $8,%rcx
 je Lintent_value
 shlq $3,%rcx
 movq $-1,%r8
 shlq %cl,%r8
 notq %r8
 andq %r8,%rax
Lintent_value:
 movq %rax,0x5a020
 addq 0x5a030,%rdx
 movq %rdx,0x5a028
 xorl %r14d,%r14d
 jmp Lintent_reply
Lintent_complete:
 movl $7,%r14d
 movq 66(%rdi),%rax
 testq %rax,%rax
 jz Lintent_reply
 cmpq 0x5a010,%rax
 jne Lintent_reply
 movq $0,0x5a010
 movq $0,0x5a018
 movq $0,0x5a020
 movq $0,0x5a028
 movl $12,%r14d
 cmpq $3,50(%rdi)
 jne Lintent_reply
 movl $11,%r14d
Lintent_reply:
 movq 58(%rdi),%r9
 movq 66(%rdi),%r10
 movabsq $0x2131305249324652,%rax
 movq %rax,42(%rdi)
 movq %r9,50(%rdi)
 movq %r10,58(%rdi)
 movq %r14,66(%rdi)
 movq 0x5a010,%rax
 movq %rax,74(%rdi)
 movq 0x5a018,%rax
 movq %rax,82(%rdi)
 movq 0x5a020,%rax
 movq %rax,90(%rdi)
 movq 0x5a008,%rax
 movq %rax,98(%rdi)
 movq 0x5a028,%rax
 movq %rax,106(%rdi)
 movl 6(%rdi),%eax
 movw 10(%rdi),%cx
 movl %eax,(%rdi)
 movw %cx,4(%rdi)
 movl $0x32465202,6(%rdi)
 movw $0x0200,10(%rdi)
 movl 26(%rdi),%eax
 movl %eax,30(%rdi)
 movl $0x02004d0a,26(%rdi)
 movw 34(%rdi),%ax
 movw %ax,36(%rdi)
 movw $0x2823,34(%rdi)
 movw $0x6400,16(%rdi)
 movw $0x5000,38(%rdi)
 movb $65,22(%rdi)
 movq $114,0x5ac8
 movl $100,%r13d
 movl $80,%r12d
 movq $0,0x507e0
 movq $6,0x507e8
 incq 0x5a068
 jmp Lsecure_reply
Lintent_text:
 .asciz "Intent result=0x"
Lintent_epoch_text:
 .asciz " epoch=0x"
