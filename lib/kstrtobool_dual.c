// SPDX-License-Identifier: GPL-2.0-only
#include <linux/kernel.h>
#include <linux/export.h>
#include <linux/kstrtox.h>

extern typeof(kstrtobool) spasm_kstrtobool;
extern typeof(kstrtobool) spasm_kstrtobool_c;

typeof(kstrtobool) kstrtobool
{
	typeof(kstrtobool) spasm_result = spasm_kstrtobool;
	return spasm_result;
}
EXPORT_SYMBOL(kstrtobool);
