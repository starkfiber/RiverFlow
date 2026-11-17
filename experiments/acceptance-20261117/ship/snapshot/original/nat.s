# Bounded 32-flow UDP NAT, fixed routed LAN/upstream peer MACs, not a general firewall.
Lnat_out:
 movq $1,0x5ad8
 movq $0,0x5ad0
 jmp Lrelay_command
Lnat_in:
 movq $2,0x5ad8
 movq $1,0x5ad0
 jmp Lrelay_command
Lnat_transform:
 callq Lclock_now
 testl %edx,%edx
 jnz Lnat_clock_bad
 movq %rax,0x53f18
 movl $0x51040,%edi
 cmpw $0x0608,12(%rdi)
 je Larp_reply
 cmpw $8,12(%rdi)
 jne Lnat_policy
 cmpb $0x45,14(%rdi)
 jne Lnat_bad
 movzwl 16(%rdi),%r13d
 rolw $8,%r13w
 cmpl $28,%r13d
 jb Lnat_bad
 leal 14(%r13d),%eax
 cmpl $60,%eax
 jae Lnat_size
 movl $60,%eax
Lnat_size:
 cmpq 0x5ac8,%rax
 jne Lnat_bad
 movzwl 20(%rdi),%eax
 rolw $8,%ax
 testw $0xbfff,%ax
 jnz Lnat_bad
 leaq 14(%rdi),%rsi
 movl $20,%ecx
 xorl %edx,%edx
 callq Lnat_sum
 testl %eax,%eax
 jnz Lnat_checksum_bad
 cmpb $1,23(%rdi)
 je Licmp_echo
 cmpb $6,23(%rdi)
 je Ltcp_transform
 cmpb $17,23(%rdi)
 jne Lnat_policy
 movzwl 38(%rdi),%r12d
 rolw $8,%r12w
 leal -20(%r13d),%eax
 cmpl %eax,%r12d
 jne Lnat_bad
 cmpw $0,40(%rdi)
 je Lnat_addresses
 callq Lnat_udp_seed
 leaq 34(%rdi),%rsi
 movl %r12d,%ecx
 callq Lnat_sum
 testl %eax,%eax
 jnz Lnat_checksum_bad
Lnat_addresses:
 callq Lnat_expire
 cmpl $0x32465202,(%rdi)
 jne Lnat_policy
 cmpq $1,0x5ad0
 je Lnat_source_check_done
 cmpl $0x32465202,6(%rdi)
 jne Lnat_policy
Lnat_source_check_done:
 cmpq $1,0x5ad8
 jne Lnat_reverse
 cmpw $0x0200,4(%rdi)
 jne Lnat_policy
 cmpw $0x0300,10(%rdi)
 jne Lnat_policy
 movl 26(%rdi),%eax
 movl %eax,%ecx
 andl $0xffffff,%eax
 cmpl $0x004d0a,%eax
 jne Lnat_policy
 shrl $24,%ecx
 cmpl $3,%ecx
 jb Lnat_policy
 cmpl $254,%ecx
 ja Lnat_policy
 cmpl $0x02004d0a,30(%rdi)
 jne Lintent_not_local
 cmpw $0x2823,36(%rdi)
 je Lintent_request
Lintent_not_local:
 movzwl 34(%rdi),%eax
 rolw $8,%ax
 testl %eax,%eax
 jz Lnat_policy
 movq %rax,0x53f08
 movzwl 36(%rdi),%eax
 rolw $8,%ax
 testl %eax,%eax
 jz Lnat_policy
 movq %rax,0x53f10
 movl 26(%rdi),%eax
 movq %rax,0x53f38
 movl 30(%rdi),%eax
 movq %rax,0x53f40
 # Do not reflect ICMP errors for multicast, special or configured broadcast destinations.
 movzbl 30(%rdi),%eax
 testl %eax,%eax
 jz Lnat_policy
 cmpl $127,%eax
 je Lnat_policy
 cmpl $224,%eax
 jae Lnat_policy
 movl 30(%rdi),%eax
 cmpl $0xff004d0a,%eax
 je Lnat_policy
 cmpl $0xff6433c6,%eax
 je Lnat_policy
 cmpb $0,22(%rdi)
 je Lnat_ttl
 cmpb $1,22(%rdi)
 je Licmp_time_exceeded
 cmpl $0x02004d0a,%eax
 je Licmp_port_unreachable
 cmpl $0x026433c6,%eax
 je Licmp_port_unreachable
 callq Lroute_lookup
 testl %eax,%eax
 jnz Licmp_net_unreachable
 callq Lneighbor_get
 testl %eax,%eax
 jnz Lneighbor_probe
 movq $-1,%r10
 xorl %r9d,%r9d
 movl $0x53000,%r8d
