/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(hex2bin)
	ENDBR
	jmp spasm_hex2bin
SYM_FUNC_END(hex2bin)
