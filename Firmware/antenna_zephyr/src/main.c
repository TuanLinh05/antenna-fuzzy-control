/*
 * Antenna V5 firmware - STM32F103C8 Blue Pill, Zephyr.
 *
 *   17HS1352-P4130 + TB6600 (12 V, 1/16) --GT2 20T:80T--> azimuth shaft
 *   MT6701 on the azimuth shaft (I2C2) -> fuzzy Sugeno azimuth loop, 100 Hz
 *   LD-1501MG elevation servo (internal position loop) <- PWM 50 Hz
 *
 * Everything that decides motion lives in core/ (portable C shared with the
 * MATLAB SIL/PIL tests). This file only wires the core to the hardware:
 * one 10 ms tick = read sensor, acore_step, update STEP timer and servo PWM,
 * then execute the UART commands received during the previous period.
 */
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/kernel.h>

#include "antenna_core.h"
#include "hw_mt6701.h"
#include "hw_servo.h"
#include "hw_stepper.h"
#include "link_proto.h"
#include "params_store.h"
#include "uart_link.h"

static acore_params_t par;
static acore_t core;
static link_ctx_t lk;
static uint16_t last_raw;
static uint32_t last_loop_us;
static uint32_t sensor_errors;

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct device *const wdt = DEVICE_DT_GET(DT_ALIAS(watchdog0));
static int wdt_channel = -1;

K_SEM_DEFINE(tick_sem, 0, 1);

static void tick_fn(struct k_timer *timer)
{
	ARG_UNUSED(timer);
	k_sem_give(&tick_sem);
}
K_TIMER_DEFINE(ctrl_timer, tick_fn, NULL);

/* ---------- protocol hooks ---------- */

static void hk_write(link_ctx_t *l, const char *text)
{
	ARG_UNUSED(l);
	(void)uart_link_write(text);
}

static int hk_save(link_ctx_t *l)
{
	ARG_UNUSED(l);
	return params_store_save(&par);
}

static int hk_load(link_ctx_t *l)
{
	ARG_UNUSED(l);
	if (params_store_load(&par) != 0) {
		acore_params_default(&par);
		return -1;
	}
	return 0;
}

static int hk_read_raw(link_ctx_t *l, uint16_t *raw)
{
	ARG_UNUSED(l);
	return hw_mt6701_read(raw);
}

static void hk_set_pil(link_ctx_t *l, int on)
{
	ARG_UNUSED(l);
	/* PIL: the model in MATLAB is the plant; never move the real motor */
	hw_stepper_enable(on == 0);
}

static uint32_t hk_cycles(link_ctx_t *l)
{
	ARG_UNUSED(l);
	return k_cycle_get_32();
}

static void hk_params_changed(link_ctx_t *l)
{
	ARG_UNUSED(l);
	hw_stepper_set_motor_sign(par.motor_sign);
}

static void hk_telemetry(link_ctx_t *l)
{
	char buf[LINK_LINE_MAX + 32];

	if (link_format_telemetry(buf, sizeof(buf), l->core, k_uptime_get_32(), hw_stepper_steps(),
				  last_raw, last_loop_us, l->pil)) {
		(void)uart_link_write(buf);
	}
}

static const link_hooks_t hooks = {
	.write = hk_write,
	.save_params = hk_save,
	.load_params = hk_load,
	.read_raw = hk_read_raw,
	.set_pil = hk_set_pil,
	.cycles_now = hk_cycles,
	.params_changed = hk_params_changed,
	.telemetry = hk_telemetry,
};

/* ---------- helpers ---------- */

static void watchdog_start(void)
{
	struct wdt_timeout_cfg cfg = {
		.window = {.min = 0u, .max = CONFIG_ANTENNA_WDT_TIMEOUT_MS},
		.callback = NULL,
		.flags = WDT_FLAG_RESET_SOC,
	};

	if (!device_is_ready(wdt)) {
		return;
	}
	wdt_channel = wdt_install_timeout(wdt, &cfg);
	if (wdt_channel < 0) {
		return;
	}
	if (wdt_setup(wdt, WDT_OPT_PAUSE_HALTED_BY_DBG) != 0) {
		(void)wdt_setup(wdt, 0);
	}
}

