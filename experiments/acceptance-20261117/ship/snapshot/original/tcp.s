# Restricted TCP firewall/NAT laboratory: eight sessions, outbound443 only.
# No options, FIN, reordering/window tracking or general TCP compliance claim.
Ltcp_transform:
 cmpl $40,%r13d
 jb Lnat_bad
 callq Ltcp_options
 testl %eax,%eax
 jnz Lnat_bad
 cmpb $1,22(%rdi)
 jbe Lnat_ttl
 leal -20(%r13d),%r12d
 callq Ltcp_seed
 leaq 34(%rdi),%rsi
 movl %r12d,%ecx
 callq Lnat_sum
 testl %eax,%eax
 jnz Lnat_checksum_bad
 callq Ltcp_expire
 movl 38(%rdi),%eax
 bswapl %eax
 movq %rax,0x59090
 movl 42(%rdi),%eax
 bswapl %eax
 movq %rax,0x59098
 movl %r12d,%eax
 subl 0x590d0,%eax
 movq %rax,0x590a0
 movzbl 47(%rdi),%eax
 movq %rax,0x59088
 movzwl 34(%rdi),%eax
 rolw $8,%ax
 testl %eax,%eax
 jz Lnat_policy
 movq %rax,0x590a8
 movzwl 36(%rdi),%eax
 rolw $8,%ax
 testl %eax,%eax
 jz Lnat_policy
 movq %rax,0x590b0
 movl 26(%rdi),%eax
 movq %rax,0x590b8
 movl 30(%rdi),%eax
 movq %rax,0x590c0
 cmpl $0x32465202,(%rdi)
 jne Lnat_policy
 cmpq $0,0x5ad0
 jne Ltcp_in
 cmpw $0x0200,4(%rdi)
 jne Lnat_policy
 cmpl $0x32465202,6(%rdi)
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
 cmpq $443,0x590b0
 jne Lnat_policy
 movzbl 30(%rdi),%eax
 testl %eax,%eax
 jz Lnat_policy
 cmpl $127,%eax
 je Lnat_policy
 cmpl $224,%eax
 jae Lnat_policy
 cmpl $0xff004d0a,30(%rdi)
 je Lnat_policy
 cmpl $0xff6433c6,30(%rdi)
 je Lnat_policy
 cmpl $0x006433c6,30(%rdi)
 je Lnat_policy
 cmpl $0x02004d0a,30(%rdi)
 je Lnat_policy
 cmpl $0x026433c6,30(%rdi)
 je Lnat_policy
 movl $0x58000,%r8d
 xorl %r9d,%r9d
 movq $-1,%r10
Ltcp_find:
 cmpq $0,(%r8)
 je Ltcp_free
 movq 0x590b8,%rax
 cmpq 8(%r8),%rax
 jne Ltcp_next
 movq 0x590a8,%rax
 cmpq 16(%r8),%rax
 jne Ltcp_next
 movq 0x590c0,%rax
 cmpq 24(%r8),%rax
 je Ltcp_out_existing
 jmp Ltcp_next
Ltcp_free:
 cmpq $-1,%r10
 jne Ltcp_next
 movq %r9,%r10
Ltcp_next:
 addq $128,%r8
 incq %r9
 cmpq $8,%r9
 jb Ltcp_find
 cmpq $-1,%r10
 je Lnat_full
 cmpq $2,0x59088
 jne Lnat_no_state
 cmpq $0,0x59098
 jne Lnat_no_state
 cmpq $0,0x590a0
 jne Lnat_policy
 movq %r10,%r9
 movl $0x59000,%esi
 pushq %rdi
 movq %rsi,%rdi
 movl $16,%ecx
 xorl %eax,%eax
 rep stosq
 popq %rdi
 movq $1,0x59000
 movq 0x590b8,%rax
 movq %rax,0x59008
 movq 0x590a8,%rax
 movq %rax,0x59010
 movq 0x590c0,%rax
 movq %rax,0x59018
 movq $443,0x59020
 movl 0x59090,%eax
 incl %eax
 movq %rax,0x59028
 jmp Ltcp_out_ready
Ltcp_out_existing:
 movq %r9,0x59080
 callq Ltcp_copy
 cmpq $1,0x59000
 jne Ltcp_out_ack
 cmpq $2,0x59088
 jne Lnat_no_state
 cmpq $0,0x59098
 jne Lnat_no_state
 cmpq $0,0x590a0
 jne Lnat_policy
 movl 0x59090,%eax
 incl %eax
 cmpq 0x59028,%rax
 jne Lnat_no_state
 jmp Ltcp_out_route
