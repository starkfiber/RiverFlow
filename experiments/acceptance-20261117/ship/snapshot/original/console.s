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

# QEMU PC/Q35 lab HPET contract: fixed mapped address, 64-bit counter and period.
# Not ACPI discovery, physical clock calibration or hostile-hypervisor time.
Lclock_init:
 cmpq $1,0x5a28
 jne Lclock_fail
 cmpq $0,0x4290
 jne Lclock_fail
 movl $1,%eax
 cpuid
 testl $0x10000,%edx
 jz Lclock_map
 movl $0x277,%ecx
 rdmsr
 shrl $24,%eax
 testb %al,%al
 jnz Lclock_fail
Lclock_map:
 movabsq $0x80000000fed0001b,%rax
 movq %rax,0x4290
 invlpg 0x52000
 movq 0x52000,%r8
 testl $0x2000,%r8d
 jz Lclock_unmap_fail
 movq %r8,%rcx
 shrq $32,%rcx
 testq %rcx,%rcx
 jz Lclock_unmap_fail
 cmpq $100000000,%rcx
 ja Lclock_unmap_fail
 movq %rcx,0x5a58
 movq 0x52010,%rax
 testb $2,%al
 jnz Lclock_unmap_fail
 orq $1,%rax
 movq %rax,0x52010
 testq $1,0x52010
 jz Lclock_unmap_fail
 movabsq $3000000000000000,%rax
 xorl %edx,%edx
 divq %rcx
 testq %rdx,%rdx
 jz Lclock_lifetime
 incq %rax
Lclock_lifetime:
 movq %rax,0x5a68
 movq 0x520f0,%r8
 movl $1000000,%ecx
Lclock_progress:
 movq 0x520f0,%rax
 cmpq %r8,%rax
 jb Lclock_unmap_fail
 ja Lclock_started
 loop Lclock_progress
 jmp Lclock_unmap_fail
Lclock_started:
 movq %rax,0x5a60
 movq $1,0x5a50
 xorl %edx,%edx
 retq
Lclock_unmap_fail:
 movq $0,0x4290
 invlpg 0x52000
Lclock_fail:
 movq $2,0x5a50
 callq Lnat_revoke
 movl $37,%edx
 retq
Lclock_now:
 cmpq $0,0x5a50
 je Lclock_init
 cmpq $1,0x5a50
 jne Lclock_fail
 movl 0x52004,%eax
 cmpq 0x5a58,%rax
 jne Lclock_fail
 movq 0x52010,%rax
 andl $3,%eax
 cmpl $1,%eax
 jne Lclock_fail
 movq 0x520f0,%rax
 cmpq 0x5a60,%rax
 jb Lclock_fail
 movq %rax,0x5a60
 xorl %edx,%edx
 retq
Lclock_report:
 pushfq
 cli
 callq Lclock_now
 popfq
 leaq Lclock_text(%rip),%rsi
 callq Lputs
 movq 0x5a50,%rax
 callq Lhex
 leaq Lclock_period_text(%rip),%rsi
 callq Lputs
 movq 0x5a58,%rax
 callq Lhex
 leaq Lclock_count_text(%rip),%rsi
 callq Lputs
 movq 0x5a60,%rax
 callq Lhex
 leaq Lnewline(%rip),%rsi
 callq Lputs
 jmp Lprompt
Lclock_text:
 .asciz "HPET state=0x"
Lclock_period_text:
 .asciz " period-fs=0x"
Lclock_count_text:
 .asciz " counter=0x"

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

# Static peer/gateway ARP request/reply profile. No learning, proxy ARP or VLAN.
Larp_reply:
 cmpw $0x0200,20(%rdi)
 je Lneighbor_reply
 cmpq $60,0x5ac8
 jne Lnat_bad
 cmpw $0x0100,14(%rdi)
 jne Lnat_bad
 cmpw $8,16(%rdi)
 jne Lnat_bad
 cmpw $0x0406,18(%rdi)
 jne Lnat_bad
 cmpw $0x0100,20(%rdi)
 jne Lnat_bad
 movq 0x5ad0,%rax
 shll $1,%eax
 addl $2,%eax
 shll $8,%eax
 movl %eax,%r8d
 leal 256(%rax),%r9d
 cmpl $0x32465202,6(%rdi)
 jne Lnat_policy
 cmpw %r9w,10(%rdi)
 jne Lnat_policy
 movl 6(%rdi),%eax
 cmpl %eax,22(%rdi)
 jne Lnat_policy
 movzwl 10(%rdi),%eax
 cmpw %ax,26(%rdi)
 jne Lnat_policy
 cmpl $-1,(%rdi)
 jne Larp_unicast
 cmpw $0xffff,4(%rdi)
 je Larp_destination_ok
Larp_unicast:
 cmpl $0x32465202,(%rdi)
 jne Lnat_policy
 cmpw %r8w,4(%rdi)
 jne Lnat_policy
Larp_destination_ok:
 movl $0x02004d0a,%r10d
 movl $0x03004d0a,%r11d
 cmpq $0,0x5ad0
 je Larp_addresses
 movl $0x026433c6,%r10d
 movl $0x096433c6,%r11d
