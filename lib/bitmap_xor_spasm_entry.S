/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(__bitmap_xor)
	ENDBR
	jmp spasm_bitmap_xor
SYM_FUNC_END(__bitmap_xor)
