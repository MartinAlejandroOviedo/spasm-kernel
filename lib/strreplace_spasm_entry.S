/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(strreplace)
	ENDBR
	jmp spasm_strreplace
SYM_FUNC_END(strreplace)
