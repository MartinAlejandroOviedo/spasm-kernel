/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef _LIB_BCD_SPASM_H
#define _LIB_BCD_SPASM_H

unsigned spasm_bcd2bin_c(unsigned char val);
unsigned spasm_bcd2bin(unsigned char val);
unsigned char spasm_bin2bcd_c(unsigned val);
unsigned char spasm_bin2bcd(unsigned val);

#endif
