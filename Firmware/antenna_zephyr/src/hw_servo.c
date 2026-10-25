#include "hw_servo.h"

#include <zephyr/drivers/pwm.h>

static const struct pwm_dt_spec servo = PWM_DT_SPEC_GET(DT_PATH(zephyr_user));
static uint16_t current_us;

int hw_servo_init(uint16_t pulse_us)
{
	if (!pwm_is_ready_dt(&servo)) {
		return -ENODEV;
	}
	current_us = 0u;
	return hw_servo_set_us(pulse_us);
}

int hw_servo_set_us(uint16_t pulse_us)
{
	if (pulse_us == current_us) {
		return 0;
	}
	current_us = pulse_us;
	return pwm_set_pulse_dt(&servo, PWM_USEC(pulse_us));
}
