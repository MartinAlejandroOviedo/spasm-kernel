/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(skip_spaces)
	ENDBR
	jmp spasm_skip_spaces
SYM_FUNC_END(skip_spaces)