Larp_addresses:
 cmpl %r11d,28(%rdi)
 jne Lnat_policy
 cmpl %r10d,38(%rdi)
 jne Lnat_policy
 movq 32(%rdi),%rax
 shlq $16,%rax
 testq %rax,%rax
 jz Larp_target_ok
 cmpl $0x32465202,32(%rdi)
 jne Lnat_policy
 cmpw %r8w,36(%rdi)
 jne Lnat_policy
Larp_target_ok:
 movl 6(%rdi),%eax
 movl %eax,(%rdi)
 movw %r9w,4(%rdi)
 movl $0x32465202,6(%rdi)
 movw %r8w,10(%rdi)
 movw $0x0200,20(%rdi)
 movl 22(%rdi),%eax
 movl %eax,32(%rdi)
 movw 26(%rdi),%ax
 movw %ax,36(%rdi)
 movl %r11d,38(%rdi)
 movl $0x32465202,22(%rdi)
 movw %r8w,26(%rdi)
 movl %r10d,28(%rdi)
 movq $0,42(%rdi)
 movq $0,50(%rdi)
 movw $0,58(%rdi)
 movq 0x5ad0,%rax
 movq %rax,0x507e0
 movq $1,0x507e8
 xorl %eax,%eax
 retq

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

# Four64-byte neighbor slots; one2048-byte owned packet per slot. SingleCPU.
Lpending_init:
 movabsq $0x8000000000056003,%rax
 movq %rax,0x42b0
 addq $4096,%rax
 movq %rax,0x42b8
 addq $4096,%rax
 movq %rax,0x42c0
 addq $4096,%rax
 movq %rax,0x42c8
 invlpg 0x56000
 invlpg 0x57000
 invlpg 0x58000
 invlpg 0x59000
 movl $0x56000,%edi
 movl $2048,%ecx
 xorl %eax,%eax
 rep stosq
 retq
Lpending_revoke:
 pushq %r8
 pushq %r9
 movl $0x56000,%r8d
 movl $4,%r9d
Lpending_count_cancel:
 cmpq $0,(%r8)
 je Lpending_count_next
 incq 0x540d0
 movq $45,0x550a8
Lpending_count_next:
 addq $2048,%r8
 decl %r9d
 jnz Lpending_count_cancel
 movl $0x55100,%edi
 movl $32,%ecx
 xorl %eax,%eax
 rep stosq
 movq $0,0x550a0
 movl $0x56000,%edi
 movl $2048,%ecx
 rep stosq
 popq %r9
 popq %r8
 retq
# r8=entry,r9=index. Erase matching pending owner before slot reuse.
Lneighbor_erase:
 pushq %rdi
 pushq %rcx
 movq %r8,%rdi
 movl $8,%ecx
 xorl %eax,%eax
 rep stosq
 movq %r9,%rdi
 shlq $11,%rdi
 addq $0x56000,%rdi
 cmpq $0,(%rdi)
 je Lneighbor_erase_empty
 incq 0x540d0
Lneighbor_erase_empty:
 movl $256,%ecx
 rep stosq
 popq %rcx
 popq %rdi
 retq
# eax=0 valid,39 stale; requires current timestamp53f18.
Lneighbor_valid:
 cmpq $0,(%r8)
 je Lroute_absent
 movq 0x55000,%rax
 cmpq 40(%r8),%rax
 jne Lroute_absent
 movq 0x50ac8,%rax
 cmpq 32(%r8),%rax
 jne Lroute_absent
 movq 0x53f18,%rax
 subq 24(%r8),%rax
 jc Lroute_absent
 cmpq 0x5a68,%rax
 jae Lroute_absent
 xorl %eax,%eax
 retq
Lneighbor_get:
 movl 0x55080,%r11d
 movl $0x55100,%r8d
 xorl %r9d,%r9d
 movq $-1,%r10
Lneighbor_scan:
 callq Lneighbor_valid
 testl %eax,%eax
 jz Lneighbor_live
 callq Lneighbor_erase
 cmpq $-1,%r10
 jne Lneighbor_advance
 movq %r8,%r10
 jmp Lneighbor_advance
Lneighbor_live:
 cmpl 8(%r8),%r11d
 jne Lneighbor_advance
 movq %r8,0x55098
 cmpq $2,(%r8)
 jne Lroute_absent
 movq 16(%r8),%rax
 movq %rax,0x55088
 xorl %eax,%eax
 retq
Lneighbor_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_scan
 movq %r10,0x55098
 jmp Lroute_absent
Lneighbor_source:
 movl $0x55100,%r8d
 xorl %r9d,%r9d
Lneighbor_source_next:
 cmpq $2,(%r8)
 jne Lneighbor_source_advance
 callq Lneighbor_valid
 testl %eax,%eax
 jnz Lneighbor_source_advance
 movq 6(%rdi),%rax
 shlq $16,%rax
 shrq $16,%rax
 cmpq 16(%r8),%rax
 jne Lneighbor_source_advance
 movq %rax,0x55088
 xorl %eax,%eax
 retq