Lnat_find:
 cmpq $1,(%r8)
 jne Lnat_free
 movq 0x53f08,%rax
 cmpq 8(%r8),%rax
 jne Lnat_next
 movq 0x53f10,%rax
 cmpq 16(%r8),%rax
 jne Lnat_next
 movq 0x53f38,%rax
 cmpq 56(%r8),%rax
 jne Lnat_next
 movq 0x53f40,%rax
 cmpq 64(%r8),%rax
 je Lnat_selected
 jmp Lnat_next
Lnat_free:
 cmpq $-1,%r10
 jne Lnat_next
 movq %r9,%r10
Lnat_next:
 addq $96,%r8
 incq %r9
 cmpq $32,%r9
 jb Lnat_find
 cmpq $-1,%r10
 je Lnat_full
 movq %r10,%r9
Lnat_selected:
 movq %r9,0x53f00
 movq 0x502c8,%rax
 movq %rax,0x53f28
 movq 0x50ac8,%rax
 movq %rax,0x53f30
 leal 40000(%r9d),%eax
 rolw $8,%ax
 movw %ax,34(%rdi)
 movl 0x55088,%eax
 movl %eax,(%rdi)
 movzwl 0x5508c,%eax
 movw %ax,4(%rdi)
 movw $0x0400,10(%rdi)
 movl $0x026433c6,26(%rdi)
 jmp Lnat_rechecksum
Lnat_reverse:
 cmpb $1,22(%rdi)
 jbe Lnat_ttl
 cmpw $0x0400,4(%rdi)
 jne Lnat_policy
 callq Lneighbor_source
 testl %eax,%eax
 jnz Lnat_policy
 cmpl $0x026433c6,30(%rdi)
 jne Lnat_policy
 movzwl 36(%rdi),%eax
 rolw $8,%ax
 subl $40000,%eax
 cmpl $32,%eax
 jae Lnat_no_state
 imulq $96,%rax,%rax
 leaq 0x53000(%rax),%r8
 cmpq $1,(%r8)
 jne Lnat_no_state
 movl 26(%rdi),%eax
 cmpq 64(%r8),%rax
 jne Lnat_no_state
 movzwl 34(%rdi),%eax
 rolw $8,%ax
 testl %eax,%eax
 jz Lnat_policy
 cmpq 16(%r8),%rax
 jne Lnat_no_state
 movq 8(%r8),%rax
 rolw $8,%ax
 movw %ax,36(%rdi)
 movl 56(%r8),%eax
 movl %eax,30(%rdi)
 movl $0x32465202,(%rdi)
 movw $0x0300,4(%rdi)
 movl $0x32465202,6(%rdi)
 movw $0x0200,10(%rdi)
Lnat_rechecksum:
 decb 22(%rdi)
 movw $0,24(%rdi)
 leaq 14(%rdi),%rsi
 movl $20,%ecx
 xorl %edx,%edx
 callq Lnat_sum
 movw %ax,24(%rdi)
 movw $0,40(%rdi)
 callq Lnat_udp_seed
 leaq 34(%rdi),%rsi
 movl %r12d,%ecx
 callq Lnat_sum
 testw %ax,%ax
 jnz Lnat_checksum_nonzero
 movw $0xffff,%ax
Lnat_checksum_nonzero:
 movw %ax,40(%rdi)
 xorl %eax,%eax
 retq
