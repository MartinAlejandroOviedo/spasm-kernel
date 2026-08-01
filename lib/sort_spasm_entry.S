/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(sort)
	ENDBR
	jmp spasm_sort
SYM_FUNC_END(sort)
