# Lab AEAD channel. Fresh directional keys+bootID are trusted-console provisioned.
# No embedded key, native entropy, autonomous boot provisioning or PKI claim.
Lsecure_init:
 movabsq $0x800000000005b003,%rax
 movq %rax,0x42d8
 addq $4096,%rax
 movq %rax,0x42e0
 invlpg 0x5b000
 invlpg 0x5c000
 movl $0x5b000,%edi
 movl $1024,%ecx
 xorl %eax,%eax
 rep stosq
 retq
Lsecure_work_clear:
 pushq %rax
 pushq %rcx
 pushq %rdi
 movl $0x5c000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 popq %rdi
 popq %rcx
 popq %rax
 retq
Lsecure_provision:
 xorl %r15d,%r15d
 cmpq $1,0x5a28
 jne Lsecure_provision_bad_no_map
 cmpq $0,0x5b050
 jne Lsecure_provision_bad
 movl $0x5c300,%edi
 movl $80,%r8d
Lsecure_key_byte:
 xorl %ebx,%ebx
 movl $2,%r9d
Lsecure_key_digit:
 callq Lroute_char
 jc Lsecure_provision_bad
 cmpb $'0',%al
 jb Lsecure_provision_bad
 cmpb $'9',%al
 jbe Lsecure_key_decimal
 cmpb $'a',%al
 jb Lsecure_provision_bad
 cmpb $'f',%al
 ja Lsecure_provision_bad
 subb $87,%al
 jmp Lsecure_key_accum
Lsecure_key_decimal:
 subb $48,%al
Lsecure_key_accum:
 shll $4,%ebx
 movzbl %al,%eax
 orl %eax,%ebx
 decl %r9d
 jnz Lsecure_key_digit
 movb %bl,(%rdi)
 incl %edi
 decl %r8d
 jnz Lsecure_key_byte
 callq Lroute_char
 jc Lsecure_provision_bad
 cmpb $10,%al
 jne Lsecure_provision_bad
 movl $1,%r15d
 xorl %eax,%eax
 xorl %edx,%edx
 xorl %r9d,%r9d
 movl $32,%ecx
Lsecure_keys_check:
 movzbl 0x5c300(%rcx),%r8d
 # Loop uses offsets0..31, not1..32.
 decl %ecx
 movzbl 0x5c300(%rcx),%r8d
 orl %r8d,%eax
 movzbl 0x5c320(%rcx),%r10d
 orl %r10d,%edx
 xorl %r10d,%r8d
 orl %r8d,%r9d
 testl %ecx,%ecx
 jnz Lsecure_keys_check
 testl %eax,%eax
 jz Lsecure_provision_bad
 testl %edx,%edx
 jz Lsecure_provision_bad
 testl %r9d,%r9d
 jz Lsecure_provision_bad
 movq 0x5c340,%rax
 orq 0x5c348,%rax
 jz Lsecure_provision_bad
 movl $0x5c300,%esi
 movl $0x5b000,%edi
 movl $10,%ecx
 rep movsq
 movq $1,0x5b050
 callq Lsecure_work_clear
 xorl %r14d,%r14d
 jmp Lsecure_provision_report
Lsecure_provision_bad:
 testl %r15d,%r15d
 jnz Lsecure_provision_clear
 cmpb $10,%al
 je Lsecure_provision_clear
 movq $1,0x55090
Lsecure_provision_clear:
 callq Lsecure_work_clear
Lsecure_provision_bad_no_map:
 movl $47,%r14d
Lsecure_provision_report:
 leaq Lsecure_key_text(%rip),%rsi
 callq Lputs
 movq %r14,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lsecure_erase:
 cmpq $1,0x5a28
 jne Lsecure_provision_bad_no_map
 callq Lintent_revoke
 movl $0x5b000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 movq $2,0x5b050
 callq Lsecure_work_clear
 xorl %r14d,%r14d
 jmp Lsecure_provision_report
Lsecure_key_text:
 .asciz "Credentials result=0x"
# rax=open, rsi=key address; exact128-byte UDPpayload header40+cipher72+tag16.
Lsecure_context:
 movq %rax,0x5c000
 movl $0x5c008,%edi
 movl $4,%ecx
 rep movsq
 movl 0x5b068,%eax
 movl %eax,0x5c028
 movq 0x5b060,%rax
 movq %rax,0x5c02c
 movq $0x5106a,0x5c038
 movq $40,0x5c040
 movq $0x51092,0x5c048
 movq $72,0x5c050
 movq $0x510da,0x5c058
 retq
Lsecure_crypt:
 pushq %rbx
 pushq %rbp
 pushq %r12
 pushq %r13
 pushq %r14
 pushq %r15
 movq %rsp,%rbx
 andq $-16,%rsp
 movl $0x5c000,%edi
 callq Lcrypto_rf2_aead
 movq %rbx,%rsp
 popq %r15
 popq %r14
 popq %r13
 popq %r12
 popq %rbp
 popq %rbx
 retq
Lintent_request:
 cmpl $0x03004d0a,26(%rdi)
 jne Lnat_policy
 cmpq $170,0x5ac8
 jne Lnat_bad
 cmpq $136,%r12
 jne Lnat_bad
 cmpw $0,40(%rdi)
 je Lnat_checksum_bad
 cmpq $1,0x5b050
 jne Lnat_policy
 movabsq $0x2131304541324652,%rax
 cmpq %rax,42(%rdi)
 jne Lnat_bad
 movq 50(%rdi),%rax
 cmpq 0x5b040,%rax
 jne Lnat_policy
 movq 58(%rdi),%rax
 cmpq 0x5b048,%rax
 jne Lnat_policy
 movq 66(%rdi),%rax
 movq %rax,%rdx
 shrq $32,%rdx
 jnz Lnat_policy
 movq %rax,0x5b068
 movq 74(%rdi),%rax
 cmpq 0x5b058,%rax
 jbe Lnat_policy
 movq %rax,0x5b060
 movl $1,%eax
 movl $0x5b000,%esi
 callq Lsecure_context
 callq Lsecure_crypt
 testl %eax,%eax
 jnz Lsecure_auth_bad
 movl $0x51040,%edi
 movq 98(%rdi),%rax
 cmpq 0x5b068,%rax
 jne Lsecure_auth_bad
 # Authenticated body is copied only after tag and inner/outerepoch consistency.
 leaq 82(%rdi),%rsi
 leaq 42(%rdi),%rdi
 movl $9,%ecx
 rep movsq
 movq 0x5b060,%rax
 movq %rax,0x5b058
 callq Lsecure_work_clear
 movl $0x51040,%edi
 movq $114,0x5ac8
 movl $80,%r12d
 jmp Lintent_plain_request
Lsecure_auth_bad:
 callq Lsecure_work_clear
 jmp Lnat_policy
Lsecure_hello:
 movl $1,%r14d
 cmpq $0,58(%rdi)
 jne Lintent_reply
 cmpq $0,66(%rdi)
 jne Lintent_reply
 cmpq $0,74(%rdi)
 jne Lintent_reply
 cmpq $0,82(%rdi)
 jne Lintent_reply
 cmpq $0,90(%rdi)
 jne Lintent_reply
 cmpq $0,98(%rdi)
 jne Lintent_reply
 cmpq $1,106(%rdi)
 ja Lintent_reply
 cmpl $-1,0x5a000
 je Lintent_reply
 incq 0x5a000
 callq Lintent_revoke
 movq $0,0x5a008
 movq $0,0x5a030
 movq 106(%rdi),%rax
 movq %rax,0x5a038
 movq $1000,0x5a040
 movq $1,0x5a048
 movq 0x502c8,%rax
 movq %rax,0x5a050
 movq 0x53f18,%rax
 movq %rax,0x5a058
 movq 0x5a000,%rax
 movq %rax,58(%rdi)
 movl $13,%r14d
 jmp Lintent_reply
Lsecure_reply:
 # Move the72-byte reply before constructing authenticated outer header.
 leaq 42(%rdi),%rsi
 movl $0x5c200,%edi
 movl $9,%ecx
 rep movsq
 movl $0x51040,%edi
 movabsq $0x2131305241324652,%rax
 movq %rax,42(%rdi)
 movq 0x5b040,%rax
 movq %rax,50(%rdi)
 movq 0x5b048,%rax
 movq %rax,58(%rdi)
 movq 0x5b068,%rax
 movq %rax,66(%rdi)
 movq 0x5b060,%rax
 movq %rax,74(%rdi)
 movl $0x5c200,%esi
 leaq 82(%rdi),%rdi
 movl $9,%ecx
 rep movsq
 xorl %eax,%eax
 movl $0x5b020,%esi
 callq Lsecure_context
 callq Lsecure_crypt
 testl %eax,%eax
 jnz Lsecure_auth_bad
 callq Lsecure_work_clear
 movl $0x51040,%edi
 movq $170,0x5ac8
 movw $0x9c00,16(%rdi)
 movw $0x8800,38(%rdi)
 movl $156,%r13d
 movl $136,%r12d
 jmp Lnat_rechecksum