Lnat_commit:
 cmpq $6,0x507e8
 je Lnat_commit_done
 cmpq $5,0x507e8
 je Ltcp_commit
 cmpq $4,0x507e8
 je Lnat_commit_done
 cmpq $2,0x507e8
 jae Licmp_commit
 cmpq $1,0x507e8
 jne Lnat_commit_udp
 incq 0x507f0
 xorl %eax,%eax
 retq
Lnat_commit_udp:
 cmpq $1,0x5ad8
 jne Lnat_commit_done
 callq Lclock_now
 testl %edx,%edx
 jnz Lnat_clock_bad
 movq %rax,0x5ae8
 movq %rax,%r11
 movq 0x502c8,%rax
 cmpq 0x53f28,%rax
 jne Lnat_no_state
 movq %rax,0x5af0
 movq 0x50ac8,%rax
 cmpq 0x53f30,%rax
 jne Lnat_no_state
 movq %rax,0x5af8
 movq 0x53f00,%rax
 cmpq $32,%rax
 jae Lnat_no_state
 imulq $96,%rax,%rax
 leaq 0x53000(%rax),%r8
 movq $0,(%r8)
 movq 0x53f08,%rax
 movq %rax,8(%r8)
 movq 0x53f10,%rax
 movq %rax,16(%r8)
 movq %r11,24(%r8)
 movq 0x5af0,%rax
 movq %rax,32(%r8)
 movq 0x5af8,%rax
 movq %rax,40(%r8)
 movq $1,48(%r8)
 movq 0x53f38,%rax
 movq %rax,56(%r8)
 movq 0x53f40,%rax
 movq %rax,64(%r8)
 movq $1,(%r8)
 movq $1,0x5ae0
Lnat_commit_done:
 xorl %eax,%eax
 retq
Lnat_expire:
 movq $0,0x5ae0
 movl $0x53000,%r8d
 movl $32,%r9d
Lnat_expire_next:
 cmpq $1,(%r8)
 jne Lnat_expire_advance
 movq 0x502c8,%rax
 cmpq 32(%r8),%rax
 jne Lnat_expire_remove
 movq 0x50ac8,%rax
 cmpq 40(%r8),%rax
 jne Lnat_expire_remove
 cmpq $1,48(%r8)
 jne Lnat_expire_remove
 movq 0x53f18,%rax
 subq 24(%r8),%rax
 jc Lnat_expire_remove
 cmpq 0x5a68,%rax
 jae Lnat_expire_remove
 movq $1,0x5ae0
 jmp Lnat_expire_advance
Lnat_expire_remove:
 pushq %rdi
 movq %r8,%rdi
 movl $12,%ecx
 xorl %eax,%eax
 cld
 rep stosq
 popq %rdi
Lnat_expire_advance:
 addq $96,%r8
 decl %r9d
 jnz Lnat_expire_next
 retq
Lnat_revoke:
 pushq %rax
 pushq %rcx
 pushq %rdi
 movq $0,0x5ae0
 cmpq $1,0x5a28
 jne Lnat_revoke_done
 movl $0x53000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 cld
 rep stosq
 callq Lpending_revoke
 callq Lintent_revoke
Lnat_revoke_done:
 popq %rdi
 popq %rcx
 popq %rax
 retq
Lnat_full:
 movl $38,%eax
 retq
Lnat_udp_seed:
 movl %r12d,%edx
 addl $17,%edx
 leaq 26(%rdi),%rsi
 movl $4,%ecx
Lnat_seed_word:
 movzwl (%rsi),%eax
 rolw $8,%ax
 addl %eax,%edx
 addq $2,%rsi
 loop Lnat_seed_word
 retq
Lnat_sum:
 testl $1,%ecx
 jz Lnat_even
 movzbl -1(%rsi,%rcx),%eax
 shll $8,%eax
 addl %eax,%edx
Lnat_even:
 shrl $1,%ecx
 jmp Lchecksum
Lnat_no_state:
 movl $36,%eax
 retq
Lnat_bad:
 movl $32,%eax
 retq
Lnat_policy:
 movl $33,%eax
 retq
Lnat_ttl:
 movl $34,%eax
 retq
Lnat_checksum_bad:
 movl $35,%eax
 retq

Lnat_clock_bad:
 callq Lnat_revoke
 movl $37,%eax
 retq
