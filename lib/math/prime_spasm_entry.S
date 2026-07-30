/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/linkage.h>
#include <asm/ibt.h>

SYM_FUNC_START(slow_is_prime_number)
	ENDBR
	jmp spasm_slow_is_prime_number
SYM_FUNC_END(slow_is_prime_number)