Lneighbor_source_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_source_next
 jmp Lroute_absent
Lneighbor_probe:
 movq 0x55098,%r8
 cmpq $-1,%r8
 je Lpending_full
 movq %r8,%r9
 subq $0x55100,%r9
 cmpq $192,%r9
 ja Lnat_policy
 shrq $6,%r9
 shlq $11,%r9
 addq $0x56000,%r9
 cmpq $0,(%r9)
 jne Lpending_full
 cmpq $1514,0x5ac8
 ja Lnat_bad
 movq 0x5ac8,%rax
 movq %rax,8(%r9)
 movq 0x53f18,%rax
 movq %rax,16(%r9)
 movq %rax,24(%r8)
 movq 0x502c8,%rax
 movq %rax,24(%r9)
 movq 0x50ac8,%rax
 movq %rax,32(%r9)
 movq %rax,32(%r8)
 movq 0x55000,%rax
 movq %rax,40(%r9)
 movq %rax,40(%r8)
 movl 0x55080,%eax
 movl %eax,48(%r9)
 movl %eax,8(%r8)
 pushq %rdi
 movq %rdi,%rsi
 leaq 64(%r9),%rdi
 movq 0x5ac8,%rcx
 rep movsb
 popq %rdi
 movq $1,(%r9)
 movq $1,(%r8)
 incq 0x540c0
 pushq %rdi
 movl $60,%ecx
 xorl %eax,%eax
 rep stosb
 popq %rdi
 movl $-1,(%rdi)
 movw $-1,4(%rdi)
 movl $0x32465202,6(%rdi)
 movw $0x0400,10(%rdi)
 movw $0x0608,12(%rdi)
 movw $0x0100,14(%rdi)
 movw $8,16(%rdi)
 movw $0x0406,18(%rdi)
 movw $0x0100,20(%rdi)
 movl $0x32465202,22(%rdi)
 movw $0x0400,26(%rdi)
 movl $0x026433c6,28(%rdi)
 movl 0x55080,%eax
 movl %eax,38(%rdi)
 movq $60,0x5ac8
 movq $4,0x507e8
 xorl %eax,%eax
 retq
Lpending_full:
 incq 0x540d8
 movl $44,%eax
 retq
Lneighbor_reply:
 cmpq $1,0x5ad0
 jne Lnat_policy
 cmpq $60,0x5ac8
 jne Lnat_bad
 cmpw $0x0608,12(%rdi)
 jne Lnat_bad
 cmpw $0x0100,14(%rdi)
 jne Lnat_bad
 cmpw $8,16(%rdi)
 jne Lnat_bad
 cmpw $0x0406,18(%rdi)
 jne Lnat_bad
 cmpl $0x32465202,(%rdi)
 jne Lnat_policy
 cmpw $0x0400,4(%rdi)
 jne Lnat_policy
 cmpl $0x32465202,32(%rdi)
 jne Lnat_policy
 cmpw $0x0400,36(%rdi)
 jne Lnat_policy
 cmpl $0x026433c6,38(%rdi)
 jne Lnat_policy
 movl 6(%rdi),%eax
 cmpl %eax,22(%rdi)
 jne Lnat_policy
 movzwl 10(%rdi),%eax
 cmpw %ax,26(%rdi)
 jne Lnat_policy
 testb $1,6(%rdi)
 jnz Lnat_policy
 movl 6(%rdi),%eax
 movzwl 10(%rdi),%edx
 orl %edx,%eax
 jz Lnat_policy
 movl $0x55100,%r8d
 xorl %r9d,%r9d
Lneighbor_reply_next:
 cmpq $1,(%r8)
 jne Lneighbor_reply_advance
 movl 28(%rdi),%eax
 cmpl 8(%r8),%eax
 jne Lneighbor_reply_advance
 callq Lneighbor_valid
 testl %eax,%eax
 jnz Lnat_policy
 movq 6(%rdi),%rax
 shlq $16,%rax
 shrq $16,%rax
 movq %rax,16(%r8)
 movq 0x53f18,%rax
 movq %rax,24(%r8)
 movq $2,(%r8)
 incq %r9
 movq %r9,0x550a0
 movl $42,%eax
 retq
Lneighbor_reply_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_reply_next
 jmp Lnat_policy
