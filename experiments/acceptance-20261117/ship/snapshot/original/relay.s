# Manually requested bounded one-frame guest relay. No routing, NAT or STP.
# A reserved NX staging page separates source and destination ownership.
Lrelay0:
 movq $0,0x5ad8
 movq $0,0x5ad0
 jmp Lrelay_command
Lrelay1:
 movq $0,0x5ad8
 movq $1,0x5ad0
Lrelay_command:
 pushfq
 cli
 movq $20,0x5ac0
 movq $0,0x5ac8
 cmpq $1,0x5a28
 jne Lrelay_report
 cmpq $3,0x5a30
 jne Lrelay_report
 movq $2,0x507e0
 movq $0,0x507e8
 cmpq $1,0x5ab8
 je Lrelay_stage_ready
 cmpq $0,0x4288
 jne Lrelay_report
 movabsq $0x8000000000051003,%rax
 movq %rax,0x4288
 invlpg 0x51000
 movq $1,0x5ab8
Lrelay_stage_ready:
 movl $0x51000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 cld
 rep stosq
 movq 0x5ad0,%rax
 callq Lrelay_select
 testl %eax,%eax
 jnz Lrelay_source_save
 movq $1,0x5c28
 callq Lrelay_receive
 cmpl $27,%eax
 jne Lrelay_source_save
 movq %rax,0x5ac0
 callq Lshutdown
 movq 0x5ac0,%rax
Lrelay_source_save:
 movq %rax,0x5ac0
 callq Lrelay_save
 cmpq $0,0x5ac0
 jne Lrelay_clear
 cmpq $0,0x5ad8
 je Lrelay_plain_target
 callq Lnat_transform
 movq %rax,0x5ac0
 testl %eax,%eax
 jnz Lrelay_clear
Lrelay_plain_target:
 movq 0x507e0,%rax
 cmpq $2,%rax
 jb Lrelay_target_ready
 movq 0x5ad0,%rax
 xorq $1,%rax
Lrelay_target_ready:
 callq Lrelay_select
 testl %eax,%eax
 jnz Lrelay_dest_save
 movq $1,0x5c28
 callq Lrelay_transmit
 testl %eax,%eax
 jz Lrelay_dest_save
 movq %rax,0x5ac0
 callq Lshutdown
 movq 0x5ac0,%rax
Lrelay_dest_save:
 testl %eax,%eax
 jnz Lrelay_dest_error
 callq Lnat_commit
 jmp Lrelay_dest_record
Lrelay_dest_error:
 cmpq $0,0x5ad8
 je Lrelay_dest_record
 callq Lnat_revoke
Lrelay_dest_record:
 movq %rax,0x5ac0
 callq Lrelay_save
Lrelay_clear:
 movl $0x51000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 cld
 rep stosq
 callq Ltcp_scratch_clear
 callq Lpending_flush
Lrelay_report:
 callq Lstats_result
 popfq
 cmpq $1,0x5a78
 je Lrelay_service_return
 leaq Lrelay_text(%rip),%rsi
 callq Lputs
 movq 0x5ac0,%rax
 callq Lhex
 leaq Lrelay_length_text(%rip),%rsi
 callq Lputs
 movq 0x5ac8,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lrelay_select:
 movq %rax,0x5a38
 imulq $0x30000,%rax,%rax
 movq %rax,0x5a40
 callq Lif_load
 movq $3,0x5c20
 cmpq $1,0x5dc0
 jne Lrelay_unowned
 callq Lif_focus
 testl %eax,%eax
 jz Lrelay_selected
 movq $2,0x5dc0
Lrelay_selected:
 retq
Lrelay_unowned:
 movl $20,%eax
 retq
Lrelay_save:
 callq Lif_unfocus
 callq Lif_store
 movq 0x5a38,%rax
 cmpq $0,0x5dc0
 je Lrelay_clear_owned
 btsq %rax,0x5a30
 retq
Lrelay_clear_owned:
 btrq %rax,0x5a30
 retq
Lrelay_receive:
 movq 0x5d40,%rsi
 cmpb $15,20(%rsi)
 jne Lrelay_completion_error
 movl $0x1000000,%ecx
 cmpq $1,0x5a78
 jne Lrelay_poll_rx
 movl $1,%ecx
Lrelay_poll_rx:
 movzwl 0x32002,%eax
 subl 0x5ba0,%eax
 andl $65535,%eax
 cmpl 0x5c38,%eax
 ja Lrelay_completion_error
 testl %eax,%eax
 jnz Lrelay_have_rx
 loop Lrelay_poll_rx
 movl $26,%eax
 retq
Lrelay_have_rx:
 cmpq 0x5c38,%rax
 jne Lrelay_not_full
 incq 0x5c50
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 incq 0x54058(%rdx)
Lrelay_not_full:
 lfence
 # A descriptor cannot have two still-pending completions without CPU repost.
 movl %eax,%r10d
 xorl %r11d,%r11d
 movq 0x5ba0,%rbx
