.text
.code16
 cli
 xorw %ax,%ax
 movw %ax,%ds
 movw %ax,%es
 movw %ax,%ss
 movw $0x7c00,%sp
 movw $0x8000,%bx
 movw $0x0211,%ax
 movw $2,%cx
 xorb %dh,%dh
 int $0x13
 jc Lboot_fail
 movw $0xa200,%bx
 movw $0x0212,%ax
 movw $1,%cx
 movb $1,%dh
 int $0x13
 jc Lboot_fail
 movw $0xc600,%bx
 movw $0x0212,%ax
 movw $0x0101,%cx
 xorb %dh,%dh
 int $0x13
 jc Lboot_fail
 movw $0xea00,%bx
 movw $0x020a,%ax
 movw $0x0101,%cx
 movb $1,%dh
 int $0x13
 jc Lboot_fail
 .byte 0xea
 .word 0x8000
 .word 0
Lboot_fail:
 movb $38,%al
 movw $0xf4,%dx
 outb %al,%dx
 cli
Lboot_halt:
 hlt
 jmp Lboot_halt