Ltcp_out_ack:
 cmpq $17,0x59088
 jne Ltcp_out_normal_sequence
 testq $1,0x59058
 jz Ltcp_out_normal_sequence
 cmpq $0,0x590a0
 jne Lnat_no_state
 movl 0x59090,%eax
 incl %eax
 cmpq 0x59028,%rax
 jne Lnat_no_state
 movq 0x59098,%rax
 cmpq 0x59030,%rax
 jne Lnat_no_state
 jmp Ltcp_out_route
Ltcp_out_normal_sequence:
 movq 0x59090,%rax
 cmpq 0x59028,%rax
 jne Lnat_no_state
 movq 0x59098,%rax
 cmpq 0x59030,%rax
 jne Lnat_no_state
 cmpq $2,0x59000
 jne Ltcp_out_established
 cmpq $16,0x59088
 jne Lnat_policy
 cmpq $0,0x590a0
 jne Lnat_policy
 movq $3,0x59000
 jmp Ltcp_out_route
Ltcp_out_established:
 cmpq $3,0x59000
 je Ltcp_out_live
 cmpq $4,0x59000
 jne Lnat_no_state
Ltcp_out_live:
 callq Ltcp_est_flags
 testl %eax,%eax
 jnz Lnat_policy
 cmpq $0,0x59000
 je Ltcp_out_route
 testq $1,0x59058
 jz Ltcp_out_can_data
 cmpq $0,0x590a0
 jne Lnat_policy
Ltcp_out_can_data:
 movl 0x59028,%eax
 addl 0x590a0,%eax
 cmpq $17,0x59088
 jne Ltcp_out_advance
 testq $1,0x59058
 jnz Lnat_no_state
 orq $1,0x59058
 incl %eax
Ltcp_out_advance:
 movq %rax,0x59028
 testq $2,0x59058
 jz Ltcp_out_close_check
 orq $8,0x59058
Ltcp_out_close_check:
 callq Ltcp_close_check
 jmp Ltcp_out_route
Ltcp_out_ready:
 movq %r9,0x59080
 movq 0x502c8,%rax
 movq %rax,0x59038
 movq 0x50ac8,%rax
 movq %rax,0x59040
 movq 0x55000,%rax
 movq %rax,0x59048
Ltcp_out_route:
 callq Lroute_lookup
 testl %eax,%eax
 jnz Lnat_policy
 callq Lneighbor_get
 testl %eax,%eax
 jnz Lneighbor_probe
 movq 0x55088,%rax
 movl %eax,(%rdi)
 shrq $32,%rax
 movw %ax,4(%rdi)
 movw $0x0400,10(%rdi)
 movl $0x026433c6,26(%rdi)
 movl 0x59080,%eax
 addl $50000,%eax
 rolw $8,%ax
 movw %ax,34(%rdi)
 jmp Ltcp_rechecksum
Ltcp_in:
 cmpw $0x0400,4(%rdi)
 jne Lnat_policy
 cmpl $0x026433c6,30(%rdi)
 jne Lnat_policy
 callq Lneighbor_source
 testl %eax,%eax
 jnz Lnat_policy
 movq 0x590b0,%rax
 subq $50000,%rax
 cmpq $8,%rax
 jae Lnat_no_state
 movq %rax,0x59080
 shlq $7,%rax
 leaq 0x58000(%rax),%r8
 cmpq $0,(%r8)
 je Lnat_no_state
 movq 0x590b8,%rax
 cmpq 24(%r8),%rax
 jne Lnat_no_state
 cmpq $443,0x590a8
 jne Lnat_no_state
 callq Ltcp_copy
 movq 0x59098,%rax
 cmpq 0x59028,%rax
 jne Lnat_no_state
 cmpq $1,0x59000
 je Ltcp_synack
 cmpq $2,0x59000
 je Ltcp_synack_repeat
 cmpq $3,0x59000
 je Ltcp_in_live
 cmpq $4,0x59000
 jne Lnat_no_state
Ltcp_in_live:
 cmpq $17,0x59088
 jne Ltcp_in_normal_sequence
 testq $2,0x59058
 jz Ltcp_in_normal_sequence
 cmpq $0,0x590a0
 jne Lnat_no_state
 movl 0x59090,%eax
 incl %eax
 cmpq 0x59030,%rax
 jne Lnat_no_state
 jmp Ltcp_in_ready
Ltcp_in_normal_sequence:
 movq 0x59090,%rax
 cmpq 0x59030,%rax
 jne Lnat_no_state
 callq Ltcp_est_flags
 testl %eax,%eax
 jnz Lnat_policy
 cmpq $0,0x59000
 je Ltcp_in_ready
 testq $2,0x59058
 jz Ltcp_in_can_data
 cmpq $0,0x590a0
 jne Lnat_policy
Ltcp_in_can_data:
 movl 0x59030,%eax
 addl 0x590a0,%eax
 cmpq $17,0x59088
 jne Ltcp_in_advance
 testq $2,0x59058
 jnz Lnat_no_state
 orq $2,0x59058
 incl %eax
Ltcp_in_advance:
 movq %rax,0x59030
 testq $1,0x59058
 jz Ltcp_in_close_check
 orq $4,0x59058
Ltcp_in_close_check:
 callq Ltcp_close_check
 jmp Ltcp_in_ready
Ltcp_synack_repeat:
 movl 0x59090,%eax
 incl %eax
 cmpq 0x59030,%rax
 jne Lnat_no_state
Ltcp_synack:
 cmpq $18,0x59088
 jne Lnat_policy
 cmpq $0,0x590a0
 jne Lnat_policy
 movq $2,0x59000
 movl 0x59090,%eax
 incl %eax
 movq %rax,0x59030
Ltcp_in_ready:
 # Read immutable tuple from committed entry, even if a checked RST clears shadow.
 movl 8(%r8),%eax
 movl %eax,30(%rdi)
 movw 16(%r8),%ax
 rolw $8,%ax
 movw %ax,36(%rdi)
 movl $0x32465202,(%rdi)
 movw $0x0300,4(%rdi)
 movl $0x32465202,6(%rdi)
 movw $0x0200,10(%rdi)
Ltcp_rechecksum:
 decb 22(%rdi)
 movw $0,24(%rdi)
 leaq 14(%rdi),%rsi
 movl $20,%ecx
 xorl %edx,%edx
 callq Lnat_sum
 movw %ax,24(%rdi)
 movw $0,50(%rdi)
 callq Ltcp_seed
 leaq 34(%rdi),%rsi
 movl %r12d,%ecx
 callq Lnat_sum
 movw %ax,50(%rdi)
 movq $5,0x507e8
 xorl %eax,%eax
 retq
Ltcp_est_flags:
 cmpq $17,0x59088
 je Ltcp_flags_good
 cmpq $16,0x59088
 je Ltcp_flags_good
 cmpq $24,0x59088
 je Ltcp_flags_good
 cmpq $20,0x59088
 jne Ltcp_flags_bad
 cmpq $4,0x59000
 je Ltcp_flags_bad
 cmpq $0,0x590a0
 jne Ltcp_flags_bad
 pushq %rdi
 movl $0x59000,%edi
 movl $16,%ecx
 xorl %eax,%eax
 rep stosq
 popq %rdi
Ltcp_flags_good:
 xorl %eax,%eax
 retq
Ltcp_flags_bad:
 movl $33,%eax
 retq
Ltcp_copy:
 pushq %rdi
 movq %r8,%rsi
 movl $0x59000,%edi
 movl $16,%ecx
 rep movsq
 popq %rdi
 retq
Ltcp_commit:
 callq Lclock_now
 testl %edx,%edx
 jnz Lnat_clock_bad
 movq %rax,%r11
 movq 0x59080,%rax
 cmpq $8,%rax
 jae Lnat_no_state
 shlq $7,%rax
 leaq 0x58000(%rax),%rdi
 cmpq $0,0x59000
 je Ltcp_commit_copy
 movq 0x502c8,%rax
 cmpq 0x59038,%rax
 jne Lnat_no_state
 movq 0x50ac8,%rax
 cmpq 0x59040,%rax
 jne Lnat_no_state
 movq 0x55000,%rax
 cmpq 0x59048,%rax
 jne Lnat_no_state
 cmpq $4,0x59000
 jne Ltcp_commit_time
 cmpq $4,(%rdi)
 je Ltcp_commit_copy
Ltcp_commit_time:
 movq %r11,0x59050
Ltcp_commit_copy:
 movl $0x59000,%esi
 movl $16,%ecx
 rep movsq
 xorl %eax,%eax
 retq
Ltcp_expire:
 movl $0x58000,%r8d
 movl $8,%r9d
Ltcp_expire_next:
 cmpq $0,(%r8)
 je Ltcp_expire_advance
 movq 0x502c8,%rax
 cmpq 56(%r8),%rax
 jne Ltcp_expire_remove
 movq 0x50ac8,%rax
 cmpq 64(%r8),%rax
 jne Ltcp_expire_remove
 movq 0x55000,%rax
 cmpq 72(%r8),%rax
 jne Ltcp_expire_remove
 movq 0x53f18,%rax
 subq 80(%r8),%rax
 jc Ltcp_expire_remove
 movq 0x5a68,%rcx
 cmpq $4,(%r8)
 jne Ltcp_expire_limit
 imulq $40,%rcx,%rcx
