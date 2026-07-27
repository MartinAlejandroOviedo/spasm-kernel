/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(hex_to_bin)
	ENDBR
	jmp spasm_hex_to_bin
SYM_FUNC_END(hex_to_bin)
