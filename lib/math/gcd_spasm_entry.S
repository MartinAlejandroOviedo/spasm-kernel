/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

/*
 * Preserve Linux's public symbol while keeping one reusable SpASM core for
 * both direct and dual-comparison builds.
 */
SYM_FUNC_START(gcd)
	ENDBR
	jmp spasm_gcd
SYM_FUNC_END(gcd)
