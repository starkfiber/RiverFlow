.text
.code16
 pushw %ds
 pushw %es
 int $0x12
 nop
 movw %ax,%bx
 xorw %ax,%ax
 movw %ax,%ds
 movw %ax,%es
 movw %bx,0x6f0
 cmpw $512,%bx
 jb Lbios_memory_fail
 popw %es
 popw %ds
 jmp Lbios_memory_done
Lbios_memory_fail:
 movw $0xf4,%dx
 movb $38,%al
 outb %al,%dx
 cli
Lbios_memory_halt:
 hlt
 jmp Lbios_memory_halt
Lbios_memory_done:
