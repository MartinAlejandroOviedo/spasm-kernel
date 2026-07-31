# SPDX-License-Identifier: GPL-2.0-only
obj-y += div64.o int_log.o reciprocal_div.o

obj-$(CONFIG_SPASM_KERNEL_INT_POW_C) += int_pow.o
obj-$(CONFIG_SPASM_KERNEL_INT_POW_SPASM) += int_pow_spasm.o int_pow_spasm_entry.o int_pow_export.o
obj-$(CONFIG_SPASM_KERNEL_INT_POW_DUAL) += int_pow.o int_pow_spasm.o int_pow_dual.o

obj-$(CONFIG_SPASM_KERNEL_GCD_C) += gcd.o
obj-$(CONFIG_SPASM_KERNEL_GCD_SPASM) += gcd_spasm.o gcd_spasm_entry.o gcd_export.o
obj-$(CONFIG_SPASM_KERNEL_GCD_DUAL) += gcd.o gcd_spasm.o gcd_dual.o

obj-$(CONFIG_SPASM_KERNEL_INT_SQRT_C) += int_sqrt.o
obj-$(CONFIG_SPASM_KERNEL_INT_SQRT_SPASM) += int_sqrt_spasm.o int_sqrt_spasm_entry.o int_sqrt_export.o
obj-$(CONFIG_SPASM_KERNEL_INT_SQRT_DUAL) += int_sqrt.o int_sqrt_spasm.o int_sqrt_dual.o

obj-$(CONFIG_SPASM_KERNEL_LCM_SPASM) += lcm_spasm.o lcm_spasm_entry.o lcm_not_zero_spasm_entry.o lcm_export.o lcm_not_zero_export.o
obj-$(CONFIG_SPASM_KERNEL_LCM_DUAL) += lcm.o lcm_spasm.o lcm_dual.o
obj-$(CONFIG_SPASM_KERNEL_LCM_C) += lcm.o

obj-$(CONFIG_CORDIC)		+= cordic.o
obj-$(CONFIG_PRIME_NUMBERS)	+= prime_numbers.o
obj-$(CONFIG_RATIONAL)		+= rational.o

obj-$(CONFIG_TEST_DIV64)	+= test_div64.o
obj-$(CONFIG_TEST_MULDIV64)	+= test_mul_u64_u64_div_u64.o

obj-y += tests/
obj-$(CONFIG_SPASM_KERNEL_INTLOG2_SPASM) += intlog2_spasm.o intlog2_spasm_entry.o intlog2_export.o
obj-$(CONFIG_SPASM_KERNEL_INTLOG2_DUAL) += intlog2_spasm.o intlog2_dual.o
obj-$(CONFIG_SPASM_KERNEL_INTLOG10_SPASM) += intlog10_spasm.o intlog10_spasm_entry.o intlog10_export.o
obj-$(CONFIG_SPASM_KERNEL_INTLOG10_DUAL) += intlog10_spasm.o intlog10_dual.o
