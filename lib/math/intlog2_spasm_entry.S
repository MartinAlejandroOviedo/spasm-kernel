/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(intlog2)
	ENDBR
	jmp spasm_intlog2
SYM_FUNC_END(intlog2)
