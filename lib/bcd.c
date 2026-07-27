// SPDX-License-Identifier: GPL-2.0
#include <linux/bcd.h>
#include <linux/export.h>

#include "bcd_spasm.h"

#ifdef CONFIG_SPASM_KERNEL_BCD_SPASM
unsigned __attribute__((weak)) _bcd2bin(unsigned char val)
#elif defined(CONFIG_SPASM_KERNEL_BCD_DUAL)
#define _bcd2bin spasm_bcd2bin_c
unsigned _bcd2bin(unsigned char val)
#else
unsigned _bcd2bin(unsigned char val)
#endif
{
	return (val & 0x0f) + (val >> 4) * 10;
}
#if !defined(CONFIG_SPASM_KERNEL_BCD_SPASM) && !defined(CONFIG_SPASM_KERNEL_BCD_DUAL)
EXPORT_SYMBOL(_bcd2bin);
#endif

unsigned char _bin2bcd(unsigned val)
{
	const unsigned int t = (val * 103) >> 10;

	return (t << 4) | (val - t * 10);
}
EXPORT_SYMBOL(_bin2bcd);
