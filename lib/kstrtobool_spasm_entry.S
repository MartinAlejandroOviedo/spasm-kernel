/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(kstrtobool)
	ENDBR
	jmp spasm_kstrtobool
SYM_FUNC_END(kstrtobool)