# Transfer one pending owner into staging, clear original before revalidation/TX.
Lpending_flush:
 cmpq $1,0x5a28
 jne Lpending_done
 cmpq $0,0x550a0
 je Lpending_done
 pushq 0x5ad0
 pushq 0x5ad8
 pushq 0x5ac0
 pushq 0x5ac8
 movq 0x550a0,%r15
 movq $0,0x550a0
 decq %r15
 cmpq $3,%r15
 ja Lpending_restore
 shlq $11,%r15
 addq $0x56000,%r15
 cmpq $1,(%r15)
 jne Lpending_restore
 callq Lclock_now
 testl %edx,%edx
 jnz Lpending_cancel
 movq %rax,0x53f18
 subq 16(%r15),%rax
 jc Lpending_cancel
 cmpq 0x5a68,%rax
 jae Lpending_cancel
 movq 0x502c8,%rax
 cmpq 24(%r15),%rax
 jne Lpending_cancel
 movq 0x50ac8,%rax
 cmpq 32(%r15),%rax
 jne Lpending_cancel
 movq 0x55000,%rax
 cmpq 40(%r15),%rax
 jne Lpending_cancel
 movq 8(%r15),%rcx
 cmpq $60,%rcx
 jb Lpending_cancel
 cmpq $1514,%rcx
 ja Lpending_cancel
 movq %rcx,0x5ac8
 leaq 64(%r15),%rsi
 movl $0x51040,%edi
 rep movsb
 movq %r15,%rdi
 movl $256,%ecx
 xorl %eax,%eax
 rep stosq
 movq $0,0x5ad0
 movq $1,0x5ad8
 movq $2,0x507e0
 movq $0,0x507e8
 callq Lnat_transform
 testl %eax,%eax
 jnz Lpending_result
 movq $1,%rax
 callq Lrelay_select
 testl %eax,%eax
 jnz Lpending_result
 movq $1,0x5c28
 callq Lrelay_transmit
 testl %eax,%eax
 jnz Lpending_tx_failed
 callq Lnat_commit
 jmp Lpending_save
Lpending_tx_failed:
 pushq %rax
 callq Lshutdown
 callq Lnat_revoke
 popq %rax
Lpending_save:
 movq %rax,0x550a8
 callq Lrelay_save
 movq 0x550a8,%rax
Lpending_result:
 movq %rax,0x550a8
 testl %eax,%eax
 jnz Lpending_failed
 incq 0x540c8
 jmp Lpending_clear_stage
Lpending_failed:
 incq 0x540d0
 jmp Lpending_clear_stage
Lpending_cancel:
 movq %r15,%rdi
 movl $256,%ecx
 xorl %eax,%eax
 rep stosq
 incq 0x540d0
 movq $45,0x550a8
Lpending_clear_stage:
 callq Ltcp_scratch_clear
 movl $0x51000,%edi
 movl $512,%ecx
 xorl %eax,%eax
 rep stosq
Lpending_restore:
 popq 0x5ac8
 popq 0x5ac0
 popq 0x5ad8
 popq 0x5ad0
Lpending_done:
 retq

# Called by the continuous service, so expired owners do not await new traffic.
Lneighbor_sweep:
 movl $0x55100,%r8d
 xorl %r9d,%r9d
Lneighbor_sweep_next:
 callq Lneighbor_valid
 testl %eax,%eax
 jz Lneighbor_sweep_advance
 callq Lneighbor_erase
Lneighbor_sweep_advance:
 addq $64,%r8
 incq %r9
 cmpq $4,%r9
 jb Lneighbor_sweep_next
 retq

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

	.section	__TEXT,__text,regular,pure_instructions
Lcrypto_rf2_aead:                              ## @rf2_aead
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	subq	$568, %rsp                      ## imm = 0x238
	movq	64(%rdi), %r14
	movq	80(%rdi), %r15
	movl	$129, %eax
	cmpq	%rax, %r14
	setae	%cl
	cmpq	%rax, %r15
	setae	%al
	orb	%cl, %al
	je	LBB0_2
## %bb.1:
	pushq	$2
	popq	%rbx
	jmp	LBB0_38
LBB0_2:
	movq	%rdi, %r13
	leaq	8(%rdi), %rsi
	leaq	40(%rdi), %rdx
	movq	56(%rdi), %rbx
	movq	72(%rdi), %r12
	movq	88(%rdi), %rax
	movq	%rax, -152(%rbp)                ## 8-byte Spill
	leaq	-336(%rbp), %rdi
	movq	%rsi, -144(%rbp)                ## 8-byte Spill
	movq	%rdx, -136(%rbp)                ## 8-byte Spill
	xorl	%ecx, %ecx
	callq	Lcrypto_block
	cmpq	$0, (%r13)
	jne	LBB0_4
## %bb.3:
	movq	%r12, %rdi
	movq	%r15, %rsi
	movq	-144(%rbp), %rdx                ## 8-byte Reload
	movq	-136(%rbp), %rcx                ## 8-byte Reload
	callq	Lcrypto_cipher
LBB0_4:
	xorl	%eax, %eax
LBB0_5:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	%rax, %r14
	je	LBB0_6
## %bb.39:                              ##   in Loop: Header=BB0_5 Depth=1
	movb	(%rbx,%rax), %cl
	movb	%cl, -608(%rbp,%rax)
	incq	%rax
	jmp	LBB0_5
LBB0_6:
	leaq	(%r14,%rbp), %rbx
	addq	$-608, %rbx                     ## imm = 0xFDA0
	movq	%r14, %rdx
LBB0_7:                                 ## =>This Inner Loop Header: Depth=1
	testb	$15, %dl
	je	LBB0_8
## %bb.40:                              ##   in Loop: Header=BB0_7 Depth=1
	incq	%rdx
	movb	$0, (%rbx)
	incq	%rbx
	jmp	LBB0_7
