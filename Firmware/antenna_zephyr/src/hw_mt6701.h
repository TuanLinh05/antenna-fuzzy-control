/* MT6701 magnetic angle sensor on I2C2 (address 0x06, angle in 0x03/0x04). */
#ifndef HW_MT6701_H
#define HW_MT6701_H

#include <stdint.h>

int hw_mt6701_init(void);
/* 14-bit absolute angle; returns 0 or a negative errno. */
int hw_mt6701_read(uint16_t *raw);
/* Toggle SCL to free a stuck bus after repeated errors. */
int hw_mt6701_recover(void);

#endif