Lrelay_pending_ids:
 movq %rbx,%rax
 andq 0x5c40,%rax
 movl 0x32004(,%rax,8),%edx
 cmpl 0x5c38,%edx
 jae Lrelay_completion_error
 btsq %rdx,%r11
 jc Lrelay_completion_error
 incq %rbx
 decl %r10d
 jnz Lrelay_pending_ids
 movq 0x5ba0,%rax
 andq 0x5c40,%rax
 movl 0x32004(,%rax,8),%r8d
 cmpl 0x5c38,%r8d
 jae Lrelay_completion_error
 movl 0x32008(,%rax,8),%r9d
 movq %r8,%rdi
 shlq $11,%rdi
 addq $0x36000,%rdi
 cmpl $72,%r9d
 jb Lrelay_drop_rx
 cmpl $1526,%r9d
 ja Lrelay_drop_rx
 cmpq $0,(%rdi)
 jne Lrelay_drop_rx
 cmpw $0,8(%rdi)
 jne Lrelay_drop_rx
 cmpw $1,10(%rdi)
 ja Lrelay_drop_rx
 # Only untagged Ethernet-II; reject group/zero sources and reserved controls.
 movzwl 24(%rdi),%eax
 rolw $8,%ax
 cmpw $1536,%ax
 jb Lrelay_drop_rx
 cmpw $0x8100,%ax
 je Lrelay_drop_rx
 cmpw $0x88a8,%ax
 je Lrelay_drop_rx
 testb $1,18(%rdi)
 jnz Lrelay_drop_rx
 movq 18(%rdi),%rax
 shlq $16,%rax
 testq %rax,%rax
 jz Lrelay_drop_rx
 movq 12(%rdi),%rax
 shlq $16,%rax
 testq %rax,%rax
 jz Lrelay_drop_rx
 cmpl $0x00c28001,12(%rdi)
 jne Lrelay_copy_rx
 cmpb $0,16(%rdi)
 jne Lrelay_copy_rx
 cmpb $16,17(%rdi)
 jb Lrelay_drop_rx
Lrelay_copy_rx:
 subl $12,%r9d
 movq %r9,0x5ac8
 leaq 12(%rdi),%rsi
 movl $0x51040,%edi
 movl %r9d,%ecx
 cld
 rep movsb
 xorl %r9d,%r9d
 jmp Lrelay_repost_rx
Lrelay_drop_rx:
 movl $28,%r9d
Lrelay_repost_rx:
 movq %r8,%rdi
 shlq $11,%rdi
 addq $0x36000,%rdi
 movl $256,%ecx
 xorl %eax,%eax
 cld
 rep stosq
 movq 0x5ba8,%rax
 movq %rax,%rdx
 andq 0x5c40,%rdx
 movw %r8w,0x31004(,%rdx,2)
 incq %rax
 mfence
 movw %ax,0x31002
 movq %rax,0x5ba8
 incq 0x5ba0
 incq 0x5dd0
 mfence
 movq 0x5be0,%rdi
 movw $0,(%rdi)
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 incq 0x54000(%rdx)
 movl %r9d,%eax
 retq
Lrelay_transmit:
 movq 0x5d40,%rsi
 cmpb $15,20(%rsi)
 jne Lrelay_completion_error
 movq 0x5bc0,%rax
 cmpq 0x5bb8,%rax
 jne Lrelay_completion_error
 movq %rax,%r8
 andq 0x5c40,%r8
 movq %r8,%rdi
 shlq $11,%rdi
 addq $0x3e000,%rdi
 movq $0,(%rdi)
 movl $0,8(%rdi)
 addq $12,%rdi
 movl $0x51040,%esi
 movq 0x5ac8,%rcx
 cld
 rep movsb
 movq %r8,%rdi
 shlq $4,%rdi
 movq 0x5ac8,%rax
 addl $12,%eax
 movl %eax,0x33008(%rdi)
 callq Ltx_enqueue
 testl %eax,%eax
 jnz Lrelay_completion_error
 mfence
 movq 0x5be8,%rdi
 movw $1,(%rdi)
 movl $0x1000000,%ecx
Lrelay_poll_tx:
 movzwl 0x35002,%eax
 subl 0x5bb8,%eax
 andl $65535,%eax
 cmpl $1,%eax
 ja Lrelay_completion_error
 cmpl $1,%eax
 je Lrelay_tx_done
 loop Lrelay_poll_tx
 movl $40,%eax
 retq
Lrelay_tx_done:
 lfence
 movq 0x5bb8,%rax
 andq 0x5c40,%rax
 cmpl %r8d,0x35004(,%rax,8)
 jne Lrelay_completion_error
 incq 0x5bb8
 incq 0x5dd8
 movq 0x5a38,%rdx
 shlq $8,%rdx
 incq 0x54008(%rdx)
 xorl %eax,%eax
 retq
Lrelay_completion_error:
 movl $27,%eax
 retq
Lrelay_text:
 .asciz "Relay result=0x"
Lrelay_length_text:
 .asciz " bytes=0x"

Lrelay_service_return:
 retq
