// SPDX-License-Identifier: GPL-2.0-only
#include <linux/kernel.h>
#include <linux/export.h>
#include <linux/string.h>

extern typeof(skip_spaces) spasm_skip_spaces;
extern typeof(skip_spaces) spasm_skip_spaces_c;

typeof(skip_spaces) skip_spaces
{
	typeof(skip_spaces) spasm_result = spasm_skip_spaces;
	return spasm_result;
}
EXPORT_SYMBOL(skip_spaces);
