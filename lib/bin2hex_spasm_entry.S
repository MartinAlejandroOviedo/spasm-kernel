/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(bin2hex)
	ENDBR
	jmp spasm_bin2hex
SYM_FUNC_END(bin2hex)
