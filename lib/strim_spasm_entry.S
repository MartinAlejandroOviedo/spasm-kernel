/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(strim)
	ENDBR
	jmp spasm_strim
SYM_FUNC_END(strim)
