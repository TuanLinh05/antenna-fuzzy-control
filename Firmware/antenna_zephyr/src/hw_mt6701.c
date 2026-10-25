/*
 * MT6701 (MagnTek, Rev.1.8): default 7-bit slave address 0x06.
 * Reg 0x03 = Angle[13:6], reg 0x04 bits 7..2 = Angle[5:0]; read 0x03 first.
 * angle = raw / 16384 * 360 deg. I2C clock up to 1 MHz; 400 kHz is used.
 */
#include "hw_mt6701.h"

#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>

#define MT6701_ADDR      0x06
#define MT6701_REG_ANGLE 0x03

static const struct device *const bus = DEVICE_DT_GET(DT_NODELABEL(i2c2));

int hw_mt6701_init(void)
{
	return device_is_ready(bus) ? 0 : -ENODEV;
}

int hw_mt6701_read(uint16_t *raw)
{
	uint8_t b[2];
	int rc;

#ifdef CONFIG_ANTENNA_MT6701_SINGLE_READS
	rc = i2c_reg_read_byte(bus, MT6701_ADDR, MT6701_REG_ANGLE, &b[0]);
	if (rc == 0) {
		rc = i2c_reg_read_byte(bus, MT6701_ADDR, MT6701_REG_ANGLE + 1, &b[1]);
	}
#else
	rc = i2c_burst_read(bus, MT6701_ADDR, MT6701_REG_ANGLE, b, sizeof(b));
#endif
	if (rc != 0) {
		return rc;
	}
	*raw = (uint16_t)(((uint16_t)b[0] << 6) | (b[1] >> 2));
	return 0;
}

int hw_mt6701_recover(void)
{
	return i2c_recover_bus(bus);
}
