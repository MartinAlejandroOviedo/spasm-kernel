// SPDX-License-Identifier: GPL-2.0-only
#include <linux/atomic.h>
#include <linux/export.h>
#include <linux/math.h>
#include <linux/printk.h>

#include "int_pow_spasm.h"

static atomic64_t spasm_int_pow_dual_calls = ATOMIC64_INIT(0);
static atomic64_t spasm_int_pow_dual_mismatches = ATOMIC64_INIT(0);

u64 int_pow(u64 base, unsigned int exp)
{
	u64 c_result = spasm_int_pow_c(base, exp);
	u64 spasm_result = spasm_int_pow(base, exp);

	atomic64_inc(&spasm_int_pow_dual_calls);
	if (unlikely(c_result != spasm_result)) {
		atomic64_inc(&spasm_int_pow_dual_mismatches);
		pr_err_ratelimited("spasm-kernel: %s mismatch base=%llu exp=%u C=%llu SpASM=%llu calls=%lld mismatches=%lld\n",
				   __func__, base, exp, c_result, spasm_result,
				   atomic64_read(&spasm_int_pow_dual_calls),
				   atomic64_read(&spasm_int_pow_dual_mismatches));
	}

	return spasm_result;
}
EXPORT_SYMBOL_GPL(int_pow);
