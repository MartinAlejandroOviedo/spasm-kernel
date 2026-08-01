/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc64_be)
	ENDBR
	jmp spasm_crc64_be
SYM_FUNC_END(crc64_be)
