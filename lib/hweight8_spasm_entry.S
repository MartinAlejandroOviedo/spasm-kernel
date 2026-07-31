/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(__sw_hweight8)
	ENDBR
	jmp spasm_hweight8
SYM_FUNC_END(__sw_hweight8)
