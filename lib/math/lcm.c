// SPDX-License-Identifier: GPL-2.0-only
#include <linux/compiler.h>
#include <linux/gcd.h>
#include <linux/export.h>
#include <linux/lcm.h>

#include "lcm_spasm.h"

/* Lowest common multiple */
#ifdef CONFIG_SPASM_KERNEL_LCM_SPASM
unsigned long __attribute__((weak)) lcm(unsigned long a, unsigned long b)
#elif defined(CONFIG_SPASM_KERNEL_LCM_DUAL)
#define lcm spasm_lcm_c
unsigned long lcm(unsigned long a, unsigned long b)
#else
unsigned long lcm(unsigned long a, unsigned long b)
#endif
{
	if (a && b)
		return (a / gcd(a, b)) * b;
	else
		return 0;
}
#if !defined(CONFIG_SPASM_KERNEL_LCM_SPASM) && !defined(CONFIG_SPASM_KERNEL_LCM_DUAL)
EXPORT_SYMBOL_GPL(lcm);
#endif

#ifdef CONFIG_SPASM_KERNEL_LCM_SPASM
unsigned long __attribute__((weak)) lcm_not_zero(unsigned long a, unsigned long b)
#else
unsigned long lcm_not_zero(unsigned long a, unsigned long b)
#endif
{
	unsigned long l = lcm(a, b);

	if (l)
		return l;

	return (b ? : a);
}
#if !defined(CONFIG_SPASM_KERNEL_LCM_SPASM)
EXPORT_SYMBOL_GPL(lcm_not_zero);
#endif
