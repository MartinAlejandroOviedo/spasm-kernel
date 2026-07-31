/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc_ccitt)
	ENDBR
	jmp spasm_crc_ccitt
SYM_FUNC_END(crc_ccitt)
