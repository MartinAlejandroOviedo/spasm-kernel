// SPDX-License-Identifier: GPL-2.0-only
//
// Dual C/SpASM comparison for __sw_hweight16.

#include <linux/kernel.h>
#include <linux/export.h>

extern unsigned int spasm_hweight16(unsigned int w);
extern unsigned int spasm_hweight16_c(unsigned int w);

unsigned int __sw_hweight16(unsigned int w)
{
	unsigned int c_result = spasm_hweight16_c(w);
	unsigned int spasm_result = spasm_hweight16(w);

	if (c_result != spasm_result)
		pr_err("__sw_hweight16 divergence: C=%u SpASM=%u for w=%u\n",
		       c_result, spasm_result, w);

	return spasm_result;
}
EXPORT_SYMBOL(__sw_hweight16);
