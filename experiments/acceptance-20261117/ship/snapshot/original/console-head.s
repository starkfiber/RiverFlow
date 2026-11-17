.text
.globl _rf2ship_console
_rf2ship_console:
 movl $0x8000,%esp
 movq $0,0x5a00
 movq $0,0x5a18
 movq $0,0x5a20
 leaq Ltimer_irq(%rip),%rax
 movw %ax,0x5200
 movw $0x18,0x5202
 movw $0x8e02,0x5204
 shrq $16,%rax
 movw %ax,0x5206
 movl $0,0x5208
 movl $0,0x520c
 movq $0x18003,%rax
 movq %rax,0x40c0
 invlpg 0x18000
 movq $0x19000,0x582c
 movq $0,0x40b8
 invlpg 0x17000
 movw $527,0x5400
 lidt 0x5400
 movb $0x11,%al
 outb %al,$0x20
 outb %al,$0xa0
 movb $0x20,%al
 outb %al,$0x21
 movb $0x28,%al
 outb %al,$0xa1
 movb $4,%al
 outb %al,$0x21
 movb $2,%al
 outb %al,$0xa1
 movb $1,%al
 outb %al,$0x21
 outb %al,$0xa1
 movb $0xfe,%al
 outb %al,$0x21
 movb $0xff,%al
 outb %al,$0xa1
 movb $0x34,%al
 outb %al,$0x43
 movb $0x9c,%al
 outb %al,$0x40
 movb $0x2e,%al
 outb %al,$0x40
 sti
 leaq Lbanner(%rip),%rsi
 callq Lputs
Lprompt:
 leaq Lprompt_text(%rip),%rsi
 callq Lputs
Lread:
 movw $0x3fd,%dx
 inb %dx,%al
 testb $1,%al
 jnz Lreceive
 hlt
 jmp Lread
Lreceive:
 movw $0x3f8,%dx
 inb %dx,%al
 cmpq $1,0x5a28
 jne Lreceive_normal
 cmpq $1,0x55090
 jne Lreceive_normal
 cmpb $10,%al
 jne Lread
 movq $0,0x55090
 jmp Lread
