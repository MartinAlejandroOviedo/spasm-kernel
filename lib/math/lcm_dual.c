// SPDX-License-Identifier: GPL-2.0-only
#include <linux/atomic.h>
#include <linux/export.h>
#include <linux/gcd.h>
#include <linux/lcm.h>
#include <linux/printk.h>

#include "lcm_spasm.h"

static atomic64_t spasm_lcm_dual_calls = ATOMIC64_INIT(0);
static atomic64_t spasm_lcm_dual_mismatches = ATOMIC64_INIT(0);

unsigned long lcm(unsigned long a, unsigned long b)
{
	unsigned long c_result = spasm_lcm_c(a, b);
	unsigned long spasm_result = spasm_lcm(a, b);

	atomic64_inc(&spasm_lcm_dual_calls);
	if (unlikely(c_result != spasm_result)) {
		atomic64_inc(&spasm_lcm_dual_mismatches);
		pr_err_ratelimited("spasm-kernel: %s mismatch a=%lu b=%lu C=%lu SpASM=%lu calls=%lld mismatches=%lld\n",
				   __func__, a, b, c_result, spasm_result,
				   atomic64_read(&spasm_lcm_dual_calls),
				   atomic64_read(&spasm_lcm_dual_mismatches));
	}

	return spasm_result;
}
EXPORT_SYMBOL_GPL(lcm);
