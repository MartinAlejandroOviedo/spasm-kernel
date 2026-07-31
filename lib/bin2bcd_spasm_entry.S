/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(_bin2bcd)
	ENDBR
	jmp spasm_bin2bcd
SYM_FUNC_END(_bin2bcd)
