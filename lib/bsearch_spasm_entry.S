/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(bsearch)
	ENDBR
	jmp spasm_bsearch
SYM_FUNC_END(bsearch)
