// SPDX-License-Identifier: GPL-2.0-only
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>

extern unsigned long gcd(unsigned long a, unsigned long b);

static unsigned long reference_gcd(unsigned long a, unsigned long b)
{
	while (b) {
		unsigned long remainder = a % b;

		a = b;
		b = remainder;
	}
	return a;
}

static unsigned long linux_binary_gcd(unsigned long a, unsigned long b)
{
	unsigned long common;

	if (!a || !b)
		return a | b;
	common = (a | b) & -(a | b);
	b >>= __builtin_ctzl(b);
	for (;;) {
		a >>= __builtin_ctzl(a);
		if (a == b)
			return a * common;
		if (a < b) {
			unsigned long temporary = a;

			a = b;
			b = temporary;
		}
		a -= b;
	}
}

static uint64_t random_state = UINT64_C(0x4e6963654b65726e);

static uint64_t next_random(void)
{
	uint64_t value = random_state;

	value ^= value << 13;
	value ^= value >> 7;
	value ^= value << 17;
	random_state = value;
	return value;
}

static uint64_t monotonic_ns(void)
{
	struct timespec now;

	if (clock_gettime(CLOCK_MONOTONIC, &now))
		return 0;
	return (uint64_t)now.tv_sec * UINT64_C(1000000000) + now.tv_nsec;
}

int main(void)
{
	static const unsigned long vectors[][2] = {
		{ 0, 0 },
		{ 0, 25 },
		{ 25, 0 },
		{ 1071, 462 },
		{ 48, 18 },
		{ 17, 13 },
		{ ~0UL, 0 },
		{ ~0UL, ~0UL - 1 },
		{ 1UL << 63, 1UL << 62 },
		{ 7540113804746346429UL, 4660046610375530309UL },
	};
	const unsigned int random_cases = 250000;
	const unsigned int benchmark_cases = 1000000;
	volatile unsigned long sink = 0;
	uint64_t started;
	uint64_t spasm_ns;
	uint64_t reference_ns;
	uint64_t linux_ns;
	unsigned int index;

	for (index = 0; index < sizeof(vectors) / sizeof(vectors[0]); index++) {
		unsigned long a = vectors[index][0];
		unsigned long b = vectors[index][1];
		unsigned long expected = reference_gcd(a, b);
		unsigned long actual = gcd(a, b);

		if (actual != expected) {
			fprintf(stderr,
				"vector %u fallo: gcd(%lu, %lu)=%lu, esperado=%lu\n",
				index, a, b, actual, expected);
			return 1;
		}
	}

	for (index = 0; index < random_cases; index++) {
		unsigned long a = (unsigned long)next_random();
		unsigned long b = (unsigned long)next_random();
		unsigned long expected = reference_gcd(a, b);
		unsigned long actual = gcd(a, b);
		unsigned long linux_result = linux_binary_gcd(a, b);

		if (actual != expected || linux_result != expected) {
			fprintf(stderr,
				"aleatorio %u fallo: gcd(%lu, %lu)=%lu, "
				"Linux=%lu, esperado=%lu\n",
				index, a, b, actual, linux_result, expected);
			return 1;
		}
	}

	random_state = UINT64_C(0x4e6963654b65726e);
	started = monotonic_ns();
	for (index = 0; index < benchmark_cases; index++)
		sink ^= gcd((unsigned long)next_random(),
			    (unsigned long)next_random());
	spasm_ns = monotonic_ns() - started;

	random_state = UINT64_C(0x4e6963654b65726e);
	started = monotonic_ns();
	for (index = 0; index < benchmark_cases; index++)
		sink ^= reference_gcd((unsigned long)next_random(),
				      (unsigned long)next_random());
	reference_ns = monotonic_ns() - started;

	random_state = UINT64_C(0x4e6963654b65726e);
	started = monotonic_ns();
	for (index = 0; index < benchmark_cases; index++)
		sink ^= linux_binary_gcd((unsigned long)next_random(),
					 (unsigned long)next_random());
	linux_ns = monotonic_ns() - started;

	printf("gcd SpASM: vectores=%zu aleatorios=%u resultado=OK\n",
	       sizeof(vectors) / sizeof(vectors[0]), random_cases);
	printf("benchmark: SpASM=%" PRIu64 " ns referencia=%" PRIu64
	       " ns Linux-binario=%" PRIu64 " ns llamadas=%u sink=%lu\n",
	       spasm_ns, reference_ns, linux_ns, benchmark_cases, sink);
	return 0;
}
