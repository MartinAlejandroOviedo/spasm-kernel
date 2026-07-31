/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc_itu_t)
	ENDBR
	jmp spasm_crc_itu_t
SYM_FUNC_END(crc_itu_t)
