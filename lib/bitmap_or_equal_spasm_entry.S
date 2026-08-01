/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(__bitmap_or_equal)
	ENDBR
	jmp spasm_bitmap_or_equal
SYM_FUNC_END(__bitmap_or_equal)