LBB0_8:
	xorl	%eax, %eax
LBB0_9:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	%rax, %r15
	je	LBB0_10
## %bb.41:                              ##   in Loop: Header=BB0_9 Depth=1
	movb	(%r12,%rax), %cl
	movb	%cl, (%rbx,%rax)
	incq	%rax
	jmp	LBB0_9
LBB0_10:
	addq	%rax, %rbx
	addq	%rax, %rdx
LBB0_11:                                ## =>This Inner Loop Header: Depth=1
	testb	$15, %dl
	je	LBB0_13
## %bb.12:                              ##   in Loop: Header=BB0_11 Depth=1
	incq	%rdx
	movb	$0, (%rbx)
	incq	%rbx
	jmp	LBB0_11
LBB0_13:
	movq	%rbx, %rdi
	movq	%r14, %rsi
	movq	%rdx, %r14
	callq	Lcrypto_s64
	addq	$8, %rbx
	movq	%rbx, %rdi
	movq	%r15, %rsi
	callq	Lcrypto_s64
	movq	%r14, %rdx
	andq	$0, -112(%rbp)
	andq	$0, -120(%rbp)
	andq	$0, -128(%rbp)
	xorl	%eax, %eax
LBB0_14:                                ## =>This Inner Loop Header: Depth=1
	cmpq	$16, %rax
	je	LBB0_15
## %bb.42:                              ##   in Loop: Header=BB0_14 Depth=1
	movb	-336(%rbp,%rax), %cl
	movb	%cl, -64(%rbp,%rax)
	incq	%rax
	jmp	LBB0_14
LBB0_15:
	movq	%r13, -176(%rbp)                ## 8-byte Spill
	movq	%r12, -160(%rbp)                ## 8-byte Spill
	movq	%r15, -168(%rbp)                ## 8-byte Spill
	andb	$15, -61(%rbp)
	andb	$15, -57(%rbp)
	andb	$15, -53(%rbp)
	andb	$15, -49(%rbp)
	andb	$-4, -60(%rbp)
	andb	$-4, -56(%rbp)
	andb	$-4, -52(%rbp)
	addq	$16, %rdx
	xorl	%r12d, %r12d
	leaq	-96(%rbp), %r13
	leaq	-240(%rbp), %rbx
	leaq	-272(%rbp), %r14
	movq	%rdx, -184(%rbp)                ## 8-byte Spill
LBB0_16:                                ## =>This Loop Header: Depth=1
                                        ##     Child Loop BB0_18 Depth 2
                                        ##       Child Loop BB0_23 Depth 3
                                        ##     Child Loop BB0_20 Depth 2
	cmpq	%rdx, %r12
	jae	LBB0_27
## %bb.17:                              ##   in Loop: Header=BB0_16 Depth=1
	movq	-608(%rbp,%r12), %rax
	movq	-600(%rbp,%r12), %rcx
	movq	%rax, -208(%rbp)
	movq	%rcx, -200(%rbp)
	movq	$1, -192(%rbp)
	leaq	-128(%rbp), %rdi
	leaq	-208(%rbp), %rsi
	callq	Lcrypto_addp
	andq	$0, -80(%rbp)
	andq	$0, -88(%rbp)
	andq	$0, -96(%rbp)
	movq	-128(%rbp), %rax
	movq	-120(%rbp), %rcx
	movq	%rax, -240(%rbp)
	movq	%rcx, -232(%rbp)
	movq	-112(%rbp), %rax
	movq	%rax, -224(%rbp)
	xorl	%r15d, %r15d
LBB0_18:                                ##   Parent Loop BB0_16 Depth=1
                                        ## =>  This Loop Header: Depth=2
                                        ##       Child Loop BB0_23 Depth 3
	cmpl	$128, %r15d
	je	LBB0_19
## %bb.22:                              ##   in Loop: Header=BB0_18 Depth=2
	movl	%r15d, %eax
	shrl	$3, %eax
	movzbl	-64(%rbp,%rax), %eax
	movl	%r15d, %ecx
	andl	$7, %ecx
	btl	%ecx, %eax
	movl	$0, %eax
	sbbq	%rax, %rax
	xorl	%ecx, %ecx
LBB0_23:                                ##   Parent Loop BB0_16 Depth=1
                                        ##     Parent Loop BB0_18 Depth=2
                                        ## =>    This Inner Loop Header: Depth=3
	cmpq	$3, %rcx
	je	LBB0_24
## %bb.25:                              ##   in Loop: Header=BB0_23 Depth=3
	movq	-240(%rbp,%rcx,8), %rdx
	andq	%rax, %rdx
	movq	%rdx, -272(%rbp,%rcx,8)
	incq	%rcx
	jmp	LBB0_23
LBB0_24:                                ##   in Loop: Header=BB0_18 Depth=2
	movq	%r13, %rdi
	movq	%r14, %rsi
	callq	Lcrypto_addp
	movq	%rbx, %rdi
	movq	%rbx, %rsi
	callq	Lcrypto_addp
	incl	%r15d
	jmp	LBB0_18
