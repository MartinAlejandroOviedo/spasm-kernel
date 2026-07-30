/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(lcm)
	ENDBR
	jmp spasm_lcm
SYM_FUNC_END(lcm)
