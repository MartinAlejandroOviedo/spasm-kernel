/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc32c)
	ENDBR
	jmp spasm_crc32c
SYM_FUNC_END(crc32c)