Ltcp_expire_limit:
 cmpq %rcx,%rax
 jb Ltcp_expire_advance
Ltcp_expire_remove:
 pushq %rdi
 movq %r8,%rdi
 movl $16,%ecx
 xorl %eax,%eax
 rep stosq
 popq %rdi
Ltcp_expire_advance:
 addq $128,%r8
 decl %r9d
 jnz Ltcp_expire_next
 retq
Ltcp_seed:
 movl %r12d,%edx
 addl $6,%edx
 leaq 26(%rdi),%rsi
 movl $4,%ecx
Ltcp_seed_word:
 movzwl (%rsi),%eax
 rolw $8,%ax
 addl %eax,%edx
 addq $2,%rsi
 loop Ltcp_seed_word
 retq
Ltcp_scratch_clear:
 cmpq $1,0x5a28
 jne Ltcp_scratch_done
 pushq %rdi
 pushq %rcx
 pushq %rax
 movl $0x59000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 popq %rax
 popq %rcx
 popq %rdi
Ltcp_scratch_done:
 retq

Ltcp_close_check:
 cmpq $15,0x59058
 jne Ltcp_close_done
 movq $4,0x59000
Ltcp_close_done:
 retq
# Bounded transparent option validation; option values are not negotiated here.
Ltcp_options:
 movzbl 46(%rdi),%eax
 testb $15,%al
 jnz Ltcp_options_bad
 shrl $4,%eax
 shll $2,%eax
 cmpl $20,%eax
 jb Ltcp_options_bad
 leal 20(%eax),%ecx
 cmpl %r13d,%ecx
 ja Ltcp_options_bad
 movl %eax,0x590d0
 leaq 34(%rdi,%rax),%r9
 leaq 54(%rdi),%r8
 xorl %r11d,%r11d
Ltcp_options_next:
 cmpq %r9,%r8
 jae Ltcp_options_ok
 movzbl (%r8),%eax
 testl %eax,%eax
 jz Ltcp_options_padding
 cmpl $1,%eax
 je Ltcp_option_nop
 leaq 2(%r8),%rcx
 cmpq %r9,%rcx
 ja Ltcp_options_bad
 movzbl 1(%r8),%edx
 cmpl $2,%edx
 jb Ltcp_options_bad
 leaq (%r8,%rdx),%rcx
 cmpq %r9,%rcx
 ja Ltcp_options_bad
 cmpl $2,%eax
 je Ltcp_option_mss
 cmpl $3,%eax
 je Ltcp_option_ws
 cmpl $4,%eax
 je Ltcp_option_sackpermit
 cmpl $5,%eax
 je Ltcp_option_sack
 cmpl $8,%eax
 je Ltcp_option_time
 jmp Ltcp_option_advance
Ltcp_option_mss:
 cmpl $4,%edx
 jne Ltcp_options_bad
 cmpw $0,2(%r8)
 je Ltcp_options_bad
 jmp Ltcp_option_syn
Ltcp_option_ws:
 cmpl $3,%edx
 jne Ltcp_options_bad
 cmpb $14,2(%r8)
 ja Ltcp_options_bad
 jmp Ltcp_option_syn
Ltcp_option_sackpermit:
 cmpl $2,%edx
 jne Ltcp_options_bad
Ltcp_option_syn:
 testb $2,47(%rdi)
 jz Ltcp_options_bad
 jmp Ltcp_option_unique
Ltcp_option_sack:
 cmpl $10,%edx
 jb Ltcp_options_bad
 subl $2,%edx
 testl $7,%edx
 jnz Ltcp_options_bad
Ltcp_option_unique:
 btl %eax,%r11d
 jc Ltcp_options_bad
 btsl %eax,%r11d
 jmp Ltcp_option_advance
Ltcp_option_time:
 cmpl $10,%edx
 jne Ltcp_options_bad
 jmp Ltcp_option_unique
Ltcp_option_nop:
 incq %r8
 jmp Ltcp_options_next
Ltcp_option_advance:
 movq %rcx,%r8
 jmp Ltcp_options_next
Ltcp_options_padding:
 cmpb $0,(%r8)
 jne Ltcp_options_bad
 incq %r8
 cmpq %r9,%r8
 jb Ltcp_options_padding
Ltcp_options_ok:
 xorl %eax,%eax
 retq
Ltcp_options_bad:
 movl $32,%eax
 retq
