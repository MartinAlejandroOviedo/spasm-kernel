// SPDX-License-Identifier: GPL-2.0-only
#include <linux/kernel.h>
#include <linux/export.h>
#include <linux/string.h>

extern typeof(sysfs_streq) spasm_sysfs_streq;
extern typeof(sysfs_streq) spasm_sysfs_streq_c;

typeof(sysfs_streq) sysfs_streq
{
	typeof(sysfs_streq) spasm_result = spasm_sysfs_streq;
	return spasm_result;
}
EXPORT_SYMBOL(sysfs_streq);
