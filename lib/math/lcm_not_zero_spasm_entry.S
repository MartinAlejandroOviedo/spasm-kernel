/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(lcm_not_zero)
	ENDBR
	jmp spasm_lcm_not_zero
SYM_FUNC_END(lcm_not_zero)
