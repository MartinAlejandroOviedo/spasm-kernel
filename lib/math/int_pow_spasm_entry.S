/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(int_pow)
	ENDBR
	movl %esi, %esi
	jmp spasm_int_pow
SYM_FUNC_END(int_pow)
