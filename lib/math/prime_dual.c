// SPDX-License-Identifier: GPL-2.0-only
#include <linux/atomic.h>
#include <linux/export.h>
#include <linux/printk.h>
#include <linux/prime_numbers.h>

#include "prime_spasm.h"

static atomic64_t spasm_prime_dual_calls = ATOMIC64_INIT(0);
static atomic64_t spasm_prime_dual_mismatches = ATOMIC64_INIT(0);

bool slow_is_prime_number(unsigned long x)
{
	bool c_result = spasm_slow_is_prime_number_c(x);
	bool spasm_result = spasm_slow_is_prime_number(x);

	atomic64_inc(&spasm_prime_dual_calls);
	if (c_result != spasm_result) {
		atomic64_inc(&spasm_prime_dual_mismatches);
		pr_err_ratelimited("spasm-kernel: %s mismatch x=%lu C=%d SpASM=%d calls=%lld mismatches=%lld\n",
				   __func__, x, c_result, spasm_result,
				   atomic64_read(&spasm_prime_dual_calls),
				   atomic64_read(&spasm_prime_dual_mismatches));
	}

	return spasm_result;
}
EXPORT_SYMBOL_GPL(slow_is_prime_number);
