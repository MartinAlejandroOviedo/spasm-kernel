/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(sysfs_streq)
	ENDBR
	jmp spasm_sysfs_streq
SYM_FUNC_END(sysfs_streq)
