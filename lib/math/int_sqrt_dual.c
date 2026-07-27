// SPDX-License-Identifier: GPL-2.0-only
#include <linux/atomic.h>
#include <linux/export.h>
#include <linux/math.h>
#include <linux/printk.h>

#include "int_sqrt_nice.h"

static atomic64_t nice_int_sqrt_dual_calls = ATOMIC64_INIT(0);
static atomic64_t nice_int_sqrt_dual_mismatches = ATOMIC64_INIT(0);

unsigned long int_sqrt(unsigned long x)
{
	unsigned long c_result = nice_int_sqrt_c(x);
	unsigned long spasm_result = nice_int_sqrt_spasm(x);

	atomic64_inc(&nice_int_sqrt_dual_calls);
	if (unlikely(c_result != spasm_result)) {
		atomic64_inc(&nice_int_sqrt_dual_mismatches);
		pr_err_ratelimited("nice-kernel: %s mismatch x=%lu C=%lu SpASM=%lu calls=%lld mismatches=%lld\n",
				   __func__, x, c_result, spasm_result,
				   atomic64_read(&nice_int_sqrt_dual_calls),
				   atomic64_read(&nice_int_sqrt_dual_mismatches));
	}

	return spasm_result;
}
EXPORT_SYMBOL_GPL(int_sqrt);
