// SPDX-License-Identifier: GPL-2.0
/*
 * An integer based power function
 *
 * Derived from drivers/video/backlight/pwm_bl.c
 */

#include <linux/export.h>
#include <linux/math.h>
#include <linux/types.h>

#include "int_pow_spasm.h"

#ifdef CONFIG_SPASM_KERNEL_INT_POW_DUAL
#define int_pow spasm_int_pow_c
#endif

/**
 * int_pow - computes the exponentiation of the given base and exponent
 * @base: base which will be raised to the given power
 * @exp: power to be raised to
 *
 * Computes: pow(base, exp), i.e. @base raised to the @exp power
 */
u64 int_pow(u64 base, unsigned int exp)
{
	u64 result = 1;

	while (exp) {
		if (exp & 1)
			result *= base;
		exp >>= 1;
		base *= base;
	}

	return result;
}
#ifndef CONFIG_SPASM_KERNEL_INT_POW_DUAL
EXPORT_SYMBOL_GPL(int_pow);
#endif
