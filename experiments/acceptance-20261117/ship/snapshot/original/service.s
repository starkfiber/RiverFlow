# Raw interface startup and a continuous, UART-cancellable two-port NAT poller.
Lraw_open0:
 movq $0,0x5a38
 jmp Lraw_open
Lraw_open1:
 movq $1,0x5a38
Lraw_open:
 movq $4,0x5a70
 movq $1,0x5a48
 jmp Lif_command
Lservice_start:
 movq $20,0x5a98
 cmpq $0,0x5a30
 jne Lservice_check
 movq $4,0x5a70
 movq $1,0x5a48
 movq $0,0x5a38
 callq Lif_dispatch
 cmpq $0,0x5d70
 jne Lservice_close
 movq $1,0x5a38
 callq Lif_dispatch
Lservice_check:
 cmpq $3,0x5a30
 jne Lservice_close
 cmpq $1,0x50130
 jne Lservice_close
 cmpq $1,0x50930
 jne Lservice_close
 callq Lclock_now
 testl %edx,%edx
 jnz Lservice_clock_failed
 movq $0,0x507f0
 movq $1,0x5a78
 movq $0,0x5a80
 movq $0,0x5a88
 movq $0,0x5a90
 leaq Lservice_started(%rip),%rsi
 callq Lputs
Lservice_round:
 callq Lclock_now
 testl %edx,%edx
 jnz Lservice_clock_failed
 movq %rax,0x53f18
 callq Lneighbor_sweep
 callq Ltcp_expire
 callq Lintent_expire
 movw $0x3fd,%dx
 inb %dx,%al
 testb $1,%al
 jz Lservice_packets
 movw $0x3f8,%dx
 inb %dx,%al
 cmpb $'x',%al
 je Lservice_cancel
 cmpb $'s',%al
 jne Lservice_packets
 callq Lservice_report
Lservice_packets:
 movq $0,0x5a98
 movq $1,0x5ad8
 movq $0,0x5ad0
 callq Lrelay_command
 callq Lservice_result
 testl %eax,%eax
 jnz Lservice_failed
 movq $2,0x5ad8
 movq $1,0x5ad0
 callq Lrelay_command
 callq Lservice_result
 testl %eax,%eax
 jnz Lservice_failed
 cmpq $0,0x5a98
 jne Lservice_round
 hlt
 jmp Lservice_round
Lservice_result:
 movq 0x5ac0,%rax
 testl %eax,%eax
 jnz Lservice_not_forward
 movq 0x5ad0,%rdx
 incq 0x5a80(,%rdx,8)
 movq $1,0x5a98
 retq
Lservice_not_forward:
 cmpl $42,%eax
 je Lservice_idle
 cmpl $44,%eax
 je Lservice_drop
 cmpl $39,%eax
 je Lservice_drop
 cmpl $41,%eax
 je Lservice_drop
 cmpl $38,%eax
 je Lservice_drop
 cmpl $26,%eax
 je Lservice_idle
 cmpl $28,%eax
 je Lservice_drop
 cmpl $32,%eax
 jb Lservice_fatal
 cmpl $36,%eax
 ja Lservice_fatal
Lservice_drop:
 incq 0x5a90
 movq $1,0x5a98
Lservice_idle:
 xorl %eax,%eax
Lservice_fatal:
 retq
Lservice_cancel:
 movq $0,0x5a98
 jmp Lservice_close
Lservice_clock_failed:
 movl $37,%eax
Lservice_failed:
 movq %rax,0x5a98
Lservice_close:
 movq $0,0x5a78
 movq $3,0x5a48
 movq $0,0x5a38
 callq Lif_dispatch
 movq $1,0x5a38
 callq Lif_dispatch
 callq Lservice_report
 leaq Lservice_reason(%rip),%rsi
 callq Lputs
 movq 0x5a98,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 leaq Lservice_stopped(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lservice_report:
 callq Lstats_report
 leaq Lservice_out_text(%rip),%rsi
 callq Lputs
 movq 0x5a80,%rax
 callq Lhex
 leaq Lservice_in_text(%rip),%rsi
 callq Lputs
 movq 0x5a88,%rax
 callq Lhex
 leaq Lservice_drop_text(%rip),%rsi
 callq Lputs
 movq 0x5a90,%rax
 callq Lhex
 cmpq $1,0x5a28
 jne Lpressure_report_end
 leaq Lpressure0(%rip),%rsi
 callq Lputs
 movq 0x50150,%rax
 callq Lhex
 leaq Lpressure1(%rip),%rsi
 callq Lputs
 movq 0x50950,%rax
 callq Lhex
Lpressure_report_end:
 leaq Lnewline(%rip),%rsi
 callq Lputs
 retq
Lservice_started:
 .asciz "NAT service running; s status, x cancel/close.\r\n"
Lservice_stopped:
 .asciz "NAT service stopped.\r\n"
Lservice_out_text:
 .asciz "Service out=0x"
Lservice_in_text:
 .asciz " in=0x"
Lservice_drop_text:
 .asciz " drop=0x"

Lservice_reason:
 .asciz "Service stop reason=0x"

Lpressure0:
 .asciz " full0=0x"
Lpressure1:
 .asciz " full1=0x"
