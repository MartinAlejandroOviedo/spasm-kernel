// SPDX-License-Identifier: GPL-2.0-only
#include <stdint.h>
#include <stdio.h>

extern int spasm_bin2bcd(int value);
extern uint64_t spasm_int_pow(uint64_t base, uint32_t exp);
extern unsigned long spasm_lcm(unsigned long a, unsigned long b);
extern unsigned long spasm_lcm_not_zero(unsigned long a, unsigned long b);

unsigned long gcd(unsigned long a, unsigned long b)
{
	while (b) {
		unsigned long remainder = a % b;
		a = b;
		b = remainder;
	}
	return a;
}

static unsigned char ref_bin2bcd(unsigned int value)
{
	const unsigned int tens = (value * 103) >> 10;
	return (unsigned char)((tens << 4) | (value - tens * 10));
}

static uint64_t ref_int_pow(uint64_t base, uint32_t exp)
{
	uint64_t result = 1;
	while (exp) {
		if (exp & 1)
			result *= base;
		exp >>= 1;
		base *= base;
	}
	return result;
}

static unsigned long ref_lcm(unsigned long a, unsigned long b)
{
	return a && b ? (a / gcd(a, b)) * b : 0;
}

int main(void)
{
	uint64_t state = UINT64_C(0x535041534d434152);
	unsigned int i;

	for (i = 0; i <= 99; i++) {
		if ((unsigned char)spasm_bin2bcd((int)i) != ref_bin2bcd(i)) {
			fprintf(stderr, "bin2bcd mismatch value=%u expected=%u actual=%u\n",
				i, ref_bin2bcd(i),
				(unsigned char)spasm_bin2bcd((int)i));
			return 1;
		}
	}
	for (i = 0; i < 100000; i++) {
		uint64_t base;
		uint32_t exp;
		unsigned long a;
		unsigned long b;
		unsigned long expected;

		state = state * UINT64_C(6364136223846793005) + 1;
		base = state;
		exp = (uint32_t)(state >> 58);
		if (spasm_int_pow(base, exp) != ref_int_pow(base, exp))
			return 2;
		state = state * UINT64_C(6364136223846793005) + 1;
		a = (unsigned long)(state & 0xfffff);
		state = state * UINT64_C(6364136223846793005) + 1;
		b = (unsigned long)(state & 0xfffff);
		expected = ref_lcm(a, b);
		if (spasm_lcm(a, b) != expected)
			return 3;
		if (spasm_lcm_not_zero(a, b) !=
		    (expected ? expected : (b ? b : a)))
			return 4;
	}
	puts("SpASM core equivalence: bin2bcd=100 int_pow=100000 lcm=100000 OK");
	return 0;
}
