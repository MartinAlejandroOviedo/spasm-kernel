/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(crc64_nvme)
	ENDBR
	jmp spasm_crc64_nvme
SYM_FUNC_END(crc64_nvme)