Lreceive_normal:
 cmpb $'B',%al
 je Lsecure_provision
 cmpb $'U',%al
 je Lsecure_erase
 cmpb $'I',%al
 je Ldebug_refused
 cmpb $'J',%al
 je Ldebug_refused
 cmpb $'R',%al
 je Lroute_config
 cmpb $'o',%al
 je Lraw_open0
 cmpb $'i',%al
 je Lraw_open1
 cmpb $'j',%al
 je Lclock_report
 cmpb $'z',%al
 je Lservice_start
 cmpb $'r',%al
 je Lnat_out
 cmpb $'w',%al
 je Lnat_in
 cmpb $'f',%al
 je Ldebug_refused
 cmpb $'g',%al
 je Ldebug_refused
 cmpb $'a',%al
 je Ldebug_refused
 cmpb $'b',%al
 je Ldebug_refused
 cmpb $'t',%al
 je Ldebug_refused
 cmpb $'u',%al
 je Ldebug_refused
 cmpb $'c',%al
 je Lif_close0
 cmpb $'e',%al
 je Lif_close1
 cmpb $'x',%al
 je Lif_close_all
 cmpb $'h',%al
 je Lhelp
 cmpb $'s',%al
 je Lstatus
 cmpb $'p',%al
 je Ldebug_refused
 cmpb $'q',%al
 je Lquit
 cmpb $'n',%al
 je Lnet_readonly
 cmpb $'v',%al
 je Ldebug_refused
 cmpb $'d',%al
 je Ldebug_refused
 cmpb $13,%al
 je Lread
 cmpb $10,%al
 je Lread
 leaq Lunknown(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lhelp:
 leaq Lhelp_text(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lstatus:
 callq Lstats_report
 leaq Lstatus_text(%rip),%rsi
 callq Lputs
 movq 0x5a18,%rax
 callq Lhex
 leaq Lticks_text(%rip),%rsi
 callq Lputs
 movq 0x5a20,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lnet_readonly:
 movq $0,0x5c20
 callq Lnet
 jmp Lprompt
Lnet_negotiate:
 cmpq $0,0x5a28
 jne Lif_legacy_refused
 movq $1,0x5c20
 callq Lnet
 jmp Lprompt
Lnet_dma:
 cmpq $0,0x5a28
 jne Lif_legacy_refused
 movq $2,0x5c20
 callq Lnet
 jmp Lprompt
Lnet:
 movq $0,0x5c00
 leaq Lnet_header(%rip),%rsi
 callq Lputs
 xorq %r10,%r10
 xorq %r12,%r12
Lnet_bus:
 xorq %r13,%r13
Lnet_device:
 xorq %r14,%r14
 movq $1,%r15
Lnet_function:
 xorl %edi,%edi
 callq Lpci_read
 movl %eax,%r11d
 cmpw $0xffff,%ax
 je Lnet_next
 testw %ax,%ax
 jz Lnet_next
 testq %r14,%r14
 jnz Lnet_identify
 movl $12,%edi
 callq Lpci_read
 testl $0x00800000,%eax
 jz Lnet_identify
 movq $8,%r15
Lnet_identify:
 movl %r11d,%eax
 cmpw $0x1af4,%ax
 jne Lnet_next
 shrl $16,%eax
 cmpw $0x1000,%ax
 je Lnet_found
 cmpw $0x1041,%ax
 jne Lnet_next
Lnet_found:
 incq %r10
 leaq Lnet_bdf(%rip),%rsi
 callq Lputs
 movq %r12,%rax
 shlq $8,%rax
 orq %r13,%rax
 shlq $8,%rax
 orq %r14,%rax
 callq Lhex
 leaq Lnet_id(%rip),%rsi
 callq Lputs
 movl %r11d,%eax
 callq Lhex
 leaq Lnet_command(%rip),%rsi
 callq Lputs
 movl $4,%edi
 callq Lpci_read
 andl $65535,%eax
 callq Lhex
 leaq Lnet_bar(%rip),%rsi
 callq Lputs
 movl $16,%edi
 callq Lpci_read
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 callq Lcaps
 cmpq $0,0x5b20
 jne Lnet_next
 incq 0x5c00
 cmpq $3,0x5c20
 jb Lnet_bind_selected
 movq 0x5c00,%rax
 decq %rax
 cmpq 0x5a38,%rax
 jne Lnet_next
Lnet_bind_selected:
 movq %r12,0x5c08
 movq %r13,0x5c10
 movq %r14,0x5c18
Lnet_next:
 incq %r14
 cmpq %r15,%r14
 jb Lnet_function
 incq %r13
 cmpq $32,%r13
 jb Lnet_device
 incq %r12
 cmpq $8,%r12
 jb Lnet_bus
 leaq Lnet_count(%rip),%rsi
 callq Lputs
 movq %r10,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 cmpq $0,0x5c20
 je Lnet_return
 callq Ldevice_init
Lnet_return:
 retq
Lpci_read:
 movl %r12d,%eax
 shll $16,%eax
 movl %r13d,%ecx
 shll $11,%ecx
 orl %ecx,%eax
 movl %r14d,%ecx
 shll $8,%ecx
 orl %ecx,%eax
 orl %edi,%eax
 orl $0x80000000,%eax
 movw $0xcf8,%dx
 outl %eax,%dx
 movw $0xcfc,%dx
 inl %dx,%eax
 retq
Lfault:
 leaq Lfault_text(%rip),%rsi
 callq Lputs
 leaq Lfault_pc(%rip),%rax
 movq %rax,0x5a08
 leaq Lresume(%rip),%rax
 movq %rax,0x5a10
 movq $1,0x5a00
 movq $0x1111,%rax
 movq $0x2222,%rbx
 movq $0x3333,%rcx
 movq $0x4444,%rdx
 movq $0x5555,%rsi
 movq $0x6666,%rdi
 movq $0x7777,%rbp
 movq $0x8888,%r8
 movq $0x9999,%r9
 movq $0xaaaa,%r10
 movq $0xbbbb,%r11
 movq $0xcccc,%r12
 movq $0xdddd,%r13
 movq $0xeeee,%r14
 movq $0xffff,%r15
 stc
Lfault_pc:
 movq 0x10000,%rax
Lresume:
 jnc Lbad_register
 cmpq $0x1111,%rax
 jne Lbad_register
 cmpq $0x2222,%rbx
 jne Lbad_register
 cmpq $0x3333,%rcx
 jne Lbad_register
 cmpq $0x4444,%rdx
 jne Lbad_register
 cmpq $0x5555,%rsi
 jne Lbad_register
 cmpq $0x6666,%rdi
 jne Lbad_register
 cmpq $0x7777,%rbp
 jne Lbad_register
 cmpq $0x8888,%r8
 jne Lbad_register
 cmpq $0x9999,%r9
 jne Lbad_register
 cmpq $0xaaaa,%r10
 jne Lbad_register
 cmpq $0xbbbb,%r11
 jne Lbad_register
 cmpq $0xcccc,%r12
 jne Lbad_register
 cmpq $0xdddd,%r13
 jne Lbad_register
 cmpq $0xeeee,%r14
 jne Lbad_register
 cmpq $0xffff,%r15
 jne Lbad_register
 cmpq $0x8000,%rsp
 jne Lbad_register
 leaq Lrecovered(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lbad_register:
 leaq Lregister_text(%rip),%rsi
 callq Lputs
 jmp Lfatal_exit
Lquit:
 leaq Lquit_text(%rip),%rsi
 callq Lputs
 movw $0xf4,%dx
 movb $32,%al
 outb %al,%dx
Lhalt:
 cli
 hlt
 jmp Lhalt
Lputs:
 lodsb
 testb %al,%al
 jz Ldone
 callq Lchar
 jmp Lputs
Ldone:
 retq
Lchar:
 movb %al,%bl
 movl $65535,%ecx
 movw $0x3fd,%dx
Lwait:
 inb %dx,%al
 testb $32,%al
 jnz Lready
 loop Lwait
 jmp Lhalt
Lready:
 movw $0x3f8,%dx
 movb %bl,%al
 outb %al,%dx
 retq
Lhex:
 movq %rax,%r8
 movq $16,%r9
Lhex_loop:
 rolq $4,%r8
 movb %r8b,%al
 andb $15,%al
 cmpb $10,%al
 jb Ldigit
 addb $87,%al
 jmp Lemit_digit
Ldigit:
 addb $48,%al
Lemit_digit:
 callq Lchar
 decq %r9
 jnz Lhex_loop
 retq
Lrf2ship_pf:
 pushq %rax
 pushq %rbx
 pushq %rcx
 pushq %rdx
 pushq %rsi
 pushq %rdi
 pushq %rbp
 pushq %r8
 pushq %r9
 pushq %r10
 pushq %r11
 pushq %r12
 pushq %r13
 pushq %r14
 pushq %r15
 leaq 120(%rsp),%rax
 cmpq $0x12000,%rax
 jb Lfatal_pf
 cmpq $0x13000,%rax
 jae Lfatal_pf
 cmpq $1,0x5a00
 jne Lfatal_pf
 movq %cr2,%rax
 cmpq $0x10000,%rax
 jne Lfatal_pf
 cmpq $0,120(%rsp)
 jne Lfatal_pf
 movq 0x5a08,%rax
 cmpq %rax,128(%rsp)
 jne Lfatal_pf
 cmpq $0x18,136(%rsp)
 jne Lfatal_pf
 testq $512,144(%rsp)
 jz Lfatal_pf
 cmpq $0x8000,152(%rsp)
 jne Lfatal_pf
 cmpq $0x10,160(%rsp)
 jne Lfatal_pf
 movq 0x5a10,%rax
 subq 0x5a08,%rax
 cmpq $8,%rax
 jne Lfatal_pf
 cmpq $1000000,0x5a18
 jae Lfatal_pf
 movq $0,0x5a00
 incq 0x5a18
 movq 0x5a10,%rax
 movq %rax,128(%rsp)
 popq %r15
 popq %r14
 popq %r13
 popq %r12
 popq %r11
 popq %r10
 popq %r9
 popq %r8
 popq %rbp
 popq %rdi
 popq %rsi
 popq %rdx
 popq %rcx
 popq %rbx
 popq %rax
 addq $8,%rsp
 iretq
Lfatal_pf:
 leaq Lfatal_text(%rip),%rsi
 callq Lputs
Lfatal_exit:
 movw $0xf4,%dx
 movb $34,%al
 outb %al,%dx
 jmp Lhalt
Ltimer_irq:
 pushq %rax
 pushq %rdx
 leaq 16(%rsp),%rax
 cmpq $0x18000,%rax
 jb Lfatal_irq
 cmpq $0x19000,%rax
 jae Lfatal_irq
 cmpq $0x18,24(%rsp)
 jne Lfatal_irq
 testq $512,32(%rsp)
 jz Lfatal_irq
 incq 0x5a20
 movw $0x20,%dx
 movb $0x20,%al
 outb %al,%dx
 popq %rdx
 popq %rax
 iretq
Lfatal_irq:
 leaq Lirq_fatal_text(%rip),%rsi
 callq Lputs
 jmp Lfatal_exit
Lbanner:
 .asciz "\r\nRF2Ship 0.18-dev | isolated UDP NAT lab\r\n"
Lprompt_text:
 .asciz "RF2Ship> "
Lhelp_text:
 .asciz "h for help | o/i open z NAT x stop r/w step | p validated fault recovery q halt\r\n"
Lstatus_text:
 .asciz "\r\nRecovered page faults: 0x"
Lfault_text:
 .asciz "\r\nTesting guarded read; validating frame before IRETQ.\r\n"
Lrecovered:
 .asciz "\r\nRECOVERED: registers, carry flag and stack preserved.\r\n"
Lfatal_text:
 .asciz "\r\nFATAL: unexpected page-fault frame; recovery refused.\r\n"
Lregister_text:
 .asciz "\r\nFATAL: recovered register/stack mismatch.\r\n"
Lticks_text:
 .asciz " | Timer ticks: 0x"
Lnewline:
 .asciz "\r\n"
Lquit_text:
 .asciz "\r\nRF2Ship halted.\r\n"
Lunknown:
 .asciz "\r\nUnknown command. Press h for help.\r\n"

Lirq_fatal_text:
 .asciz "\r\nFATAL: unexpected timer interrupt frame.\r\n"

Lnet_header:
 .asciz "\r\nRF2Net PCI inventory: buses0..7, read only.\r\n"
Lnet_bdf:
 .asciz "BDF=0x"
Lnet_id:
 .asciz " id=0x"
Lnet_command:
 .asciz " cmd=0x"
Lnet_bar:
 .asciz " bar0=0x"
Lnet_count:
 .asciz "Supported virtio net devices: 0x"

# Read-only modern virtio capability admission. CF8 selector writes only.
# BDF in r12/r13/r14; preserve enumeration state. No MMIO or DMA effects.
Lcaps:
 pushq %r10
 pushq %r11
 pushq %r15
 xorl %r11d,%r11d
 xorq %r15,%r15
 movq $0,0x5b08
 movl $4,%edi
 callq Lpci_read
 testl $0x00100000,%eax
 jz Lcap_no_list
 movl $0x34,%edi
 callq Lpci_read
 movzbl %al,%r10d
Lcap_walk:
 testl %r10d,%r10d
 jz Lcap_finish
 cmpl $0x40,%r10d
 jb Lcap_bad_pointer
 cmpl $0xfc,%r10d
 ja Lcap_bad_pointer
 testl $3,%r10d
 jnz Lcap_bad_pointer
 movl %r10d,%edi
 shrl $2,%edi
 btsq %rdi,%r15
 jc Lcap_cycle
 incq 0x5b08
 cmpq $48,0x5b08
 ja Lcap_cycle
 movl %r10d,%edi
 callq Lpci_read
 movl %eax,%ebp
 movl %eax,%ecx
 shrl $8,%ecx
 andl $255,%ecx
 movl %ecx,0x5b00
 cmpb $9,%al
 jne Lcap_next
 movl %ebp,%ecx
 shrl $16,%ecx
 andl $255,%ecx
 cmpl $16,%ecx
 jb Lcap_bad_header
 addl %r10d,%ecx
 cmpl $256,%ecx
 ja Lcap_bad_header
 movl %ebp,%ebx
 shrl $24,%ebx
 cmpl $1,%ebx
 jb Lcap_next
 cmpl $4,%ebx
 ja Lcap_next
 cmpl $2,%ebx
 jne Lcap_header_ok
 movl %ebp,%ecx
 shrl $16,%ecx
 andl $255,%ecx
 cmpl $20,%ecx
 jb Lcap_bad_header
Lcap_header_ok:
 btsq %rbx,%r11
 jc Lcap_duplicate
 leal 4(%r10d),%edi
 callq Lpci_read
 movzbl %al,%esi
 cmpl $5,%esi
 ja Lcap_bad_bar
 movl %esi,0x5b10
 # A 64-bit BAR consumes the next slot; reject capabilities naming its high half.
 xorl %edi,%edi
Lcap_bar_walk:
 cmpl 0x5b10,%edi
 je Lcap_bar_selected
 ja Lcap_bad_bar
 movl %edi,0x5b28
 leal 16(,%rdi,4),%edi
 callq Lpci_read
 movl 0x5b28,%edi
 testl $1,%eax
 jnz Lcap_bar_advance
 andl $6,%eax
 cmpl $4,%eax
 jne Lcap_bar_advance
 incl %edi
Lcap_bar_advance:
 incl %edi
 jmp Lcap_bar_walk
Lcap_bar_selected:
 leal 16(,%rdi,4),%edi
 callq Lpci_read
 testl $1,%eax
 jnz Lcap_bad_bar
 movl %eax,%ecx
 andl $6,%ecx
 cmpl $0,%ecx
 je Lcap_bar32
 cmpl $4,%ecx
 jne Lcap_bad_bar
 cmpl $5,0x5b10
 je Lcap_bad_bar
 andl $0xfffffff0,%eax
 movl %eax,0x5b14
 addl $4,%edi
 callq Lpci_read
 orl 0x5b14,%eax
 jz Lcap_bad_bar
 jmp Lcap_span
Lcap_bar32:
 andl $0xfffffff0,%eax
 jz Lcap_bad_bar
Lcap_span:
 leal 8(%r10d),%edi
 callq Lpci_read
 movl %eax,0x5b18
 cmpl $1,%ebx
 jne Lcap_offset_notify
 testl $3,%eax
 jnz Lcap_bad_span
Lcap_offset_notify:
 cmpl $2,%ebx
 jne Lcap_offset_ok
 testl $1,%eax
 jnz Lcap_bad_span
Lcap_offset_ok:
 leal 12(%r10d),%edi
 callq Lpci_read
 testl %eax,%eax
 jz Lcap_bad_span
 cmpl $1,%ebx
 jne Lcap_not_common
 cmpl $56,%eax
 jb Lcap_bad_span
Lcap_not_common:
 cmpl $2,%ebx
 jne Lcap_not_notify
 cmpl $2,%eax
 jb Lcap_bad_span
Lcap_not_notify:
 cmpl $4,%ebx
 jne Lcap_span_end
 cmpl $6,%eax
 jb Lcap_bad_span
Lcap_span_end:
 addl 0x5b18,%eax
 jc Lcap_bad_span
 # Record required capability pointers only for this validation pass.
 movl %ebx,%edx
 shll $3,%edx
 movq %r10,0x5600(%rdx)
Lcap_next:
 movl 0x5b00,%r10d
 jmp Lcap_walk
Lcap_finish:
 cmpl $30,%r11d
 jne Lcap_missing
 xorl %eax,%eax
 jmp Lcap_return
Lcap_no_list:
 movl $1,%eax
 jmp Lcap_return
Lcap_bad_pointer:
 movl $2,%eax
 jmp Lcap_return
Lcap_cycle:
 movl $3,%eax
 jmp Lcap_return
Lcap_bad_header:
 movl $4,%eax
 jmp Lcap_return
Lcap_bad_bar:
 movl $5,%eax
 jmp Lcap_return
Lcap_bad_span:
 movl $6,%eax
 jmp Lcap_return
Lcap_missing:
 movl $7,%eax
 jmp Lcap_return
Lcap_duplicate:
 movl $8,%eax
Lcap_return:
 movq %rax,0x5b20
 popq %r15
 popq %r11
 popq %r10
 cmpq $3,0x5c20
 jae Lcap_quiet_return
 leaq Lcap_result(%rip),%rsi
 callq Lputs
 movq 0x5b20,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 retq
Lcap_quiet_return:
 retq
Lcap_result:
 .asciz "Virtio capability admission: 0x"



# One isolated modern-memory NIC. Explicit d adds bounded DMA; v stays negotiation-only.
# Expected mapped-result paths revoke our temporary mapping; unexpected faults halt.
Ldevice_init:
 movq $0,0x5d70
 movq $0,0x5d78
 movq $0,0x5d80
 movq $0,0x5dd0
 movq $0,0x5dd8
 cmpq $0,0x5dc0
 jne Ldev_owned_busy
 cmpq $3,0x5c20
 jb Ldev_legacy_count
 cmpq $2,0x5c00
 ja Ldev_no_unique
 movq 0x5a38,%rax
 cmpq 0x5c00,%rax
 jae Ldev_no_unique
 jmp Ldev_count_ok
Ldev_legacy_count:
 cmpq $1,0x5c00
 jne Ldev_no_unique
Ldev_count_ok:
 movq 0x5c08,%r12
 movq 0x5c10,%r13
 movq 0x5c18,%r14
 cmpq $3,0x5c20
 jb Ldev_pin_ok
 callq Lif_pincheck
 testl %eax,%eax
 jnz Ldev_pin_refused
Ldev_pin_ok:
 xorl %edi,%edi
 callq Lpci_read
 movl %eax,0x5d90
 callq Lcaps
 cmpq $0,0x5b20
 jne Ldev_unstable
 # Disable asynchronous timer delivery only during bounded configuration/MMIO work.
 pushfq
 cli
 movl $4,%edi
 callq Lpci_read
 andl $65535,%eax
 movl %eax,0x5d00
 testl $4,%eax
 jnz Ldev_busy_locked
 testl $2,%eax
 jz Ldev_busy_locked
 movl $1,%r10d
Lregion_loop:
 movl %r10d,%eax
 shll $6,%eax
 addl $0x5e00,%eax
 movq %rax,0x5d20
 movq 0x5600(,%r10,8),%r11
 leal 4(%r11d),%edi
 callq Lpci_read
 andl $255,%eax
 movq 0x5d20,%rdx
 movq %rax,0(%rdx)
 leal 16(,%rax,4),%edi
 movl %edi,0x5d10
 callq Lpci_read
 movl %eax,0x5d08
 movl %eax,%ecx
 andl $6,%ecx
 movl %ecx,0x5d14
 andl $0xfffffff0,%eax
 movq 0x5d20,%rdx
 movq %rax,8(%rdx)
 cmpl $4,0x5d14
 jne Lregion_low_bar
 movl 0x5d10,%edi
 addl $4,%edi
 callq Lpci_read
 testl %eax,%eax
 jnz Ldev_high_bar
Lregion_low_bar:
 leal 8(%r11d),%edi
 callq Lpci_read
 movq 0x5d20,%rdx
 movq %rax,16(%rdx)
 leal 12(%r11d),%edi
 callq Lpci_read
 movq 0x5d20,%rdx
 movq %rax,24(%rdx)
 movl $0,0x5d28
 # BAR sizing with decode and bus mastering disabled; restore before validation.
 movl 0x5d00,%eax
 andl $0xfffc,%eax
 movl $4,%edi
 callq Lcfg_write16
 callq Lpci_read
 testl $7,%eax
 jz Lregion_decode_disabled
 movl $1,0x5d28
 jmp Lregion_restore_command
Lregion_decode_disabled:
 movl 0x5d10,%edi
 movl $0xffffffff,%eax
 callq Lcfg_write32
 cmpl $4,0x5d14
 jne Lregion_read_mask
 addl $4,%edi
 movl $0xffffffff,%eax
 callq Lcfg_write32
 callq Lpci_read
 movl %eax,0x5d0c
Lregion_read_mask:
 movl 0x5d10,%edi
 callq Lpci_read
 movl %eax,0x5d18
 cmpl $4,0x5d14
 jne Lregion_restore_low
 addl $4,%edi
 xorl %eax,%eax
 callq Lcfg_write32
Lregion_restore_low:
 movl 0x5d10,%edi
 movl 0x5d08,%eax
 callq Lcfg_write32
Lregion_restore_command:
 movl $4,%edi
 movl 0x5d00,%eax
 callq Lcfg_write16
 callq Lpci_read
 andl $65535,%eax
 cmpl 0x5d00,%eax
 jne Ldev_restore_failed
 cmpl $0,0x5d28
 jne Ldev_busy_locked
 movl 0x5d10,%edi
 callq Lpci_read
 cmpl 0x5d08,%eax
 jne Ldev_restore_failed
 cmpl $4,0x5d14
 jne Lregion_size
 addl $4,%edi
 callq Lpci_read
 testl %eax,%eax
 jnz Ldev_restore_failed
 cmpl $0xffffffff,0x5d0c
 jne Ldev_bad_aperture
Lregion_size:
 cmpl $0,0x5d28
 jne Ldev_busy_locked
 movl 0x5d18,%eax
 andl $0xfffffff0,%eax
 negl %eax
 testl %eax,%eax
 jz Ldev_bad_aperture
 movl %eax,%ecx
 decl %ecx
 testl %eax,%ecx
 jnz Ldev_bad_aperture
 movq 0x5d20,%rdx
 movq %rax,32(%rdx)
 movq 8(%rdx),%r8
 movl $0xf0000000,%ecx
 cmpq %rcx,%r8
 jb Ldev_bad_aperture
 movq 32(%rdx),%rcx
 decq %rcx
 testq %rcx,%r8
 jnz Ldev_bad_aperture
 addq %rax,%r8
 movabsq $0x100000000,%r9
 cmpq %r9,%r8
 ja Ldev_bad_aperture
 cmpq %rax,24(%rdx)
 ja Ldev_bad_aperture
 subq 24(%rdx),%rax
 cmpq %rax,16(%rdx)
 ja Ldev_bad_aperture
 movq 8(%rdx),%rax
 addq 16(%rdx),%rax
 movq %rax,40(%rdx)
 # Reject overlap with every previously collected full region, even across BARs.
 movl $1,%r8d
Lregion_overlap:
 cmpq %r10,%r8
 jae Lregion_stable
 movq %r8,%rsi
 shlq $6,%rsi
 addq $0x5e00,%rsi
 movq 40(%rsi),%rax
 movq 40(%rdx),%rcx
 addq 24(%rdx),%rcx
 cmpq %rcx,%rax
 jae Lregion_overlap_next
 addq 24(%rsi),%rax
 cmpq %rax,40(%rdx)
 jb Ldev_overlap
Lregion_overlap_next:
 incq %r8
 jmp Lregion_overlap
Lregion_stable:
 # Compare capability/BAR metadata again after the sizing/restore transaction.
 leal 4(%r11d),%edi
 callq Lpci_read
 andl $255,%eax
 movq 0x5d20,%rdx
 cmpq 0(%rdx),%rax
 jne Ldev_unstable_locked
 leal 8(%r11d),%edi
 callq Lpci_read
 movq 0x5d20,%rdx
 cmpq 16(%rdx),%rax
 jne Ldev_unstable_locked
 leal 12(%r11d),%edi
 callq Lpci_read
 movq 0x5d20,%rdx
 cmpq 24(%rdx),%rax
 jne Ldev_unstable_locked
 incq %r10
 cmpq $5,%r10
 jb Lregion_loop
 xorl %edi,%edi
 callq Lpci_read
 cmpl 0x5d90,%eax
 jne Ldev_unstable_locked
 # A single uncached, supervisor-only, non-executable 4KiB mapping.
 movq 0x5e68,%rax
 movq %rax,%r8
 andq $4095,%r8
 cmpq $4040,%r8
 ja Ldev_bad_aperture
 cmpq $0,0x4100
 jne Ldev_mapping_busy
 # PCD/PWT select PAT entry3 when PAT is present; require that entry to be UC.
 movl $1,%eax
 cpuid
 testl $0x10000,%edx
 jz Lcache_ok
 movl $0x277,%ecx
 rdmsr
 shrl $24,%eax
 testb %al,%al
 jnz Ldev_cache_refused
Lcache_ok:
 movl $0x80000001,%eax
 cpuid
 testl $0x00100000,%edx
 jz Ldev_no_nx
 movl $0xc0000080,%ecx
 rdmsr
 movl %eax,0x5d30
 movl %edx,0x5d34
 orl $0x800,%eax
 wrmsr
 movq 0x5e68,%rax
 andq $-4096,%rax
 orq $0x1b,%rax
 btsq $63,%rax
 movq %rax,0x4100
 invlpg 0x20000
 movq 0x5e68,%rax
 andq $4095,%rax
 addq $0x20000,%rax
 movq %rax,0x5d40
 movq $1,0x5d80
 callq Lvirtio_negotiate
 testl %eax,%eax
 jnz Ldev_operation_done
 cmpq $2,0x5c20
 jb Ldev_operation_done
 callq Ldma_run
Ldev_operation_done:
 movq %rax,0x5d70
 testl %eax,%eax
 jnz Ldev_reset_after_operation
 cmpq $3,0x5c20
 jae Ldev_unlock
Ldev_reset_after_operation:
 callq Lshutdown
 jmp Ldev_unlock
Ldev_pin_refused:
 movq $31,0x5d70
 jmp Ldev_report
Ldev_owned_busy:
 movq $20,0x5d70
 jmp Ldev_report
Ldev_no_unique:
 movq $1,0x5d70
 jmp Ldev_report
Ldev_unstable:
 movq $2,0x5d70
 jmp Ldev_report
Ldev_busy_locked:
 movq $3,0x5d70
 jmp Ldev_unlock
Ldev_high_bar:
 movq $4,0x5d70
 jmp Ldev_unlock
Ldev_restore_failed:
 movq $5,0x5d70
 jmp Ldev_unlock
Ldev_bad_aperture:
 movq $6,0x5d70
 jmp Ldev_unlock
Ldev_overlap:
 movq $7,0x5d70
 jmp Ldev_unlock
Ldev_unstable_locked:
 movq $2,0x5d70
 jmp Ldev_unlock
Ldev_mapping_busy:
 movq $8,0x5d70
 jmp Ldev_unlock
Ldev_no_nx:
 movq $9,0x5d70
 jmp Ldev_unlock
Ldev_cache_refused:
 movq $14,0x5d70
Ldev_unlock:
 popfq
Ldev_report:
 cmpq $3,0x5c20
 jae Ldev_quiet_return
 leaq Ldev_result(%rip),%rsi
 callq Lputs
 movq 0x5d70,%rax
 callq Lhex
 leaq Ldev_cleanup(%rip),%rsi
 callq Lputs
 movq 0x5d78,%rax
 callq Lhex
 leaq Ldev_mapping(%rip),%rsi
 callq Lputs
 movq 0x4100,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 cmpq $2,0x5c20
 jne Ldev_report_done
 callq Ldma_report
Ldev_report_done:
Ldev_quiet_return:
 retq
Lcfg_write32:
 pushq %rax
 callq Lcfg_address
 popq %rax
 outl %eax,%dx
 retq
Lcfg_write16:
 pushq %rax
 callq Lcfg_address
 popq %rax
 outw %ax,%dx
 retq
Lcfg_address:
 movl %r12d,%eax
 shll $16,%eax
 movl %r13d,%ecx
 shll $11,%ecx
 orl %ecx,%eax
 movl %r14d,%ecx
 shll $8,%ecx
 orl %ecx,%eax
 orl %edi,%eax
 orl $0x80000000,%eax
 movw $0xcf8,%dx
 outl %eax,%dx
 movw $0xcfc,%dx
 retq
Lvirtio_reset:
 movq 0x5d40,%rsi
 movb $0,20(%rsi)
 movl $65536,%ecx
Lreset_poll:
 cmpb $0,20(%rsi)
 je Lreset_ok
 loop Lreset_poll
 movl $10,%eax
 retq
Lreset_ok:
 xorl %eax,%eax
 retq
Lvirtio_negotiate:
 callq Lvirtio_reset
 testl %eax,%eax
 jnz Lneg_return
 movb $1,20(%rsi)
 cmpb $1,20(%rsi)
 jne Lneg_status
 movb $3,20(%rsi)
 cmpb $3,20(%rsi)
 jne Lneg_status
 movl $1,0(%rsi)
 movl 4(%rsi),%eax
 movl %eax,0x5da0
 testl $1,%eax
 jz Lneg_version
 movl $0,8(%rsi)
 movl $0,12(%rsi)
 movl $1,8(%rsi)
 movl $1,12(%rsi)
 movb $11,20(%rsi)
 cmpb $11,20(%rsi)
 jne Lneg_features
 cmpl $1,12(%rsi)
 jne Lneg_features
 xorl %eax,%eax
 retq
Lneg_status:
 movl $11,%eax
 retq
Lneg_version:
 movl $12,%eax
 retq
Lneg_features:
 movl $13,%eax
Lneg_return:
 retq
Ldev_result:
 .asciz "Virtio negotiation/reset result: 0x"
Ldev_cleanup:
 .asciz " cleanup: 0x"
Ldev_mapping:
 .asciz " remaining PTE: 0x"

Lshutdown:
 # Revoke all UDP authorizations whenever either interface is shut down.
 callq Lnat_revoke
 callq Lvirtio_reset
 movq %rax,0x5d78
 cmpq $2,0x5c20
 jb Ldev_no_dma_cleanup
 callq Ldma_cleanup
Ldev_no_dma_cleanup:
 movq $0,0x4100
 invlpg 0x20000
 cmpq $1,0x5a28
 je Ldev_keep_nx
 cmpq $2,0x5dc0
 je Ldev_keep_nx
 movl $0xc0000080,%ecx
 movl 0x5d30,%eax
 movl 0x5d34,%edx
 wrmsr
Ldev_keep_nx:
 movq $0,0x5d80
 retq

# Fixed conventional-RAM arena, four one-shot descriptors per queue.
# Software ownership and CPU page guards are not an IOMMU DMA fence.
Ldma_run:
 movq $4,0x5c38
 cmpq $4,0x5c20
 jne Ldma_capacity_set
 movq $16,0x5c38
Ldma_capacity_set:
 movq 0x5c38,%rax
 decq %rax
 movq %rax,0x5c40
 movq $0,0x5c50
 movq $0,0x5c30
 movq $0,0x5c28
 movq $0,0x5dd0
 movq $0,0x5dd8
 movq $0,0x5bf0
 movq $0,0x5ba0
 movq 0x5c38,%rax
 movq %rax,0x5ba8
 movq $0,0x5bb8
 movq $0,0x5bc0
 movq $0,0x5bc8
 cmpq $0,0x5dc0
 jne Ldma_busy
 cmpw $256,0x6f0
 jb Ldma_memory
 cmpq $0,0x4108
 jne Ldma_busy
 cmpq $-1,0x5dc8
 je Ldma_busy
 # Require all ten CPU mappings unused before acquiring any one of them.
 movl $0x4180,%edi
 movl $22,%ecx
Ldma_check_ptes:
 cmpq $0,(%rdi)
 jne Ldma_busy
 addl $8,%edi
 loop Ldma_check_ptes
 # PAT entry0 is the RAM mapping type; require WB if PAT exists.
 movl $1,%eax
 cpuid
 testl $0x10000,%edx
 jz Ldma_ram_cache_ok
 movl $0x277,%ecx
 rdmsr
 cmpb $6,%al
 jne Ldma_memory
Ldma_ram_cache_ok:
 incq 0x5dc8
 movq $1,0x5dc0
 movl $0x4180,%edi
 movl $0x30000,%ebx
 addl 0x5a40,%ebx
 movl $0x30000,%esi
 movl $22,%ecx
Ldma_map:
 movq %rbx,%rax
 orq $3,%rax
 btsq $63,%rax
 movq %rax,(%rdi)
 invlpg (%rsi)
 addl $8,%edi
 addl $4096,%ebx
 addl $4096,%esi
 loop Ldma_map
 cld
 movl $0x30000,%edi
 xorl %eax,%eax
 movl $11264,%ecx
 rep stosq
 # Build RX and TX descriptors and exact Ethernet test frames.
 xorl %r10d,%r10d
Ldma_descriptors:
 movq %r10,%rdi
 shlq $4,%rdi
 movq %r10,%rax
 shlq $11,%rax
 addq $0x36000,%rax
 addq 0x5a40,%rax
 movq %rax,0x30000(%rdi)
 movl $2048,0x30008(%rdi)
 movw $2,0x3000c(%rdi)
 movq %r10,%rax
 shlq $11,%rax
 addq $0x3e000,%rax
 addq 0x5a40,%rax
 movq %rax,0x33000(%rdi)
 movl $72,0x33008(%rdi)
 movw $0,0x3300c(%rdi)
 subq 0x5a40,%rax
 cmpq $4,0x5c20
 je Ldma_raw_descriptor
 cmpq $3,0x5c20
 jne Ldma_legacy_frame
 movl $86,0x33008(%rdi)
 callq Lpacket_build
 jmp Ldma_frame_ready
Ldma_legacy_frame:
 movl $0x32465202,12(%rax)
 movw $0x0300,16(%rax)
 movl $0x32465202,18(%rax)
 movw $0x0200,22(%rax)
 movw $0xb588,24(%rax)
 movabsq $0x3730414d44324652,%rdx
 movq %rdx,26(%rax)
 movq 0x5dc8,%rdx
 movq %rdx,34(%rax)
 leal 1(%r10d),%edx
 movl %edx,42(%rax)
 jmp Ldma_frame_ready
Ldma_raw_descriptor:
 movw %r10w,0x31004(,%r10,2)
 jmp Ldma_descriptor_next
Ldma_frame_ready:
 movw %r10w,0x31004(,%r10,2)
 callq Ltx_enqueue
 testl %eax,%eax
 jnz Ldma_queue_error
Ldma_descriptor_next:
 incq %r10
 cmpq 0x5c38,%r10
 jb Ldma_descriptors
 cmpq $4,0x5c20
 je Ldma_raw_descriptors_ready
 # A fifth publish must refuse without modifying the ring or producer index.
 callq Ltx_enqueue
 cmpl $1,%eax
 jne Ldma_queue_error
 movq $1,0x5bc8
Ldma_raw_descriptors_ready:
 movw $1,0x31000
 movw $1,0x34000
 mfence
 movq 0x5c38,%rax
 movw %ax,0x31002
 # Read the notification multiplier from the validated notification capability.
 movq 0x5610,%rdi
 addl $16,%edi
 callq Lpci_read
 movl %eax,0x5bf8
 xorl %r10d,%r10d
Ldma_setup_queue:
 movq 0x5d40,%rsi
 movw %r10w,22(%rsi)
 cmpw $0,28(%rsi)
 jne Ldma_queue_error
 movq 0x5c38,%rdx
 cmpw %dx,24(%rsi)
 jb Ldma_queue_error
 movw %dx,24(%rsi)
 cmpw %dx,24(%rsi)
 jne Ldma_queue_error
 movw $0xffff,26(%rsi)
 cmpw $0xffff,26(%rsi)
 jne Ldma_queue_error
 movq %r10,%rax
 imulq $0x3000,%rax,%rax
 addq $0x30000,%rax
 addq 0x5a40,%rax
 movq %rax,32(%rsi)
 cmpq %rax,32(%rsi)
 jne Ldma_queue_error
 addq $4096,%rax
 movq %rax,40(%rsi)
 cmpq %rax,40(%rsi)
 jne Ldma_queue_error
 addq $4096,%rax
 movq %rax,48(%rsi)
 cmpq %rax,48(%rsi)
 jne Ldma_queue_error
 movzwl 30(%rsi),%eax
 movl 0x5bf8,%ecx
 imulq %rcx,%rax
 movq 0x5e98,%rcx
 subq $2,%rcx
 cmpq %rcx,%rax
 ja Ldma_notify_error
 addq 0x5ea8,%rax
 movq %rax,%rdx
 andq $4095,%rdx
 cmpq $4094,%rdx
 ja Ldma_notify_error
 testl $1,%edx
 jnz Ldma_notify_error
 addq $0x21000,%rdx
 movq %rdx,0x5be0(,%r10,8)
 andq $-4096,%rax
 cmpq $0,%r10
 jne Ldma_notify_same
 movq %rax,0x5bd8
 orq $0x1b,%rax
 btsq $63,%rax
 movq %rax,0x4108
 invlpg 0x21000
 movq $1,0x5bf0
 jmp Ldma_notify_ready
Ldma_notify_same:
 cmpq 0x5bd8,%rax
 jne Ldma_notify_error
Ldma_notify_ready:
 movw $1,28(%rsi)
 cmpw $1,28(%rsi)
 jne Ldma_queue_error
 incq %r10
 cmpq $2,%r10
 jb Ldma_setup_queue
 movl $4,%edi
 callq Lpci_read
 andl $65535,%eax
 cmpl 0x5d00,%eax
 jne Ldma_queue_error
 orl $4,%eax
 callq Lcfg_write16
 callq Lpci_read
 testl $4,%eax
 jz Ldma_master_error
 movq 0x5d40,%rsi
 movb $15,20(%rsi)
 cmpb $15,20(%rsi)
 jne Ldma_queue_error
 mfence
 movq 0x5be0,%rdi
 movw $0,(%rdi)
 cmpq $4,0x5c20
 jne Ldma_fixture_start
 movq $1,0x5c28
 movq $1,0x5c30
 xorl %eax,%eax
 retq
Ldma_fixture_start:
 movq 0x5be8,%rdi
 movw $1,(%rdi)
 movl $0x1000000,%ecx
Ldma_poll:
 movzwl 0x35002,%eax
 subl 0x5bb8,%eax
 andl $65535,%eax
 cmpl $4,%eax
 ja Ldma_completion_error
 movzwl 0x32002,%edx
 subl 0x5ba0,%edx
 andl $65535,%edx
 cmpl $4,%edx
 ja Ldma_completion_error
 cmpl $4,%eax
 jne Ldma_poll_again
 cmpl $4,%edx
 je Ldma_complete
Ldma_poll_again:
 loop Ldma_poll
 movl $26,%eax
 retq
Ldma_complete:
 lfence
 callq Ldma_validate
 retq
Ltx_enqueue:
 movq 0x5bc0,%rax
 movq %rax,%rdx
 subq 0x5bb8,%rdx
 cmpq 0x5c38,%rdx
 jae Ltx_full
 movq %rax,%rdx
 andq 0x5c40,%rdx
 movw %dx,0x34004(,%rdx,2)
 incq %rax
 mfence
 movw %ax,0x34002
 movq %rax,0x5bc0
 xorl %eax,%eax
 retq
Ltx_full:
 movl $1,%eax
 retq
Ldma_validate:
 xorl %r10d,%r10d
 xorl %r11d,%r11d
 xorl %r8d,%r8d
 xorl %r9d,%r9d
Ldma_check_used:
 movq 0x5bb8,%rbx
 addq %r10,%rbx
 andq $3,%rbx
 movl 0x35004(,%rbx,8),%eax
 cmpl $4,%eax
 jae Ldma_completion_error
 btsq %rax,%r8
 jc Ldma_completion_error
 movq 0x5ba0,%rbx
 addq %r10,%rbx
 andq $3,%rbx
 movl 0x32004(,%rbx,8),%eax
 cmpl $4,%eax
 jae Ldma_completion_error
 btsq %rax,%r9
 jc Ldma_completion_error
 cmpq $3,0x5c20
 jne Ldma_legacy_validate
 cmpl $86,0x32008(,%rbx,8)
 jne Ldma_packet_error
 shlq $11,%rax
 addq $0x36000,%rax
 callq Lpacket_validate
 testl %eax,%eax
 jnz Ldma_packet_error
 jmp Ldma_validated_one
Ldma_legacy_validate:
 cmpl $72,0x32008(,%rbx,8)
 jne Ldma_packet_error
 shlq $11,%rax
 addq $0x36000,%rax
 cmpb $0,(%rax)
 jne Ldma_packet_error
 cmpb $0,1(%rax)
 jne Ldma_packet_error
 # Some QEMU non-mergeable headers leave num_buffers0; never accept >1.
 cmpw $1,10(%rax)
 ja Ldma_packet_error
 cmpl $0x32465202,12(%rax)
 jne Ldma_packet_error
 cmpw $0x0200,16(%rax)
 jne Ldma_packet_error
 cmpl $0x32465202,18(%rax)
 jne Ldma_packet_error
 cmpw $0x0300,22(%rax)
 jne Ldma_packet_error
 movl 42(%rax),%edx
 decl %edx
 cmpl $4,%edx
 jae Ldma_packet_error
 btsq %rdx,%r11
 jc Ldma_packet_error
 movq %rax,%rdi
 addq $24,%rdi
 movq %rdx,%rsi
 shlq $11,%rsi
 addq $0x3e018,%rsi
 movl $48,%ecx
 cld
 repe cmpsb
 jne Ldma_packet_error
Ldma_validated_one:
 incq %r10
 cmpq $4,%r10
 jb Ldma_check_used
 addq $4,0x5dd0
 addq $4,0x5dd8
 addq $4,0x5ba0
 addq $4,0x5bb8
 cmpq $3,0x5c20
 jne Ldma_batch_valid
 callq Ldma_repost
Ldma_batch_valid:
 xorl %eax,%eax
 retq
Ldma_busy:
 movl $20,%eax
 retq
Ldma_memory:
 movl $21,%eax
 retq
Ldma_queue_error:
 movl $22,%eax
 retq
Ldma_notify_error:
 movl $23,%eax
 retq
Ldma_master_error:
 movl $24,%eax
 retq
Ldma_completion_error:
 movl $27,%eax
 retq
Ldma_packet_error:
 movl $28,%eax
 retq
Ldma_cleanup:
 cmpq $0,0x5dc0
 je Ldma_cleanup_done
 # Stop bus mastering and require readback before considering reuse.
 movl $4,%edi
 movl 0x5d00,%eax
 andl $0xfffb,%eax
 callq Lcfg_write16
 callq Lpci_read
 testl $4,%eax
 jnz Ldma_quarantine
 cmpq $0,0x5d78
 jne Ldma_quarantine
 movl $0x4180,%edi
 movl $0x30000,%ebx
 addl 0x5a40,%ebx
 movl $22,%ecx
Ldma_check_owned:
 movq (%rdi),%rax
 andq $-97,%rax
 movq %rbx,%rdx
 orq $3,%rdx
 btsq $63,%rdx
 cmpq %rdx,%rax
 jne Ldma_foreign
 addl $8,%edi
 addl $4096,%ebx
 loop Ldma_check_owned
 cmpq $1,0x5bf0
 jne Ldma_owned_notify_ok
 movq 0x4108,%rax
 andq $-97,%rax
 movq 0x5bd8,%rdx
 orq $0x1b,%rdx
 btsq $63,%rdx
 cmpq %rdx,%rax
 jne Ldma_foreign
Ldma_owned_notify_ok:
 cld
 movl $0x30000,%edi
 xorl %eax,%eax
 movl $11264,%ecx
 rep stosq
 movq $0,0x5dc0
 jmp Ldma_unmap
Ldma_foreign:
 movq $30,0x5d78
Ldma_quarantine:
 movq $2,0x5dc0
 cmpq $0,0x5d78
 jne Ldma_unmap
 movq $29,0x5d78
Ldma_unmap:
 # CPU revocation is not DMA revocation. Quarantined physical pages stay reserved.
 movl $0x4180,%edi
 movl $0x30000,%ebx
 addl 0x5a40,%ebx
 movl $0x30000,%esi
 movl $22,%ecx
Ldma_unmap_loop:
 movq (%rdi),%rax
 andq $-97,%rax
 movq %rbx,%rdx
 orq $3,%rdx
 btsq $63,%rdx
 cmpq %rdx,%rax
 jne Ldma_keep_foreign
 movq $0,(%rdi)
 invlpg (%rsi)
Ldma_keep_foreign:
 addl $8,%edi
 addl $4096,%ebx
 addl $4096,%esi
 loop Ldma_unmap_loop
 cmpq $1,0x5bf0
 jne Ldma_cleanup_done
 movq 0x4108,%rax
 andq $-97,%rax
 movq 0x5bd8,%rdx
 orq $0x1b,%rdx
 btsq $63,%rdx
 cmpq %rdx,%rax
 jne Ldma_cleanup_done
 movq $0,0x4108
 invlpg 0x21000
 movq $0,0x5bf0
Ldma_cleanup_done:
 retq
Ldma_report:
 leaq Ldma_rx_text(%rip),%rsi
 callq Lputs
 movq 0x5dd0,%rax
 callq Lhex
 leaq Ldma_tx_text(%rip),%rsi
 callq Lputs
 movq 0x5dd8,%rax
 callq Lhex
 leaq Ldma_owner_text(%rip),%rsi
 callq Lputs
 movq 0x5dc0,%rax
 callq Lhex
 leaq Ldma_full_text(%rip),%rsi
 callq Lputs
 movq 0x5bc8,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 retq
Ldma_rx_text:
 .asciz "DMA RX=0x"
Ldma_tx_text:
 .asciz " TX=0x"
Ldma_owner_text:
 .asciz " owner=0x"
Ldma_full_text:
 .asciz " full-refusals=0x"

# Persistent four-slot rings. All counters are software u64 totals;
# the device sees their low16 bits. At most four descriptors outstanding.
Ldma_next_batch:
 cmpq $1,0x5dc0
 jne Ldma_busy
 movq 0x5d40,%rsi
 cmpb $15,20(%rsi)
 jne Ldma_queue_error
 movq 0x5bc0,%rax
 cmpq 0x5bb8,%rax
 jne Ldma_queue_error
 movl $0xfffffffb,%edx
 cmpq %rdx,%rax
 ja Ldma_queue_error
 xorl %r10d,%r10d
Ldma_refill_tx:
 movq %r10,%rax
 shlq $11,%rax
 addq $0x3e000,%rax
 callq Lpacket_build
 callq Ltx_enqueue
 testl %eax,%eax
 jnz Ldma_queue_error
 incq %r10
 cmpq $4,%r10
 jb Ldma_refill_tx
 callq Ltx_enqueue
 cmpl $1,%eax
 jne Ldma_queue_error
 incq 0x5bc8
 mfence
 movq 0x5be8,%rdi
 movw $1,(%rdi)
 movl $0x1000000,%ecx
 jmp Ldma_poll
Ldma_repost:
 # All four completed RX buffers have passed validation and are CPU-owned.
 cld
 movl $0x36000,%edi
 movl $1024,%ecx
 xorl %eax,%eax
 rep stosq
 xorl %ebx,%ebx
 movq 0x5ba8,%rax
Ldma_repost_one:
 movq %rax,%rdx
 andq $3,%rdx
 movw %bx,0x31004(,%rdx,2)
 incq %rax
 incq %rbx
 cmpq $4,%rbx
 jb Ldma_repost_one
 mfence
 movw %ax,0x31002
 movq %rax,0x5ba8
 mfence
 movq 0x5be0,%rdi
 movw $0,(%rdi)
 retq

# Restricted Ethernet/IPv4/UDP fixture profile. Not routing, ARP or NAT.
# RAX=CPU buffer, R10=descriptor slot. Preserve R8..R14.
Lpacket_build:
 movq %rax,%rdi
 pushq %rdi
 xorl %eax,%eax
 movl $11,%ecx
 cld
 rep stosq
 popq %rdi
 movl $0x32465202,12(%rdi)
 movl $0x32465202,18(%rdi)
 movl 0x5a38,%eax
 shll $1,%eax
 addl $3,%eax
 shll $8,%eax
 movw %ax,16(%rdi)
 subl $256,%eax
 movw %ax,22(%rdi)
 movw $8,24(%rdi)
 movl $0x3c000045,26(%rdi)
 movq 0x5bc0,%rax
 incq %rax
 rolw $8,%ax
 movw %ax,30(%rdi)
 movw $0x0040,32(%rdi)
 movw $0x1140,34(%rdi)
 movl 0x5a38,%eax
 shll $8,%eax
 addl $0x02004d0a,%eax
 movl %eax,38(%rdi)
 addl $0x01000000,%eax
 movl %eax,42(%rdi)
 movw $0x409c,46(%rdi)
 movw $0x419c,48(%rdi)
 movw $0x2800,50(%rdi)
 movabsq $0x2138305049324652,%rax
 movq %rax,54(%rdi)
 movq 0x5dc8,%rax
 movq %rax,62(%rdi)
 movq 0x5bc0,%rax
 incq %rax
 movl %eax,70(%rdi)
 leaq 26(%rdi),%rsi
 movl $10,%ecx
 xorl %edx,%edx
 callq Lchecksum
 movw %ax,36(%rdi)
 callq Ludp_seed
 leaq 46(%rdi),%rsi
 movl $20,%ecx
 callq Lchecksum
 testw %ax,%ax
 jnz Lpacket_nonzero_checksum
 movw $0xffff,%ax
Lpacket_nonzero_checksum:
 movw %ax,52(%rdi)
 retq
Lpacket_validate:
 movq %rax,%rdi
 cmpb $0,(%rdi)
 jne Lpacket_bad
 cmpb $0,1(%rdi)
 jne Lpacket_bad
 cmpw $1,10(%rdi)
 ja Lpacket_bad
 cmpl $0x32465202,12(%rdi)
 jne Lpacket_bad
 cmpl $0x32465202,18(%rdi)
 jne Lpacket_bad
 movl 0x5a38,%eax
 shll $1,%eax
 addl $2,%eax
 shll $8,%eax
 cmpw %ax,16(%rdi)
 jne Lpacket_bad
 addl $256,%eax
 cmpw %ax,22(%rdi)
 jne Lpacket_bad
 cmpw $8,24(%rdi)
 jne Lpacket_bad
 cmpb $0x45,26(%rdi)
 jne Lpacket_bad
 cmpw $0x3c00,28(%rdi)
 jne Lpacket_bad
 cmpw $0x0040,32(%rdi)
 jne Lpacket_bad
 cmpb $0,34(%rdi)
 je Lpacket_bad
 cmpb $17,35(%rdi)
 jne Lpacket_bad
 movl 0x5a38,%eax
 shll $8,%eax
 addl $0x03004d0a,%eax
 cmpl %eax,38(%rdi)
 jne Lpacket_bad
 subl $0x01000000,%eax
 cmpl %eax,42(%rdi)
 jne Lpacket_bad
 cmpw $0x419c,46(%rdi)
 jne Lpacket_bad
 cmpw $0x409c,48(%rdi)
 jne Lpacket_bad
 cmpw $0x2800,50(%rdi)
 jne Lpacket_bad
 cmpw $0,52(%rdi)
 je Lpacket_bad
 leaq 26(%rdi),%rsi
 movl $10,%ecx
 xorl %edx,%edx
 callq Lchecksum
 testw %ax,%ax
 jnz Lpacket_bad
 callq Ludp_seed
 leaq 46(%rdi),%rsi
 movl $20,%ecx
 callq Lchecksum
 testw %ax,%ax
 jnz Lpacket_bad
 movl 70(%rdi),%edx
 movq 0x5bc0,%rax
 cmpq %rax,%rdx
 ja Lpacket_bad
 subq $4,%rax
 cmpq %rax,%rdx
 jbe Lpacket_bad
 subq %rax,%rdx
 decq %rdx
 btsq %rdx,%r11
 jc Lpacket_bad
 movl 70(%rdi),%esi
 decl %esi
 andl $3,%esi
 shlq $11,%rsi
 addq $0x38036,%rsi
 addq $54,%rdi
 movl $32,%ecx
 cld
 repe cmpsb
 jne Lpacket_bad
 xorl %eax,%eax
 retq
Lpacket_bad:
 movl $28,%eax
 retq
Ludp_seed:
 leaq 38(%rdi),%rsi
 movl $4,%ecx
 movl $57,%edx
Ludp_seed_word:
 movzwl (%rsi),%eax
 rolw $8,%ax
 addl %eax,%edx
 addq $2,%rsi
 loop Ludp_seed_word
 retq
# One's-complement checksum over ECX network-order words with EDX seed.
# Maximum call20words; 32-bit accumulation cannot overflow this profile.
Lchecksum:
 movzwl (%rsi),%eax
 rolw $8,%ax
 addl %eax,%edx
 addq $2,%rsi
 loop Lchecksum
 movl %edx,%eax
 shrl $16,%eax
 andl $65535,%edx
 addl %eax,%edx
 movl %edx,%eax
 shrl $16,%eax
 andl $65535,%edx
 addl %eax,%edx
 notw %dx
 rolw $8,%dx
 movzwl %dx,%eax
 retq

# Two fixed interface contexts in one reserved metadata page. No SMP/reentrancy.
Lif_open0:
 movq $3,0x5a70
 movq $0,0x5a38
 movq $1,0x5a48
 jmp Lif_command
Lif_open1:
 movq $3,0x5a70
 movq $1,0x5a38
 movq $1,0x5a48
 jmp Lif_command
Lif_transfer0:
 movq $0,0x5a38
 movq $2,0x5a48
 jmp Lif_command
Lif_transfer1:
 movq $1,0x5a38
 movq $2,0x5a48
 jmp Lif_command
Lif_close0:
 movq $0,0x5a38
 movq $3,0x5a48
 jmp Lif_command
Lif_close1:
 movq $1,0x5a38
 movq $3,0x5a48
 jmp Lif_command
Lif_close_all:
 movq $0,0x5a38
 movq $3,0x5a48
 callq Lif_dispatch
 movq $1,0x5a38
 movq $3,0x5a48
 callq Lif_dispatch
 jmp Lprompt
Lif_command:
 callq Lif_dispatch
 jmp Lprompt
Lif_legacy_refused:
 leaq Lif_legacy_text(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lif_dispatch:
 pushfq
 cli
 cmpq $0,0x5a28
 jne Lif_initialized
 cmpq $1,0x5a48
 jne Lif_uninitialized
 callq Lif_engine_init
 testl %eax,%eax
 jnz Lif_uninitialized
Lif_initialized:
 movq 0x5a38,%rax
 imulq $0x30000,%rax,%rax
 movq %rax,0x5a40
 callq Lif_load
 movq $3,0x5c20
 cmpq $1,0x5a48
 jne Lif_mode_ready
 cmpq $4,0x5a70
 jne Lif_mode_ready
 movq $4,0x5c20
Lif_mode_ready:
 movq $0,0x5d70
 movq $0,0x5d78
 cmpq $1,0x5a48
 je Lif_open
 cmpq $3,0x5a48
 je Lif_close
 cmpq $1,0x5dc0
 jne Lif_busy
 cmpq $0,0x5c28
 jne Lif_busy
 callq Lif_focus
 testl %eax,%eax
 jnz Lif_focus_failed
 callq Ldma_next_batch
 movq %rax,0x5d70
 testl %eax,%eax
 jz Lif_save
 callq Lshutdown
 jmp Lif_save
Lif_open:
 cmpq $0,0x5dc0
 jne Lif_busy
 callq Lnet
 jmp Lif_save
Lif_close:
 cmpq $0,0x5dc0
 je Lif_save
 cmpq $1,0x5dc0
 jne Lif_busy
 callq Lif_focus
 testl %eax,%eax
 jnz Lif_focus_failed
 callq Lshutdown
 jmp Lif_save
Lif_busy:
 movq $20,0x5d70
 jmp Lif_save
Lif_focus_failed:
 movq $31,0x5d70
 movq $2,0x5dc0
Lif_save:
 callq Lif_unfocus
 callq Lif_store
 movq 0x5a38,%rax
 cmpq $0,0x5dc0
 je Lif_clear_open_bit
 btsq %rax,0x5a30
 jmp Lif_dispatch_done
Lif_clear_open_bit:
 btrq %rax,0x5a30
Lif_dispatch_done:
 popfq
 callq Lif_report
 retq
Lif_uninitialized:
 movq $20,0x5d70
 movq $0,0x5d78
 movq $0,0x5dc0
 movq $0,0x5dd0
 movq $0,0x5dd8
 popfq
 callq Lif_report
 retq
Lif_engine_init:
 cmpw $512,0x6f0
 jb Lif_engine_fail
 cmpq $0,0x4280
 jne Lif_engine_fail
 movl $1,%eax
 cpuid
 testl $0x10000,%edx
 jz Lif_engine_nx
 movl $0x277,%ecx
 rdmsr
 cmpb $6,%al
 jne Lif_engine_fail
Lif_engine_nx:
 movl $0x80000001,%eax
 cpuid
 testl $0x100000,%edx
 jz Lif_engine_fail
 movl $0xc0000080,%ecx
 rdmsr
 orl $0x800,%eax
 wrmsr
 btsq $63,0x40c0
 invlpg 0x18000
 movabsq $0x8000000000050003,%rax
 movq %rax,0x4280
 invlpg 0x50000
 movl $0x50000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 cld
 rep stosq
 cmpq $0,0x4298
 jne Lif_engine_fail
 movabsq $0x8000000000053003,%rax
 movq %rax,0x4298
 invlpg 0x53000
 movl $0x53000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 cmpq $0,0x42a0
 jne Lif_engine_fail
 movabsq $0x8000000000054003,%rax
 movq %rax,0x42a0
 invlpg 0x54000
 movl $0x54000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
 callq Lroute_init
 movq $1,0x5a28
 xorl %eax,%eax
 retq
Lif_engine_fail:
 movl $21,%eax
 retq
Lif_load:
 movq 0x5a38,%rsi
 shlq $11,%rsi
 addq $0x50000,%rsi
 movl $0x5b00,%edi
 movl $160,%ecx
 cld
 rep movsq
 movq 0x5a38,%rsi
 shlq $11,%rsi
 addq $0x50600,%rsi
 movl $0x5608,%edi
 movl $4,%ecx
 rep movsq
 movq 0x5c08,%r12
 movq 0x5c10,%r13
 movq 0x5c18,%r14
 retq
Lif_store:
 movq 0x5a38,%rdi
 shlq $11,%rdi
 addq $0x50000,%rdi
 movl $0x5b00,%esi
 movl $160,%ecx
 cld
 rep movsq
 movq 0x5a38,%rdi
 shlq $11,%rdi
 addq $0x50600,%rdi
 movl $0x5608,%esi
 movl $4,%ecx
 rep movsq
 retq
Lif_pincheck:
 movq %r12,%rax
 shlq $8,%rax
 orq %r13,%rax
 shlq $8,%rax
 orq %r14,%rax
 movq 0x5a38,%rdx
 btq %rdx,0x5ab0
 jnc Lif_pin_new
 cmpq 0x5aa0(,%rdx,8),%rax
 jne Lif_pin_bad
 xorl %eax,%eax
 retq
Lif_pin_new:
 movq %rax,0x5aa0(,%rdx,8)
 btsq %rdx,0x5ab0
 xorl %eax,%eax
 retq
Lif_pin_bad:
 movl $31,%eax
 retq
Lif_focus:
 cmpq $0,0x4100
 jne Lif_focus_bad
 cmpq $0,0x4108
 jne Lif_focus_bad
 movl $0x4180,%edi
 movl $22,%ecx
Lif_focus_empty:
 cmpq $0,(%rdi)
 jne Lif_focus_bad
 addl $8,%edi
 loop Lif_focus_empty
 xorl %edi,%edi
 callq Lpci_read
 cmpl 0x5d90,%eax
 jne Lif_focus_bad
 callq Lcaps
 cmpq $0,0x5b20
 jne Lif_focus_bad
 # Recheck region declarations against the saved, sized binding; no sizing writes.
 movl $1,%r10d
Lif_binding:
 movq %r10,%rbx
 shlq $6,%rbx
 addq $0x5e00,%rbx
 movq 0x5600(,%r10,8),%r11
 leal 4(%r11d),%edi
 callq Lpci_read
 andl $255,%eax
 cmpq (%rbx),%rax
 jne Lif_focus_bad
 leal 8(%r11d),%edi
 callq Lpci_read
 cmpq 16(%rbx),%rax
 jne Lif_focus_bad
 leal 12(%r11d),%edi
 callq Lpci_read
 cmpq 24(%rbx),%rax
 jne Lif_focus_bad
 movl (%rbx),%edi
 leal 16(,%rdi,4),%edi
 callq Lpci_read
 movl %eax,%ecx
 andl $0xfffffff0,%eax
 cmpq 8(%rbx),%rax
 jne Lif_focus_bad
 andl $6,%ecx
 cmpl $4,%ecx
 jne Lif_binding_next
 addl $4,%edi
 callq Lpci_read
 testl %eax,%eax
 jnz Lif_focus_bad
Lif_binding_next:
 incq %r10
 cmpq $5,%r10
 jb Lif_binding
 movq 0x5e68,%rax
 andq $-4096,%rax
 orq $0x1b,%rax
 btsq $63,%rax
 movq %rax,0x4100
 invlpg 0x20000
 movq $1,0x5d80
 movq 0x5bd8,%rax
 orq $0x1b,%rax
 btsq $63,%rax
 movq %rax,0x4108
 invlpg 0x21000
 movq $1,0x5bf0
 movl $0x30000,%ebx
 addl 0x5a40,%ebx
 movl $0x30000,%esi
 movl $0x4180,%edi
 movl $22,%ecx
Lif_focus_arena:
 movq %rbx,%rax
 orq $3,%rax
 btsq $63,%rax
 movq %rax,(%rdi)
 invlpg (%rsi)
 addl $8,%edi
 addl $4096,%ebx
 addl $4096,%esi
 loop Lif_focus_arena
 xorl %eax,%eax
 retq
Lif_focus_bad:
 movl $31,%eax
 retq
Lif_unfocus:
 # Revoke only matching CPU aliases. Hardware ownership remains per interface.
 cmpq $1,0x5d80
 jne Lif_unfocus_notify
 movq 0x5e68,%rdx
 andq $-4096,%rdx
 orq $0x1b,%rdx
 btsq $63,%rdx
 movq 0x4100,%rax
 andq $-97,%rax
 cmpq %rdx,%rax
 jne Lif_unfocus_conflict
 movq $0,0x4100
 invlpg 0x20000
 movq $0,0x5d80
Lif_unfocus_notify:
 cmpq $1,0x5bf0
 jne Lif_unfocus_arena_start
 movq 0x5bd8,%rdx
 orq $0x1b,%rdx
 btsq $63,%rdx
 movq 0x4108,%rax
 andq $-97,%rax
 cmpq %rdx,%rax
 jne Lif_unfocus_conflict
 movq $0,0x4108
 invlpg 0x21000
 movq $0,0x5bf0
Lif_unfocus_arena_start:
 movl $0x30000,%ebx
 addl 0x5a40,%ebx
 movl $0x30000,%esi
 movl $0x4180,%edi
 movl $22,%ecx
Lif_unfocus_arena:
 movq (%rdi),%rax
 testq %rax,%rax
 jz Lif_unfocus_arena_next
 andq $-97,%rax
 movq %rbx,%rdx
 orq $3,%rdx
 btsq $63,%rdx
 cmpq %rdx,%rax
 jne Lif_unfocus_conflict
 movq $0,(%rdi)
 invlpg (%rsi)
Lif_unfocus_arena_next:
 addl $8,%edi
 addl $4096,%ebx
 addl $4096,%esi
 loop Lif_unfocus_arena
 retq
Lif_unfocus_conflict:
 movq $30,0x5d78
 movq $2,0x5dc0
 retq
Lif_report:
 leaq Lif_slot_text(%rip),%rsi
 callq Lputs
 movq 0x5a38,%rax
 callq Lhex
 leaq Lif_result_text(%rip),%rsi
 callq Lputs
 movq 0x5d70,%rax
 callq Lhex
 leaq Ldev_cleanup(%rip),%rsi
 callq Lputs
 movq 0x5d78,%rax
 callq Lhex
 leaq Lif_mask_text(%rip),%rsi
 callq Lputs
 movq 0x5a30,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 callq Ldma_report
 retq
Lif_slot_text:
 .asciz "Interface0x"
Lif_result_text:
 .asciz " result=0x"
Lif_mask_text:
 .asciz " active=0x"
Lif_legacy_text:
 .asciz "Use a/b, t/u and c/e after interface engine initialization.\r\n"


Ldebug_refused:
 leaq Ldebug_disabled(%rip),%rsi
 callq Lputs
 jmp Lprompt
Ldebug_disabled:
 .asciz "Debug operation disabled.\r\n"
