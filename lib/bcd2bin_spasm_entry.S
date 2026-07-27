/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(_bcd2bin)
	ENDBR
	jmp spasm_bcd2bin
SYM_FUNC_END(_bcd2bin)
