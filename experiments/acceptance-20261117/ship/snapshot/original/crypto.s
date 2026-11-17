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
