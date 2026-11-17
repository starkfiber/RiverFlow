# Local echo and LAN router errors only. No ICMP NAT translation/fragmentation.
Licmp_trusted_source:
 cmpl $0x32465202,(%rdi)
 jne Licmp_source_bad
 cmpl $0x32465202,6(%rdi)
 jne Licmp_source_bad
 cmpq $0,0x5ad0
 jne Licmp_source_wan
 cmpw $0x0200,4(%rdi)
 jne Licmp_source_bad
 cmpw $0x0300,10(%rdi)
 jne Licmp_source_bad
 movl 26(%rdi),%eax
 movl %eax,%ecx
 andl $0xffffff,%eax
 cmpl $0x004d0a,%eax
 jne Licmp_source_bad
 shrl $24,%ecx
 cmpl $3,%ecx
 jb Licmp_source_bad
 cmpl $254,%ecx
 ja Licmp_source_bad
 xorl %eax,%eax
 retq
Licmp_source_wan:
 cmpw $0x0400,4(%rdi)
 jne Licmp_source_bad
 cmpw $0x0500,10(%rdi)
 jne Licmp_source_bad
 cmpl $0x096433c6,26(%rdi)
 jne Licmp_source_bad
 xorl %eax,%eax
 retq
Licmp_source_bad:
 movl $33,%eax
 retq
Licmp_echo:
 callq Licmp_trusted_source
 testl %eax,%eax
 jnz Lnat_policy
 cmpb $0,22(%rdi)
 je Lnat_ttl
 movl $0x02004d0a,%eax
 cmpq $0,0x5ad0
 je Licmp_echo_destination
 movl $0x026433c6,%eax
Licmp_echo_destination:
 cmpl %eax,30(%rdi)
 jne Lnat_policy
 leaq 34(%rdi),%rsi
 leal -20(%r13d),%ecx
 xorl %edx,%edx
 callq Lnat_sum
 testl %eax,%eax
 jnz Lnat_checksum_bad
 cmpb $8,34(%rdi)
 jne Lnat_policy
 cmpb $0,35(%rdi)
 jne Lnat_bad
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 incq 0x54060(%rdx)
 callq Licmp_admit
 testl %eax,%eax
 jnz Licmp_rate_refused
 movl 26(%rdi),%eax
 movl 30(%rdi),%ecx
 movl %eax,30(%rdi)
 movl %ecx,26(%rdi)
 movb $0,34(%rdi)
 movq $2,0x507e8
 jmp Licmp_finalize
Licmp_time_exceeded:
 movw $11,%r14w
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 incq 0x540a0(%rdx)
 jmp Licmp_error
Licmp_net_unreachable:
 movw $3,%r14w
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 incq 0x540a8(%rdx)
 jmp Licmp_error
Licmp_port_unreachable:
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 incq 0x540b0(%rdx)
 movw $0x0303,%r14w
Licmp_error:
 callq Licmp_admit
 testl %eax,%eax
 jnz Licmp_rate_refused
 # Quote the intact originalIPv4 header and first8 payload bytes before overwrite.
 pushq %rdi
 leaq 14(%rdi),%rsi
 leaq 42(%rdi),%rdi
 movl $28,%ecx
 cld
 rep movsb
 popq %rdi
 movw %r14w,34(%rdi)
 movl $0,38(%rdi)
 movl 26(%rdi),%eax
 movl %eax,30(%rdi)
 movl $0x02004d0a,26(%rdi)
 movw $0x3800,16(%rdi)
 movw $0,20(%rdi)
 movb $1,23(%rdi)
 movl $56,%r13d
 movq $70,0x5ac8
 movq $3,0x507e8
Licmp_finalize:
 movl 6(%rdi),%eax
 movw 10(%rdi),%cx
 movl (%rdi),%edx
 movw 4(%rdi),%r8w
 movl %eax,(%rdi)
 movw %cx,4(%rdi)
 movl %edx,6(%rdi)
 movw %r8w,10(%rdi)
 movb $64,22(%rdi)
 movw $0,24(%rdi)
 leaq 14(%rdi),%rsi
 movl $20,%ecx
 xorl %edx,%edx
 callq Lnat_sum
 movw %ax,24(%rdi)
 movw $0,36(%rdi)
 leaq 34(%rdi),%rsi
 leal -20(%r13d),%ecx
 xorl %edx,%edx
 callq Lnat_sum
 movw %ax,36(%rdi)
 movq 0x5ad0,%rax
 movq %rax,0x507e0
 xorl %eax,%eax
 retq
Licmp_admit:
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 movq 0x53f18,%rax
 subq 0x54090(%rdx),%rax
 jc Licmp_rate_refused
 cmpq 0x5a68,%rax
 jb Licmp_check_budget
 movq 0x53f18,%rax
 movq %rax,0x54090(%rdx)
 movq $0,0x54098(%rdx)
Licmp_check_budget:
 cmpq $16,0x54098(%rdx)
 jae Licmp_rate_refused
 incq 0x54098(%rdx)
 xorl %eax,%eax
 retq
Licmp_rate_refused:
 movl $41,%eax
 retq
Licmp_commit:
 movq 0x5a38,%rdx
 shlq $8,%rdx
 incq 0x54068(%rdx)
 xorl %eax,%eax
 retq
