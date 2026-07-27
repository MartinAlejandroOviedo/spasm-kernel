/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(int_sqrt)
	ENDBR
	jmp spasm_int_sqrt
SYM_FUNC_END(int_sqrt)
