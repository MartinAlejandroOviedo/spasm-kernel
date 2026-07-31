// SPDX-License-Identifier: GPL-2.0-only
#include <linux/kernel.h>
#include <linux/export.h>
#include <linux/string.h>

extern typeof(strreplace) spasm_strreplace;
extern typeof(strreplace) spasm_strreplace_c;

typeof(strreplace) strreplace
{
	typeof(strreplace) spasm_result = spasm_strreplace;
	return spasm_result;
}
EXPORT_SYMBOL(strreplace);