LBB0_19:                                ##   in Loop: Header=BB0_16 Depth=1
	xorl	%eax, %eax
LBB0_20:                                ##   Parent Loop BB0_16 Depth=1
                                        ## =>  This Inner Loop Header: Depth=2
	cmpq	$3, %rax
	je	LBB0_26
## %bb.21:                              ##   in Loop: Header=BB0_20 Depth=2
	movq	-96(%rbp,%rax,8), %rcx
	movq	%rcx, -128(%rbp,%rax,8)
	incq	%rax
	jmp	LBB0_20
LBB0_26:                                ##   in Loop: Header=BB0_16 Depth=1
	movq	%r13, %rdi
	pushq	$24
	popq	%r15
	movq	%r15, %rsi
	callq	Lcrypto_wipe
	movq	%rbx, %rdi
	movq	%r15, %rsi
	callq	Lcrypto_wipe
	movq	%r14, %rdi
	movq	%r15, %rsi
	callq	Lcrypto_wipe
	addq	$16, %r12
	movq	-184(%rbp), %rdx                ## 8-byte Reload
	jmp	LBB0_16
LBB0_27:
	movq	-320(%rbp), %r14
	leaq	-128(%rbp), %rbx
	movq	(%rbx), %r15
	leaq	(%r14,%r15), %rsi
	leaq	-96(%rbp), %rdi
	callq	Lcrypto_s64
	addq	%r15, %r14
	leaq	-88(%rbp), %rdi
	movq	-312(%rbp), %rsi
	adcq	8(%rbx), %rsi
	callq	Lcrypto_s64
	leaq	-64(%rbp), %rdi
	pushq	$16
	popq	%rsi
	callq	Lcrypto_wipe
	pushq	$24
	popq	%r14
	movq	%rbx, %rdi
	movq	%r14, %rsi
	callq	Lcrypto_wipe
	leaq	-208(%rbp), %rdi
	movq	%r14, %rsi
	callq	Lcrypto_wipe
	movq	-176(%rbp), %rax                ## 8-byte Reload
	cmpq	$0, (%rax)
	je	LBB0_33
## %bb.28:
	xorl	%eax, %eax
	xorl	%ecx, %ecx
	movq	-168(%rbp), %rsi                ## 8-byte Reload
	movq	-152(%rbp), %r8                 ## 8-byte Reload
	movq	-160(%rbp), %rdi                ## 8-byte Reload
LBB0_29:                                ## =>This Inner Loop Header: Depth=1
	cmpq	$16, %rax
	je	LBB0_30
## %bb.32:                              ##   in Loop: Header=BB0_29 Depth=1
	movb	(%r8,%rax), %dl
	xorb	-96(%rbp,%rax), %dl
	movzbl	%dl, %edx
	orl	%edx, %ecx
	incq	%rax
	jmp	LBB0_29
LBB0_30:
	testl	%ecx, %ecx
	je	LBB0_36
## %bb.31:
	pushq	$1
	popq	%rbx
	jmp	LBB0_37
LBB0_33:
	xorl	%ebx, %ebx
	xorl	%eax, %eax
	movq	-152(%rbp), %rdx                ## 8-byte Reload
LBB0_34:                                ## =>This Inner Loop Header: Depth=1
	cmpq	$16, %rax
	je	LBB0_37
## %bb.35:                              ##   in Loop: Header=BB0_34 Depth=1
	movb	-96(%rbp,%rax), %cl
	movb	%cl, (%rdx,%rax)
	incq	%rax
	jmp	LBB0_34
LBB0_36:
	movq	-144(%rbp), %rdx                ## 8-byte Reload
	movq	-136(%rbp), %rcx                ## 8-byte Reload
	callq	Lcrypto_cipher
	xorl	%ebx, %ebx
LBB0_37:
	leaq	-336(%rbp), %rdi
	pushq	$64
	popq	%rsi
	callq	Lcrypto_wipe
	leaq	-608(%rbp), %rdi
	movl	$272, %esi                      ## imm = 0x110
	callq	Lcrypto_wipe
	leaq	-96(%rbp), %rdi
	pushq	$16
	popq	%rsi
	callq	Lcrypto_wipe
LBB0_38:
	movl	%ebx, %eax
	addq	$568, %rsp                      ## imm = 0x238
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	retq
                                        ## -- End function
Lcrypto_block:                                 ## -- Begin function block
                                        ## @block
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	subq	$136, %rsp
	movabsq	$3684054920433006693, %rax      ## imm = 0x3320646E61707865
	movq	%rax, -112(%rbp)
	movabsq	$7719281312240119090, %rax      ## imm = 0x6B20657479622D32
	movq	%rax, -104(%rbp)
	pushq	$4
	popq	%rax
LBB1_1:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	$12, %rax
	je	LBB1_2
## %bb.14:                              ##   in Loop: Header=BB1_1 Depth=1
	movl	-16(%rsi,%rax,4), %r8d
	movl	%r8d, -112(%rbp,%rax,4)
	incq	%rax
	jmp	LBB1_1
LBB1_2:
	movl	%ecx, -64(%rbp)
	xorl	%eax, %eax
