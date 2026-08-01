/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(__bitmap_clear)
	ENDBR
	jmp spasm_bitmap_clear
SYM_FUNC_END(__bitmap_clear)
