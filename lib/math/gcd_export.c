// SPDX-License-Identifier: GPL-2.0-only
#include <linux/gcd.h>
#include <linux/export.h>

/*
 * Keep Linux's exported-symbol contract separate from the implementation.
 * With CONFIG_SPASM_KERNEL_SPASM_GCD=y, gcd is a transparent assembly entry
 * that tail-calls the SpASM implementation.
 */
EXPORT_SYMBOL_GPL(gcd);
