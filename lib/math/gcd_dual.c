// SPDX-License-Identifier: GPL-2.0-only
#include <linux/atomic.h>
#include <linux/export.h>
#include <linux/gcd.h>
#include <linux/printk.h>

#include "gcd_spasm.h"

static atomic64_t spasm_gcd_dual_calls = ATOMIC64_INIT(0);
static atomic64_t spasm_gcd_dual_mismatches = ATOMIC64_INIT(0);

/**
 * gcd - compare the C reference and SpASM candidate
 * @a: first value
 * @b: second value
 *
 * The candidate result is authoritative in dual mode. A mismatch is visible,
 * rate limited and counted without changing Linux's public ABI.
 */
unsigned long gcd(unsigned long a, unsigned long b)
{
	unsigned long c_result = spasm_gcd_c(a, b);
	unsigned long spasm_result = spasm_gcd(a, b);

	atomic64_inc(&spasm_gcd_dual_calls);
	if (unlikely(c_result != spasm_result)) {
		atomic64_inc(&spasm_gcd_dual_mismatches);
		pr_err_ratelimited("spasm-kernel: %s mismatch a=%lu b=%lu C=%lu SpASM=%lu calls=%lld mismatches=%lld\n",
				   __func__, a, b, c_result, spasm_result,
				   atomic64_read(&spasm_gcd_dual_calls),
				   atomic64_read(&spasm_gcd_dual_mismatches));
	}

	return spasm_result;
}
EXPORT_SYMBOL_GPL(gcd);
