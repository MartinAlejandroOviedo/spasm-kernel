/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc32_be)
	ENDBR
	jmp spasm_crc32_be
SYM_FUNC_END(crc32_be)
