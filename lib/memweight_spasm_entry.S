/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(memweight)
	ENDBR
	jmp spasm_memweight
SYM_FUNC_END(memweight)
