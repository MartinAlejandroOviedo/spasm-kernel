// SPDX-License-Identifier: GPL-2.0-only
#include <linux/atomic.h>
#include <linux/bcd.h>
#include <linux/export.h>
#include <linux/printk.h>

#include "bcd_spasm.h"

static atomic64_t spasm_bcd_dual_calls = ATOMIC64_INIT(0);
static atomic64_t spasm_bcd_dual_mismatches = ATOMIC64_INIT(0);

unsigned _bcd2bin(unsigned char val)
{
	unsigned c_result = spasm_bcd2bin_c(val);
	unsigned spasm_result = spasm_bcd2bin(val);

	atomic64_inc(&spasm_bcd_dual_calls);
	if (unlikely(c_result != spasm_result)) {
		atomic64_inc(&spasm_bcd_dual_mismatches);
		pr_err_ratelimited("spasm-kernel: %s mismatch val=%u C=%u SpASM=%u calls=%lld mismatches=%lld\n",
				   __func__, val, c_result, spasm_result,
				   atomic64_read(&spasm_bcd_dual_calls),
				   atomic64_read(&spasm_bcd_dual_mismatches));
	}

	return spasm_result;
}
EXPORT_SYMBOL(_bcd2bin);
