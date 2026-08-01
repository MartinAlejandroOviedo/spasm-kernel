/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc_t10dif)
	ENDBR
	jmp spasm_crc_t10dif
SYM_FUNC_END(crc_t10dif)