static void led_update(uint32_t tick)
{
	int on;

	if (lk.pil) {
		on = 1;
	} else if (core.mode == ACORE_MODE_FAULT) {
		on = (tick / 10u) & 1u; /* 5 Hz */
	} else if (core.mode == ACORE_MODE_NOZERO) {
		on = (tick % 100u) < 10u; /* short flash each second */
	} else {
		on = (tick / 50u) & 1u; /* 1 Hz */
	}
	gpio_pin_set_dt(&led, on);
}

static void report_item(const char *name, int rc)
{
	char num[12];

	(void)uart_link_write(name);
	link_fmt_i32(num, rc);
	(void)uart_link_write(num);
}

/* "name=0" means OK; a negative value is a Zephyr errno. */
static void report_boot(int params_rc, int sensor_rc, int store_rc, int stepper_rc, int servo_rc)
{
	(void)uart_link_write("# antenna_v5 Zephyr " LINK_FW_VERSION " ready\n# params=");
	(void)uart_link_write(params_rc == 0 ? "flash" : "default");
	report_item(" nvs=", store_rc);
	report_item(" sensor=", sensor_rc);
	report_item(" stepper=", stepper_rc);
	report_item(" servo=", servo_rc);
	(void)uart_link_write("\n");
}

int main(void)
{
	char line[LINK_LINE_MAX];
	acore_in_t in = {0};
	acore_out_t out;
	uint32_t tick = 0, prev = 0, telemetry_acc = 0;
	const uint32_t ts_cycles = (uint32_t)(sys_clock_hw_cycles_per_sec() / 100u);
	int store_rc, params_rc, sensor_rc, stepper_rc, servo_rc;
	uint16_t raw;

	if (gpio_is_ready_dt(&led)) {
		gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	}
	(void)uart_link_init();
	stepper_rc = hw_stepper_init();
	sensor_rc = hw_mt6701_init();
	store_rc = params_store_init();

	acore_params_default(&par);
	params_rc = params_store_load(&par);
	if (params_rc != 0) {
		acore_params_default(&par);
	}
	hw_stepper_set_motor_sign(par.motor_sign);
	acore_init(&core, &par);
	servo_rc = hw_servo_init(core.out.servo_us);
	link_init(&lk, &core, &par, &hooks, NULL);
	lk.telemetry_ms = CONFIG_ANTENNA_TELEMETRY_MS;
	if (sensor_rc == 0) {
		sensor_rc = hw_mt6701_read(&raw);
	}
	report_boot(params_rc, sensor_rc, store_rc, stepper_rc, servo_rc);
	watchdog_start();

	/* The control period is fixed at 10 ms (parameter ts is read-only). */
	k_timer_start(&ctrl_timer, K_MSEC(10), K_MSEC(10));

	for (;;) {
		uint32_t t0, period;

		k_sem_take(&tick_sem, K_FOREVER);
		t0 = k_cycle_get_32();
		period = t0 - prev;
		prev = t0;
		tick++;
		if (wdt_channel >= 0) {
			(void)wdt_feed(wdt, wdt_channel);
		}

		if (!lk.pil) {
			int rc = hw_mt6701_read(&raw);

			in.sensor_ok = (rc == 0);
			if (rc == 0) {
				in.raw = raw;
				last_raw = raw;
			} else if ((++sensor_errors % 10u) == 3u) {
				(void)hw_mt6701_recover();
			}
			in.steps = hw_stepper_steps();
			in.heartbeat = lk.heartbeat;
			lk.heartbeat = 0;
			in.overrun = (tick > 2u && period > ts_cycles + ts_cycles / 2u) ? 1u : 0u;
			acore_step(&core, &par, &in, &out);
			hw_stepper_command(out.half_period_us, out.dir);
			(void)hw_servo_set_us(out.servo_us);
		}

		/* commands received during the last period take effect at the next step */
		while (uart_link_get_line(line, sizeof(line)) == 0) {
			link_handle_line(&lk, line);
		}

		if (lk.telemetry_ms != 0u && !lk.pil) {
			telemetry_acc += 10u;
			if (telemetry_acc >= lk.telemetry_ms) {
				telemetry_acc = 0u;
				hk_telemetry(&lk);
			}
		}
		led_update(tick);
		last_loop_us = k_cyc_to_us_floor32(k_cycle_get_32() - t0);
	}
	return 0;
}
