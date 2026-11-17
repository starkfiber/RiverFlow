# Local UART-only four-route lab table. Network values are host-order u32.
# ARP is solicited discovery, not cryptographic peer authentication.
Lroute_init:
 movabsq $0x8000000000055003,%rax
 movq %rax,0x42a8
 invlpg 0x55000
 movl $0x55000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 callq Lpending_init
 callq Lintent_init
 movq $1,0x55000
 movl $0xc6336400,0x55010
 movl $24,0x55014
 movl $0xc6336409,0x55018
 movl $1,0x5501c
 retq
# R followed by40lowercase hexadecimal digits and LF: expectedGeneration,
# slot, network, prefixLength, nextHop. A zero nextHop deletes a slot.
# Strict fixed frame, bounded polling, staged validation; no network authority.
Lroute_config:
 xorl %r15d,%r15d
 cmpq $1,0x5a28
 jne Lroute_config_bad
 movl $0x55400,%edi
 movl $5,%r8d
Lroute_word:
 xorl %ebx,%ebx
 movl $8,%r9d
Lroute_nibble:
 callq Lroute_char
 jc Lroute_config_bad
 cmpb $'0',%al
 jb Lroute_config_bad
 cmpb $'9',%al
 jbe Lroute_digit
 cmpb $'a',%al
 jb Lroute_config_bad
 cmpb $'f',%al
 ja Lroute_config_bad
 subb $87,%al
 jmp Lroute_accum
Lroute_digit:
 subb $48,%al
Lroute_accum:
 shll $4,%ebx
 movzbl %al,%eax
 orl %eax,%ebx
 decl %r9d
 jnz Lroute_nibble
 movl %ebx,(%rdi)
 addl $4,%edi
 decl %r8d
 jnz Lroute_word
 callq Lroute_char
 jc Lroute_config_bad
 cmpb $10,%al
 jne Lroute_config_bad
 movl $1,%r15d
 movl 0x55400,%eax
 cmpq 0x55000,%rax
 jne Lroute_config_bad
 cmpl $3,0x55404
 ja Lroute_config_bad
 movl 0x5540c,%ecx
 cmpl $32,%ecx
 ja Lroute_config_bad
 callq Lroute_mask
 notl %eax
 testl %eax,0x55408
 jnz Lroute_config_bad
 movl 0x55410,%eax
 testl %eax,%eax
 jz Lroute_apply
 movl %eax,%edx
 andl $0xffffff00,%eax
 cmpl $0xc6336400,%eax
 jne Lroute_config_bad
 andl $255,%edx
 cmpl $3,%edx
 jb Lroute_config_bad
 cmpl $254,%edx
 ja Lroute_config_bad
 # Duplicate active prefixes in other slots are ambiguous and rejected.
 movl $0x55010,%r8d
 xorl %r9d,%r9d
 cmpl $0,0x55410
 je Lroute_apply
Lroute_duplicate:
 cmpl 0x55404,%r9d
 je Lroute_duplicate_next
 cmpl $1,12(%r8)
 jne Lroute_duplicate_next
 movl 0x55408,%eax
 cmpl (%r8),%eax
 jne Lroute_duplicate_next
 movl 0x5540c,%eax
 cmpl 4(%r8),%eax
 je Lroute_config_bad
Lroute_duplicate_next:
 addl $16,%r8d
 incl %r9d
 cmpl $4,%r9d
 jb Lroute_duplicate
Lroute_apply:
 cmpl $-1,0x55000
 je Lroute_config_bad
 movl 0x55404,%edi
 shll $4,%edi
 addl $0x55010,%edi
 movl 0x55408,%eax
 movl %eax,(%rdi)
 movl 0x5540c,%eax
 movl %eax,4(%rdi)
 movl 0x55410,%eax
 movl %eax,8(%rdi)
 testl %eax,%eax
 setnz %al
 movzbl %al,%eax
 movl %eax,12(%rdi)
 incq 0x55000
 callq Lnat_revoke
 xorl %r14d,%r14d
 jmp Lroute_config_report
Lroute_config_bad:
 cmpb $10,%al
 je Lroute_no_quarantine
 testl %r15d,%r15d
 jnz Lroute_no_quarantine
 cmpq $1,0x5a28
 jne Lroute_no_quarantine
 movq $1,0x55090
Lroute_no_quarantine:
 movl $43,%r14d
Lroute_config_report:
 cmpq $1,0x5a28
 jne Lroute_report_text
 movl $0x55400,%edi
 movl $8,%ecx
 xorl %eax,%eax
 rep stosq
Lroute_report_text:
 leaq Lroute_result(%rip),%rsi
 callq Lputs
 movq %r14,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lroute_char:
 pushq %rbx
 pushq %r8
 pushq %r9
 pushq %r10
 pushq %r11
 callq Lclock_now
 testl %edx,%edx
 jnz Lroute_read_timeout
 movq %rax,%r10
 movq 0x5a68,%rax
 xorl %edx,%edx
 movl $15,%ecx
 divq %rcx
 movq %rax,%r11
 movl $65536,%esi
Lroute_wait:
 movw $0x3fd,%dx
 inb %dx,%al
 testb $1,%al
 jnz Lroute_read
 decl %esi
 jz Lroute_read_timeout
 testl $63,%esi
 jnz Lroute_wait
 callq Lclock_now
 testl %edx,%edx
 jnz Lroute_read_timeout
 subq %r10,%rax
 jc Lroute_read_timeout
 cmpq %r11,%rax
 jb Lroute_wait
Lroute_read_timeout:
 popq %r11
 popq %r10
 popq %r9
 popq %r8
 popq %rbx
 xorl %eax,%eax
 stc
 retq
Lroute_read:
 movw $0x3f8,%dx
 inb %dx,%al
 popq %r11
 popq %r10
 popq %r9
 popq %r8
 popq %rbx
 clc
 retq
Lroute_mask:
 movl $32,%eax
 subl %ecx,%eax
 movl %eax,%ecx
 movl $-1,%eax
 cmpl $32,%ecx
 jne Lroute_mask_shift
 xorl %eax,%eax
 retq
Lroute_mask_shift:
 shll %cl,%eax
 retq
Lroute_lookup:
 movl 30(%rdi),%r11d
 bswapl %r11d
 movl $0x55010,%r8d
 movl $-1,%r9d
 xorl %r10d,%r10d
Lroute_next:
 cmpl $1,12(%r8)
 jne Lroute_advance
 movl 4(%r8),%ecx
 movl %ecx,%edx
 callq Lroute_mask
 andl %r11d,%eax
 cmpl (%r8),%eax
 jne Lroute_advance
 cmpl $-1,%r9d
 je Lroute_choose
 cmpl %r9d,%edx
 jbe Lroute_advance
Lroute_choose:
 movl %edx,%r9d
 movl 8(%r8),%r10d
Lroute_advance:
 addl $16,%r8d
 cmpl $0x55050,%r8d
 jb Lroute_next
 testl %r10d,%r10d
 jz Lroute_absent
 bswapl %r10d
 movl %r10d,0x55080
 xorl %eax,%eax
 retq
Lroute_absent:
 movl $39,%eax
 retq
Lroute_result:
 .asciz "Route result=0x"
