/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc16)
	ENDBR
	jmp spasm_crc16
SYM_FUNC_END(crc16)
