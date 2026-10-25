/*
 * STEP generation: TIM2 runs as a Zephyr counter at 1 MHz. Every top-value
 * interrupt calls stepgen_tick(), which returns the time to the next edge;
 * the new top value is loaded without resetting the counter, so the edge
 * spacing is set by the hardware timer and not by the interrupt latency.
 */
#include "hw_stepper.h"

#include <zephyr/device.h>
#include <zephyr/drivers/counter.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>

#include "stepgen.h"

#define USER_NODE DT_PATH(zephyr_user)
#define DIR_GUARD_US 50u

static const struct gpio_dt_spec step_pin = GPIO_DT_SPEC_GET(USER_NODE, step_gpios);
static const struct gpio_dt_spec dir_pin = GPIO_DT_SPEC_GET(USER_NODE, dir_gpios);
#if DT_NODE_HAS_PROP(USER_NODE, ena_gpios)
static const struct gpio_dt_spec ena_pin = GPIO_DT_SPEC_GET(USER_NODE, ena_gpios);
#endif
static const struct device *const timer = DEVICE_DT_GET(DT_NODELABEL(stepgen_counter));

static stepgen_t sg;
static volatile int8_t motor_sign = 1;
static volatile bool enabled = true;
static uint32_t loaded_ticks;

static void write_dir(int8_t dir)
{
	gpio_pin_set_dt(&dir_pin, (dir * motor_sign) > 0);
}

static void top_cb(const struct device *dev, void *user_data)
{
	stepgen_pins_t pins;
	uint32_t next = stepgen_tick(&sg, &pins);

	ARG_UNUSED(user_data);
	if (pins.dir_changed) {
		write_dir(pins.dir);
	}
	gpio_pin_set_dt(&step_pin, pins.step_level && enabled);
	if (next == 0u) {
		counter_stop(dev);
		return;
	}
	if (next - 1u != loaded_ticks) {
		struct counter_top_cfg cfg = {
			.ticks = next - 1u, /* period = top + 1 ticks */
			.callback = top_cb,
			.user_data = NULL,
			.flags = COUNTER_TOP_CFG_DONT_RESET,
		};

		loaded_ticks = next - 1u;
		(void)counter_set_top_value(dev, &cfg);
	}
}

int hw_stepper_init(void)
{
	if (!gpio_is_ready_dt(&step_pin) || !gpio_is_ready_dt(&dir_pin) || !device_is_ready(timer)) {
		return -ENODEV;
	}
	if (counter_get_frequency(timer) != 1000000u) {
		return -EINVAL; /* st,prescaler must give 1 us ticks */
	}
	gpio_pin_configure_dt(&step_pin, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&dir_pin, GPIO_OUTPUT_INACTIVE);
#if DT_NODE_HAS_PROP(USER_NODE, ena_gpios)
	gpio_pin_configure_dt(&ena_pin, GPIO_OUTPUT_INACTIVE); /* driver enabled */
#endif
	stepgen_init(&sg, DIR_GUARD_US);
	write_dir(sg.dir);
	return 0;
}

void hw_stepper_command(uint32_t half_period_us, int8_t dir)
{
	unsigned int key;
	uint32_t start;

	if (!enabled) {
		half_period_us = 0u;
	}
	key = irq_lock();
	start = stepgen_command(&sg, half_period_us, dir);
	if (start != 0u) {
		struct counter_top_cfg cfg = {
			.ticks = start - 1u,
			.callback = top_cb,
			.user_data = NULL,
			.flags = 0, /* reset the counter: first edge after `start` us */
		};

		loaded_ticks = start - 1u;
		(void)counter_set_top_value(timer, &cfg);
		(void)counter_start(timer);
	} else if (sg.running) {
		/* faster rate while a long interval runs: shorten it (CNT = elapsed us) */
		uint32_t elapsed = 0u;
		uint32_t iv;

		(void)counter_get_value(timer, &elapsed);
		iv = stepgen_retime(&sg, elapsed);
		if (iv != 0u) {
			struct counter_top_cfg cfg = {
				.ticks = iv - 1u,
				.callback = top_cb,
				.user_data = NULL,
				.flags = COUNTER_TOP_CFG_DONT_RESET | COUNTER_TOP_CFG_RESET_WHEN_LATE,
			};

			loaded_ticks = iv - 1u;
			(void)counter_set_top_value(timer, &cfg);
		}
	}
	irq_unlock(key);
}

int32_t hw_stepper_steps(void)
{
	return sg.steps;
}

void hw_stepper_set_motor_sign(int8_t sign)
{
	unsigned int key = irq_lock();

	motor_sign = sign < 0 ? -1 : 1;
	write_dir(sg.dir);
	irq_unlock(key);
}

void hw_stepper_enable(bool enable)
{
	if (!enable) {
		hw_stepper_command(0u, 1);
	}
	enabled = enable;
#if DT_NODE_HAS_PROP(USER_NODE, ena_gpios)
	gpio_pin_set_dt(&ena_pin, enable ? 0 : 1);
#endif
}