LBB1_3:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	$3, %rax
	je	LBB1_4
## %bb.15:                              ##   in Loop: Header=BB1_3 Depth=1
	movl	(%rdx,%rax,4), %ecx
	movl	%ecx, -60(%rbp,%rax,4)
	incq	%rax
	jmp	LBB1_3
LBB1_4:
	xorl	%eax, %eax
LBB1_5:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	$16, %rax
	je	LBB1_6
## %bb.16:                              ##   in Loop: Header=BB1_5 Depth=1
	movl	-112(%rbp,%rax,4), %ecx
	movl	%ecx, -176(%rbp,%rax,4)
	incq	%rax
	jmp	LBB1_5
LBB1_6:
	movq	%rdi, -48(%rbp)                 ## 8-byte Spill
	pushq	$10
	popq	%r14
	leaq	-176(%rbp), %r15
	pushq	$10
	popq	%r12
	pushq	$11
	popq	%rbx
	pushq	$15
	popq	%r13
LBB1_7:                                 ## =>This Inner Loop Header: Depth=1
	subl	$1, %r14d
	jb	LBB1_8
## %bb.17:                              ##   in Loop: Header=BB1_7 Depth=1
	movq	%r15, %rdi
	xorl	%esi, %esi
	pushq	$4
	popq	%rdx
	pushq	$8
	popq	%rcx
	pushq	$12
	popq	%r8
	callq	Lcrypto_qr
	movq	%r15, %rdi
	pushq	$1
	popq	%rsi
	pushq	$5
	popq	%rdx
	pushq	$9
	popq	%rcx
	pushq	$13
	popq	%r8
	callq	Lcrypto_qr
	movq	%r15, %rdi
	pushq	$2
	popq	%rsi
	pushq	$6
	popq	%rdx
	movl	%r12d, %ecx
	pushq	$14
	popq	%r8
	callq	Lcrypto_qr
	movq	%r15, %rdi
	pushq	$3
	popq	%rsi
	pushq	$7
	popq	%rdx
	movl	%ebx, %ecx
	movl	%r13d, %r8d
	callq	Lcrypto_qr
	movq	%r15, %rdi
	xorl	%esi, %esi
	pushq	$5
	popq	%rdx
	movl	%r12d, %ecx
	movl	%r13d, %r8d
	callq	Lcrypto_qr
	movq	%r15, %rdi
	pushq	$1
	popq	%rsi
	pushq	$6
	popq	%rdx
	movl	%ebx, %ecx
	pushq	$12
	popq	%r8
	callq	Lcrypto_qr
	movq	%r15, %rdi
	pushq	$2
	popq	%rsi
	pushq	$7
	popq	%rdx
	pushq	$8
	popq	%rcx
	pushq	$13
	popq	%r8
	callq	Lcrypto_qr
	movq	%r15, %rdi
	pushq	$3
	popq	%rsi
	pushq	$4
	popq	%rdx
	pushq	$9
	popq	%rcx
	pushq	$14
	popq	%r8
	callq	Lcrypto_qr
	jmp	LBB1_7
LBB1_8:
	xorl	%eax, %eax
	movq	-48(%rbp), %r8                  ## 8-byte Reload
LBB1_9:                                 ## =>This Loop Header: Depth=1
                                        ##     Child Loop BB1_11 Depth 2
	cmpq	$16, %rax
	je	LBB1_18
## %bb.10:                              ##   in Loop: Header=BB1_9 Depth=1
	movl	-112(%rbp,%rax,4), %edx
	addl	-176(%rbp,%rax,4), %edx
	xorl	%ecx, %ecx
	movq	%r8, %rsi
LBB1_11:                                ##   Parent Loop BB1_9 Depth=1
                                        ## =>  This Inner Loop Header: Depth=2
	cmpq	$32, %rcx
	je	LBB1_13
## %bb.12:                              ##   in Loop: Header=BB1_11 Depth=2
	movl	%edx, %edi
	shrl	%cl, %edi
	movb	%dil, (%rsi)
	incq	%rsi
	addq	$8, %rcx
	jmp	LBB1_11
LBB1_13:                                ##   in Loop: Header=BB1_9 Depth=1
	incq	%rax
	addq	$4, %r8
	jmp	LBB1_9
LBB1_18:
	leaq	-176(%rbp), %rdi
	pushq	$64
	popq	%rbx
	movq	%rbx, %rsi
	callq	Lcrypto_wipe
	leaq	-112(%rbp), %rdi
	movq	%rbx, %rsi
	callq	Lcrypto_wipe
	addq	$136, %rsp
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	retq
                                        ## -- End function
Lcrypto_cipher:                                ## -- Begin function cipher
                                        ## @cipher
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	pushq	%r15
	pushq	%r14
	pushq	%r13
	pushq	%r12
	pushq	%rbx
	subq	$72, %rsp
	movq	%rcx, -48(%rbp)                 ## 8-byte Spill
	movq	%rdx, %r14
	movq	%rsi, %rbx
	movq	%rdi, %r12
	xorl	%r13d, %r13d
	movq	%rsi, %r15
