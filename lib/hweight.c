// SPDX-License-Identifier: GPL-2.0
#include <linux/export.h>
#include <linux/bitops.h>
#include <asm/types.h>

#if defined(CONFIG_SPASM_KERNEL_HWEIGHT8_DUAL)
#define __sw_hweight8 spasm_hweight8_c
#endif

#if defined(CONFIG_SPASM_KERNEL_HWEIGHT16_DUAL)
#define __sw_hweight16 spasm_hweight16_c
#endif

/**
 * DOC: __sw_hweightN - returns the hamming weight of a N-bit word
 * @w: the word to weigh
 *
 * The Hamming Weight of a number is the total number of bits set in it.
 */

#ifndef CONFIG_SPASM_KERNEL_HWEIGHT8_SPASM
#ifdef CONFIG_SPASM_KERNEL_HWEIGHT32_SPASM
unsigned int __attribute__((weak)) __sw_hweight32(unsigned int w)
#elif defined(CONFIG_SPASM_KERNEL_HWEIGHT32_DUAL)
#define __sw_hweight32 spasm_hweight32_c
unsigned int __sw_hweight32(unsigned int w)
#else
unsigned int __sw_hweight32(unsigned int w)
#endif
{
#ifdef CONFIG_ARCH_HAS_FAST_MULTIPLIER
	w -= (w >> 1) & 0x55555555;
	w =  (w & 0x33333333) + ((w >> 2) & 0x33333333);
	w =  (w + (w >> 4)) & 0x0f0f0f0f;
	return (w * 0x01010101) >> 24;
#else
	unsigned int res = w - ((w >> 1) & 0x55555555);
	res = (res & 0x33333333) + ((res >> 2) & 0x33333333);
	res = (res + (res >> 4)) & 0x0F0F0F0F;
	res = res + (res >> 8);
	return (res + (res >> 16)) & 0x000000FF;
#endif
}
#if !defined(CONFIG_SPASM_KERNEL_HWEIGHT32_SPASM) && !defined(CONFIG_SPASM_KERNEL_HWEIGHT32_DUAL)
EXPORT_SYMBOL(__sw_hweight32);
#endif

#ifndef CONFIG_SPASM_KERNEL_HWEIGHT16_SPASM
unsigned int __sw_hweight16(unsigned int w)
{
	unsigned int res = w - ((w >> 1) & 0x5555);
	res = (res & 0x3333) + ((res >> 2) & 0x3333);
	res = (res + (res >> 4)) & 0x0F0F;
	return (res + (res >> 8)) & 0x00FF;
}
#endif
#if !defined(CONFIG_SPASM_KERNEL_HWEIGHT16_SPASM)
EXPORT_SYMBOL(__sw_hweight16);
#endif

#ifndef CONFIG_SPASM_KERNEL_HWEIGHT8_SPASM
unsigned int __sw_hweight8(unsigned int w)
{
	unsigned int res = w - ((w >> 1) & 0x55);
	res = (res & 0x33) + ((res >> 2) & 0x33);
	return (res + (res >> 4)) & 0x0F;
}
#endif
#if !defined(CONFIG_SPASM_KERNEL_HWEIGHT8_SPASM)
EXPORT_SYMBOL(__sw_hweight8);
#endif

#ifdef CONFIG_SPASM_KERNEL_HWEIGHT64_SPASM
unsigned long __attribute__((weak)) __sw_hweight64(__u64 w)
#elif defined(CONFIG_SPASM_KERNEL_HWEIGHT64_DUAL)
#define __sw_hweight64 spasm_hweight64_c
unsigned long __sw_hweight64(__u64 w)
#else
unsigned long __sw_hweight64(__u64 w)
#endif
{
#if BITS_PER_LONG == 32
	return __sw_hweight32((unsigned int)(w >> 32)) +
	       __sw_hweight32((unsigned int)w);
#elif BITS_PER_LONG == 64
#ifdef CONFIG_ARCH_HAS_FAST_MULTIPLIER
	w -= (w >> 1) & 0x5555555555555555ul;
	w =  (w & 0x3333333333333333ul) + ((w >> 2) & 0x3333333333333333ul);
	w =  (w + (w >> 4)) & 0x0f0f0f0f0f0f0f0ful;
	return (w * 0x0101010101010101ul) >> 56;
#else
	__u64 res = w - ((w >> 1) & 0x5555555555555555ul);
	res = (res & 0x3333333333333333ul) + ((res >> 2) & 0x3333333333333333ul);
	res = (res + (res >> 4)) & 0x0F0F0F0F0F0F0F0Ful;
	res = res + (res >> 8);
	res = res + (res >> 16);
	return (res + (res >> 32)) & 0x00000000000000FFul;
#endif
#endif
}
#if !defined(CONFIG_SPASM_KERNEL_HWEIGHT64_SPASM) && !defined(CONFIG_SPASM_KERNEL_HWEIGHT64_DUAL)
EXPORT_SYMBOL(__sw_hweight64);
#endif
