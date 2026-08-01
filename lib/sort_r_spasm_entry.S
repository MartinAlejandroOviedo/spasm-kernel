/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(sort_r)
	ENDBR
	jmp spasm_sort_r
SYM_FUNC_END(sort_r)