LBB2_1:                                 ## =>This Loop Header: Depth=1
                                        ##     Child Loop BB2_3 Depth 2
	cmpq	%rbx, %r13
	jae	LBB2_7
## %bb.2:                               ##   in Loop: Header=BB2_1 Depth=1
	movq	%r13, %rcx
	shrq	$6, %rcx
	incl	%ecx
	leaq	-112(%rbp), %rdi
	movq	%r14, %rsi
	movq	-48(%rbp), %rdx                 ## 8-byte Reload
                                        ## kill: def $ecx killed $ecx killed $rcx
	callq	Lcrypto_block
	xorl	%eax, %eax
LBB2_3:                                 ##   Parent Loop BB2_1 Depth=1
                                        ## =>  This Inner Loop Header: Depth=2
	cmpq	$64, %rax
	je	LBB2_5
## %bb.4:                               ##   in Loop: Header=BB2_3 Depth=2
	cmpq	%rax, %r15
	je	LBB2_5
## %bb.6:                               ##   in Loop: Header=BB2_3 Depth=2
	movb	-112(%rbp,%rax), %cl
	xorb	%cl, (%r12,%rax)
	incq	%rax
	jmp	LBB2_3
LBB2_5:                                 ##   in Loop: Header=BB2_1 Depth=1
	addq	$64, %r13
	addq	$-64, %r15
	addq	$64, %r12
	jmp	LBB2_1
LBB2_7:
	leaq	-112(%rbp), %rdi
	pushq	$64
	popq	%rsi
	callq	Lcrypto_wipe
	addq	$72, %rsp
	popq	%rbx
	popq	%r12
	popq	%r13
	popq	%r14
	popq	%r15
	popq	%rbp
	retq
                                        ## -- End function
Lcrypto_s64:                                   ## -- Begin function s64
                                        ## @s64
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	xorl	%ecx, %ecx
LBB3_1:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	$64, %rcx
	je	LBB3_2
## %bb.3:                               ##   in Loop: Header=BB3_1 Depth=1
	movq	%rsi, %rax
	shrq	%cl, %rax
	movb	%al, (%rdi)
	addq	$8, %rcx
	incq	%rdi
	jmp	LBB3_1
LBB3_2:
	popq	%rbp
	retq
                                        ## -- End function
Lcrypto_wipe:                                  ## -- Begin function wipe
                                        ## @wipe
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	xorl	%eax, %eax
LBB4_1:                                 ## =>This Inner Loop Header: Depth=1
	cmpq	%rax, %rsi
	je	LBB4_3
## %bb.2:                               ##   in Loop: Header=BB4_1 Depth=1
	movb	$0, (%rdi,%rax)
	incq	%rax
	jmp	LBB4_1
LBB4_3:
	popq	%rbp
	retq
                                        ## -- End function
Lcrypto_qr:                                    ## -- Begin function qr
                                        ## @qr
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	movl	%edx, %eax
	movl	(%rdi,%rax,4), %edx
	movl	%esi, %r9d
	movl	(%rdi,%r9,4), %esi
	addl	%edx, %esi
	movl	%r8d, %r8d
	movl	(%rdi,%r8,4), %r10d
	xorl	%esi, %r10d
	roll	$16, %r10d
	movl	%ecx, %ecx
	movl	(%rdi,%rcx,4), %r11d
	addl	%r10d, %r11d
	xorl	%r11d, %edx
	roll	$12, %edx
	addl	%edx, %esi
	movl	%esi, (%rdi,%r9,4)
	xorl	%r10d, %esi
	roll	$8, %esi
	movl	%esi, (%rdi,%r8,4)
	addl	%r11d, %esi
	movl	%esi, (%rdi,%rcx,4)
	xorl	%edx, %esi
	roll	$7, %esi
	movl	%esi, (%rdi,%rax,4)
	popq	%rbp
	retq
                                        ## -- End function
Lcrypto_addp:                                  ## -- Begin function addp
                                        ## @addp
## %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	movq	(%rsi), %rcx
	addq	(%rdi), %rcx
	movq	8(%rsi), %rax
	adcq	8(%rdi), %rax
	movq	16(%rsi), %rdx
	adcq	16(%rdi), %rdx
	movq	%rcx, %rsi
	subq	$-5, %rsi
	setb	%r8b
	movl	%r8d, %r9d
	xorb	$1, %r9b
	cmpq	$-1, %rax
	setne	%r10b
	orb	%r8b, %r10b
	movzbl	%r10b, %r8d
	andl	$1, %r8d
	movq	%rdx, %r10
	subq	%r8, %r10
	addq	$-3, %r10
	addq	$3, %r8
	cmpq	%r8, %rdx
	setae	%r8b
	cmovbq	%rcx, %rsi
	movq	%rsi, (%rdi)
	cmovbq	%rdx, %r10
	andb	%r9b, %r8b
	movzbl	%r8b, %ecx
	addq	%rcx, %rax
	movq	%rax, 8(%rdi)
	movq	%r10, 16(%rdi)
	popq	%rbp
	retq
                                        ## -- End function
