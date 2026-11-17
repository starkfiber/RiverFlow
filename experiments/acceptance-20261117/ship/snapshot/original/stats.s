# Per-port observed counters; no inferred hardware/backend loss counter.
Lstats_result:
 cmpq $1,0x5a28
 jne Lstats_done
 movq 0x5ad0,%rdx
 shlq $8,%rdx
 movq 0x5ac0,%rax
 testl %eax,%eax
 jnz Lstats_not_success
 incq 0x54080(%rdx)
 retq
Lstats_not_success:
 cmpl $42,%eax
 jne Lstats_not_neighbor
 incq 0x540b8(%rdx)
 retq
Lstats_not_neighbor:
 cmpl $44,%eax
 je Lstats_capacity
 cmpl $27,%eax
 jne Lstats_not_driver
 incq 0x54048(%rdx)
 retq
Lstats_not_driver:
 cmpl $40,%eax
 je Lstats_tx_unknown
 cmpl $29,%eax
 jne Lstats_not_tx
Lstats_tx_unknown:
 incq 0x54050(%rdx)
 retq
Lstats_not_tx:
 cmpl $28,%eax
 je Lstats_malformed
 cmpl $32,%eax
 je Lstats_malformed
 cmpl $33,%eax
 je Lstats_policy
 cmpl $36,%eax
 je Lstats_policy
 cmpl $35,%eax
 je Lstats_checksum
 cmpl $34,%eax
 je Lstats_ttl
 cmpl $38,%eax
 je Lstats_capacity
 cmpl $39,%eax
 je Lstats_route
 cmpl $41,%eax
 je Lstats_rate
 retq
Lstats_malformed:
 incq 0x54018(%rdx)
 jmp Lstats_drop
Lstats_policy:
 incq 0x54020(%rdx)
 jmp Lstats_drop
Lstats_checksum:
 incq 0x54028(%rdx)
 jmp Lstats_drop
Lstats_ttl:
 incq 0x54030(%rdx)
 jmp Lstats_drop
Lstats_capacity:
 incq 0x54038(%rdx)
 jmp Lstats_drop
Lstats_route:
 incq 0x54040(%rdx)
 jmp Lstats_drop
Lstats_rate:
 incq 0x54078(%rdx)
Lstats_drop:
 incq 0x54010(%rdx)
Lstats_done:
 retq
Lstats_report:
 cmpq $1,0x5a28
 jne Lstats_done
 pushq %r15
 movl $0x54000,%r15d
Lstats_report_port:
 leaq Lstats_label(%rip),%rsi
 callq Lputs
 movq (%r15),%rax
 callq Lhex
 movb $'/',%al
 callq Lchar
 movq 16(%r15),%rax
 callq Lhex
 movb $'/',%al
 callq Lchar
 movq 80(%r15),%rax
 callq Lhex
 movb $'/',%al
 callq Lchar
 movq 88(%r15),%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 addl $256,%r15d
 cmpl $0x54200,%r15d
 jb Lstats_report_port
 popq %r15
 retq
Lstats_label:
 .asciz "Observed rx/drop/tx-unknown/full: "
