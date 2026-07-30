// SPDX-License-Identifier: GPL-2.0-only
#include <stdio.h>

extern unsigned long spasm_care_level_v1(unsigned long cpu_pct,
					 unsigned long cpu_temp_c,
					 unsigned long ram_free_mb);

struct care_vector {
	unsigned long cpu_pct;
	unsigned long cpu_temp_c;
	unsigned long ram_free_mb;
	unsigned long expected;
};

int main(void)
{
	static const struct care_vector vectors[] = {
		{ 13, 49, 26000, 0 },
		{ 90, 60, 26000, 1 },
		{ 40, 76, 26000, 2 },
		{ 40, 60, 200, 2 },
		{ 90, 76, 26000, 3 },
		{ 40, 86, 26000, 3 },
		{ 40, 60, 100, 3 },
		{ 10, 95, 26000, 4 },
		{ 10, 40, 63, 4 },
	};
	unsigned int i;

	for (i = 0; i < sizeof(vectors) / sizeof(vectors[0]); i++) {
		unsigned long actual = spasm_care_level_v1(
			vectors[i].cpu_pct,
			vectors[i].cpu_temp_c,
			vectors[i].ram_free_mb);

		if (actual != vectors[i].expected) {
			fprintf(stderr,
				"vector %u: cpu=%lu temp=%lu ram=%lu expected=%lu actual=%lu\n",
				i, vectors[i].cpu_pct, vectors[i].cpu_temp_c,
				vectors[i].ram_free_mb, vectors[i].expected, actual);
			return 1;
		}
	}

	printf("Machine Care policy SpASM: %zu/9 vectors OK\n",
	       sizeof(vectors) / sizeof(vectors[0]));
	return 0;
}
