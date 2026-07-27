# SPDX-License-Identifier: GPL-2.0-only
obj-y += div64.o lcm.o int_log.o int_pow.o int_sqrt.o reciprocal_div.o

obj-$(CONFIG_NICE_KERNEL_GCD_C) += gcd.o
obj-$(CONFIG_NICE_KERNEL_SPASM_GCD) += gcd_spasm.o gcd_spasm_entry.o gcd_export.o
obj-$(CONFIG_NICE_KERNEL_GCD_DUAL) += gcd.o gcd_spasm.o gcd_dual.o

obj-$(CONFIG_CORDIC)		+= cordic.o
obj-$(CONFIG_PRIME_NUMBERS)	+= prime_numbers.o
obj-$(CONFIG_RATIONAL)		+= rational.o

obj-$(CONFIG_TEST_DIV64)	+= test_div64.o
obj-$(CONFIG_TEST_MULDIV64)	+= test_mul_u64_u64_div_u64.o

obj-y += tests/
