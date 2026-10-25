/*
 * Host unit tests for the portable control core (antenna_core, stepgen,
 * link_proto). Built with the PC gcc by run_host_tests.py; also writes
 * vectors that MATLAB compares with its FIS and reference implementation.
 *
 * usage: test_core <output_dir>
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "antenna_core.h"
#include "link_proto.h"
#include "stepgen.h"

static int failures, checks;

#define CHECK(cond, ...)                                                                           \
	do {                                                                                       \
		checks++;                                                                          \
		if (!(cond)) {                                                                     \
			failures++;                                                                \
			printf("FAIL %s:%d: ", __FILE__, __LINE__);                                \
			printf(__VA_ARGS__);                                                       \
			printf("\n");                                                              \
		}                                                                                  \
	} while (0)

#define D2R(x) ((float)(x) * (ACORE_PI / 180.0f))
#define R2D(x) ((double)(x) * 180.0 / 3.14159265358979323846)

static const char *outdir = ".";

static FILE *open_out(const char *name)
{
	char path[1024];

	snprintf(path, sizeof(path), "%s/%s", outdir, name);
	return fopen(path, "w");
}

/* ------------------------------------------------------------------ */
static void test_params(void)
{
	acore_params_t p;

	acore_params_default(&p);
	CHECK(acore_params_check(&p) == 0, "defaults rejected: %d", acore_params_check(&p));
	p.mf_e_in = 1.2f;
	CHECK(acore_params_check(&p) != 0, "bad mf accepted");
	acore_params_default(&p);
	p.az_max = D2R(170);
	CHECK(acore_params_check(&p) != 0, "az_max >= az_fault accepted");
}

static void test_fuzzy(void)
{
	acore_params_t p;
	FILE *f;
	float mu[ACORE_NMF];

	acore_params_default(&p);
	/* partition of unity and exact rule values at the centres */
	for (int k = 0; k <= 2000; k++) {
		float x = -1.2f + 2.4f * (float)k / 2000.0f;
		float s = 0.0f;

		acore_memberships(x, p.mf_e_in, mu);
		for (int i = 0; i < ACORE_NMF; i++) {
			s += mu[i];
		}
		CHECK(fabsf(s - 1.0f) < 1e-6f, "membership sum %g at x=%g", (double)s, (double)x);
	}
	{
		const float ce[5] = {-1.0f, -p.mf_e_in, 0.0f, p.mf_e_in, 1.0f};
		const float cd[5] = {-1.0f, -p.mf_de_in, 0.0f, p.mf_de_in, 1.0f};

		for (int i = 0; i < 5; i++) {
			for (int j = 0; j < 5; j++) {
				float u = acore_fuzzy(&p, ce[i], cd[j]);

				CHECK(fabsf(u - p.rules[i][j]) < 1e-6f, "rule (%d,%d) %g vs %g", i, j,
				      (double)u, (double)p.rules[i][j]);
			}
		}
	}
	/* bounds, odd symmetry, monotonicity in e */
	f = open_out("fuzzy_C_vectors.csv");
	if (f) {
		fprintf(f, "x1,x2,u\n");
	}
	for (int a = 0; a <= 80; a++) {
		float prev = -2.0f;

		for (int b = 0; b <= 80; b++) {
			float x2 = -1.0f + 2.0f * (float)a / 80.0f;
			float x1 = -1.0f + 2.0f * (float)b / 80.0f;
			float u = acore_fuzzy(&p, x1, x2);
			float um = acore_fuzzy(&p, -x1, -x2);

			CHECK(u >= -1.0f && u <= 1.0f, "u out of range %g", (double)u);
			CHECK(fabsf(u + um) < 1e-6f, "symmetry %g %g", (double)u, (double)um);
			CHECK(u >= prev - 1e-6f, "not monotone in e at x1=%g x2=%g", (double)x1,
			      (double)x2);
			prev = u;
			if (f) {
				fprintf(f, "%.9g,%.9g,%.9g\n", (double)x1, (double)x2, (double)u);
			}
		}
	}
	if (f) {
		fclose(f);
	}
}

static void test_helpers(void)
{
	acore_params_t p;
	uint32_t hp;

	acore_params_default(&p);
	/* 30 deg/s at the antenna = 1066.67 STEP/s -> 469 us half period */
	hp = acore_velocity_to_half_period(&p, D2R(30));
	CHECK(hp == 469u, "hp(30 deg/s) = %u", (unsigned)hp);
	CHECK(acore_velocity_to_half_period(&p, 0.0f) == 0u, "hp(0)");
	CHECK(acore_velocity_to_half_period(&p, D2R(0.1)) == 0u, "hp below timer range");
	CHECK(acore_velocity_to_half_period(&p, 100.0f) == 100u, "hp clamp");

	/* raw -> azimuth: zero, sign and wrap */
	p.zero_rad = D2R(350);
	CHECK(fabs(R2D(acore_raw_to_az(&p, 0)) - 10.0) < 0.03, "wrap +10: %g",
	      R2D(acore_raw_to_az(&p, 0)));
	p.sensor_sign = -1;
	CHECK(fabs(R2D(acore_raw_to_az(&p, 0)) + 10.0) < 0.03, "sign");
	p.sensor_sign = 1;
	p.zero_rad = 0.0f;
	CHECK(fabs(R2D(acore_raw_to_az(&p, 8192)) - 180.0) < 0.03 ||
		      fabs(R2D(acore_raw_to_az(&p, 8192)) + 180.0) < 0.03,
	      "half turn");
	/* calibration removes a first harmonic */
	p.cal_a1 = D2R(1.0);
	{
		float phi = acore_sensor_angle(&p, 0);

		CHECK(fabs(R2D(phi) - 359.0) < 1e-3 || fabs(R2D(phi) + 1.0) < 1e-3, "cal %g",
		      R2D(phi));
	}
	/* discrete stopping curve, applied like the core (governor + acceleration
	 * limit each period): the overshoot stays below one acceleration quantum
	 * a*ts^2/2 (0.006 deg with the defaults) */
	for (int k = 1; k < 200; k++) {
		float e = D2R(0.01 * k * k);
		float v = acore_brake_speed(p.accel, p.ts, e), x = 0.0f;

		for (int n = 0; n < 2000; n++) {
			float rem = e - x;
			float vd = rem > 0.0f ? acore_brake_speed(p.accel, p.ts, rem) : 0.0f;
			float dv = vd - v;

			if (dv < -p.accel * p.ts) {
				dv = -p.accel * p.ts;
			}
			if (dv > p.accel * p.ts) {
				dv = p.accel * p.ts;
			}
			v += dv;
			x += v * p.ts;
		}
		CHECK(x - e <= 0.5f * p.accel * p.ts * p.ts, "brake overshoot e=%g x=%g", (double)e,
		      (double)x);
	}
	CHECK(acore_servo_us(&p, D2R(90)) == 1500u, "servo 90");
	CHECK(acore_servo_us(&p, D2R(0)) == 1000u, "servo clamp low");
	CHECK(acore_servo_us(&p, D2R(117)) == 1800u, "servo 117 deg -> %u",
	      (unsigned)acore_servo_us(&p, D2R(117)));
}

/* ------------------------------------------------------------------ */
typedef struct {
	double t;
	int stepped;
	int dir;
} edge_t;

static void test_stepgen(void)
{
	stepgen_t sg;
	stepgen_pins_t pins;
	double t = 0.0, next;
	int edges = 0, last_dir = 1;
	double last_rise = -1.0, last_dir_change = -1.0, last_fall = -1.0;
	uint32_t iv;

	stepgen_init(&sg, 50u);
	iv = stepgen_command(&sg, 500u, 1);
	CHECK(iv == STEPGEN_START_US, "start interval %u", (unsigned)iv);
	CHECK(stepgen_command(&sg, 500u, 1) == 0u, "no restart while running");
	next = iv * 1e-6;
	/* 0.1 s forward at 1 kHz, then reverse at 2 kHz for 0.1 s, then stop */
	while (next < 1.0) {
		t = next;
		if (t > 0.1 && t < 0.2) {
			stepgen_command(&sg, 250u, -1);
		} else if (t >= 0.2) {
			stepgen_command(&sg, 0u, -1);
		}
		iv = stepgen_tick(&sg, &pins);
		if (pins.dir_changed) {
			CHECK(t - last_fall >= 249e-6, "DIR too close to falling edge");
			last_dir_change = t;
			last_dir = pins.dir;
		}
		if (pins.stepped) {
			CHECK(last_dir_change < 0 || t - last_dir_change >= 249e-6,
			      "STEP too close to DIR change");
			CHECK(pins.dir == last_dir, "dir mismatch");
			last_rise = t;
			edges++;
		} else if (!pins.dir_changed && iv) {
			last_fall = t;
		}
		if (!iv) {
			break;
		}
		next = t + iv * 1e-6;
	}
	(void)last_rise;
	CHECK(!sg.running, "generator stopped");
	/* forward: ~100 steps in 0.1 s; reverse: ~200 steps in 0.1 s -> net about -100 */
	CHECK(sg.steps <= -95 && sg.steps >= -105, "net steps %d", (int)sg.steps);
	CHECK(edges >= 290 && edges <= 310, "edges %d", edges);
	/* restart after stop */
	iv = stepgen_command(&sg, 1000u, 1);
	CHECK(iv == STEPGEN_START_US && sg.running, "restart");

	/* retime: a slow interval in progress is shortened when the rate rises */
	stepgen_init(&sg, 50u);
	stepgen_command(&sg, 40000u, 1);
	(void)stepgen_tick(&sg, &pins);                   /* first rising edge, 40 ms high */
	CHECK(pins.stepped && sg.interval == 40000u, "slow start");
	stepgen_command(&sg, 500u, 1);
	iv = stepgen_retime(&sg, 3000u);
	CHECK(iv == 3000u + STEPGEN_RETIME_MARGIN_US, "retime %u", (unsigned)iv);
	CHECK(stepgen_retime(&sg, 3000u) == 0u, "second retime must keep interval");
	iv = stepgen_tick(&sg, &pins);                    /* falling edge uses the faster rate */
	CHECK(iv == 500u && !pins.stepped, "low phase %u", (unsigned)iv);
	stepgen_command(&sg, 2000u, 1);
	CHECK(stepgen_retime(&sg, 100u) == 0u, "slower rate must not retime");
}

/* ------------------------------------------------------------------ */
/* Closed loop with an ideal stepper (output angle = steps * step angle) and a
 * 14-bit sensor: checks the specification on the reference sequence. */
typedef struct {
	double peak_speed, overshoot_pct[4], final_err[4], settle[4];
	int fault;
} loop_result_t;

static loop_result_t closed_loop(acore_params_t *p, int ctrl, double noise_deg)
{
	acore_t c;
	stepgen_t sg;
	stepgen_pins_t pins;
	acore_in_t in;
	acore_out_t out;
	loop_result_t r;
	const double step_angle = 2.0 * 3.14159265358979323846 / (double)p->steps_rev;
	double next_tick = -1.0, theta_prev = 0.0;
	const double targets[4] = {60, 150, 30, 90};
	double start[4] = {0, 60, 150, 30};
	unsigned seed = 12345u;

	memset(&r, 0, sizeof(r));
	p->ctrl = (uint8_t)ctrl;
	p->zero_valid = 1;
	p->zero_rad = 0.0f;
	acore_init(&c, p);
	stepgen_init(&sg, 50u);
	memset(&in, 0, sizeof(in));
	for (int k = 0; k < 4800; k++) {
		double t0 = k * 0.01, t1 = t0 + 0.01;
		double theta = sg.steps * step_angle;
		double meas = theta * 180.0 / 3.14159265358979323846;
		int seg = k / 1200;

		if (noise_deg > 0.0) {
			seed = seed * 1103515245u + 12345u;
			meas += noise_deg * (((double)(seed >> 8) / 16777216.0) - 0.5) * 3.4641;
		}
		while (meas < 0.0) {
			meas += 360.0;
		}
		in.raw = (uint16_t)((long)floor(meas / 360.0 * 16384.0 + 0.5) & 16383);
		in.sensor_ok = 1;
		in.heartbeat = 1;
		in.steps = sg.steps;
		if (k == 1) {
			acore_cmd_sequence(&c, p, 0);
		}
		acore_step(&c, p, &in, &out);
		{
			uint32_t iv = stepgen_command(&sg, out.half_period_us, out.dir);

			if (iv) {
				next_tick = t0 + 0.0002 + iv * 1e-6;
			}
		}
		while (sg.running && next_tick < t1) {
			uint32_t iv = stepgen_tick(&sg, &pins);

			next_tick = iv ? next_tick + iv * 1e-6 : 1e9;
		}
		theta = sg.steps * step_angle * 180.0 / 3.14159265358979323846;
		{
			double sp = fabs(theta - theta_prev) / 0.01;

			if (sp > r.peak_speed) {
				r.peak_speed = sp;
			}
			theta_prev = theta;
		}
		if (seg < 4) {
			/* the sequence starts at k=1 so segment boundaries are offset by one tick */
			double step = targets[seg] - start[seg];
			double over = (theta - targets[seg]) * (step > 0 ? 1 : -1);

			if (over / fabs(step) * 100.0 > r.overshoot_pct[seg]) {
				r.overshoot_pct[seg] = over / fabs(step) * 100.0;
			}
			if (fabs(theta - targets[seg]) > 0.02 * fabs(step)) {
				r.settle[seg] = t1 - seg * 12.0;
			}
			r.final_err[seg] = fabs(theta - targets[seg]);
		}
	}
	r.fault = c.fault;
	return r;
}

static void test_closed_loop(void)
{
	acore_params_t p;

	for (int ctrl = 0; ctrl < 2; ctrl++) {
		for (int noisy = 0; noisy < 2; noisy++) {
			loop_result_t r;

			acore_params_default(&p);
			r = closed_loop(&p, ctrl, noisy ? 0.02 : 0.0);
			printf("closed loop ctrl=%d noise=%d: peak %.2f deg/s, settle %.2f %.2f %.2f "
			       "%.2f s, over %.3f %.3f %.3f %.3f %%, final %.4f %.4f %.4f %.4f deg\n",
			       ctrl, noisy, r.peak_speed, r.settle[0], r.settle[1], r.settle[2],
			       r.settle[3], r.overshoot_pct[0], r.overshoot_pct[1],
			       r.overshoot_pct[2], r.overshoot_pct[3], r.final_err[0], r.final_err[1],
			       r.final_err[2], r.final_err[3]);
			CHECK(r.fault == 0, "fault 0x%x", r.fault);
			CHECK(r.peak_speed <= 30.0, "peak speed %g", r.peak_speed);
			for (int s = 0; s < 4; s++) {
				CHECK(r.overshoot_pct[s] <= 2.0, "overshoot %g", r.overshoot_pct[s]);
				CHECK(r.final_err[s] <= 0.1, "final error %g", r.final_err[s]);
				CHECK(r.settle[s] < 11.0, "settling %g", r.settle[s]);
			}
		}
	}
}

/* ------------------------------------------------------------------ */
static void run_ticks(acore_t *c, acore_params_t *p, acore_in_t *in, int n)
{
	acore_out_t out;

	for (int k = 0; k < n; k++) {
		acore_step(c, p, in, &out);
	}
}

static void test_faults(void)
{
	acore_params_t p;
	acore_t c;
	acore_in_t in;

	acore_params_default(&p);
	p.zero_valid = 1;
	memset(&in, 0, sizeof(in));
	in.sensor_ok = 1;
	in.raw = 0;

	/* sensor errors: two bad samples tolerated, third latches */
	acore_init(&c, &p);
	run_ticks(&c, &p, &in, 2);
	in.sensor_ok = 0;
	run_ticks(&c, &p, &in, 2);
	CHECK(c.fault == 0, "early sensor fault");
	run_ticks(&c, &p, &in, 1);
	CHECK(c.fault & ACORE_F_SENSOR, "sensor fault missing");
	CHECK(acore_cmd_goto(&c, &p, ACORE_GOTO_AZ, 0.1f, 0, 1) < 0, "goto accepted in fault");
	in.sensor_ok = 1;
	CHECK(acore_cmd_clear(&c, &p) == 0 && c.mode == ACORE_MODE_ACTIVE, "clear");

	/* glitch: a 90 degree jump is rejected */
	acore_init(&c, &p);
	run_ticks(&c, &p, &in, 2);
	in.raw = 4096;
	run_ticks(&c, &p, &in, 1);
	CHECK(fabsf(c.theta) < 1e-3f && c.bad_count == 1, "glitch accepted");
	in.raw = 0;
	run_ticks(&c, &p, &in, 1);
	CHECK(c.bad_count == 0 && c.fault == 0, "glitch recovery");

	/* heartbeat: host-owned motion without heartbeat */
	acore_init(&c, &p);
	run_ticks(&c, &p, &in, 2);
	acore_cmd_goto(&c, &p, ACORE_GOTO_AZ | ACORE_GOTO_EL, 0.0f, D2R(90), 1);
	in.heartbeat = 0;
	run_ticks(&c, &p, &in, 199);
	CHECK(c.fault == 0, "early heartbeat fault");
	run_ticks(&c, &p, &in, 3);
	CHECK(c.fault & ACORE_F_HEARTBEAT, "heartbeat fault missing");

	/* stall: steps advance, sensor does not */
	acore_init(&c, &p);
	run_ticks(&c, &p, &in, 2);
	acore_cmd_goto(&c, &p, ACORE_GOTO_AZ, D2R(60), 0, 0);
	for (int k = 0; k < 300 && !(c.fault & ACORE_F_STALL); k++) {
		acore_out_t out;

		acore_step(&c, &p, &in, &out);
		if (out.half_period_us) {
			in.steps += (int32_t)(0.01 * 500000.0 / out.half_period_us) * out.dir;
		}
	}
	CHECK(c.fault & ACORE_F_STALL, "stall not detected");
	CHECK(c.v_cmd == 0.0f && c.out.half_period_us == 0u, "stepping after fault");

	/* limit */
	acore_init(&c, &p);
	in.steps = 0;
	in.raw = (uint16_t)(160.0 / 360.0 * 16384.0);
	run_ticks(&c, &p, &in, 2);
	CHECK(c.fault & ACORE_F_LIMIT, "limit fault missing");

	/* no zero: azimuth refused */
	p.zero_valid = 0;
	acore_init(&c, &p);
	in.raw = 0;
	run_ticks(&c, &p, &in, 2);
	CHECK(c.mode == ACORE_MODE_NOZERO, "mode %d", c.mode);
	CHECK(acore_cmd_goto(&c, &p, ACORE_GOTO_AZ, 0.1f, 0, 1) < 0, "az accepted without zero");
	CHECK(acore_cmd_goto(&c, &p, ACORE_GOTO_EL, 0, D2R(100), 1) == 0, "el refused");
	CHECK(acore_set_zero(&c, &p, 1000, D2R(5)) == 0 && p.zero_valid, "set zero");
	CHECK(fabs(R2D(acore_raw_to_az(&p, 1000)) - 5.0) < 1e-3, "zero value");
	CHECK(c.mode == ACORE_MODE_ACTIVE, "active after zero");
}

/* ------------------------------------------------------------------ */
static char out_text[200000];
static size_t out_len;

static void host_write(link_ctx_t *lk, const char *text)
{
	size_t n = strlen(text);

	(void)lk;
	if (out_len + n < sizeof(out_text)) {
		memcpy(out_text + out_len, text, n + 1);
		out_len += n;
	}
}

static int host_read_raw(link_ctx_t *lk, uint16_t *raw)
{
	(void)lk;
	*raw = 2000;
	return 0;
}

static int saved;
static int host_save(link_ctx_t *lk)
{
	(void)lk;
	saved++;
	return 0;
}

static void cmd(link_ctx_t *lk, const char *text)
{
	char line[LINK_LINE_MAX];

	strncpy(line, text, sizeof(line) - 1);
	line[sizeof(line) - 1] = 0;
	out_len = 0;
	out_text[0] = 0;
	link_handle_line(lk, line);
}

static void test_link(void)
{
	static const link_hooks_t hooks = {
		.write = host_write, .save_params = host_save, .read_raw = host_read_raw};
	acore_params_t p, p2;
	acore_t c, c2;
	link_ctx_t lk;
	char buf[64];
	float f;
	const char *s;

	acore_params_default(&p);
	acore_init(&c, &p);
	link_init(&lk, &c, &p, &hooks, NULL);

	cmd(&lk, "V");
	CHECK(strncmp(out_text, "V,antenna_v5,", 13) == 0, "V: %s", out_text);
	cmd(&lk, "G 10 90");
	CHECK(strncmp(out_text, "ERR G -2", 8) == 0, "G before zero: %s", out_text);
	cmd(&lk, "Z 0");
	CHECK(strncmp(out_text, "ERR Z -2", 8) != 0, "Z: %s", out_text);
	/* Z needs the first sample; feed one */
	{
		acore_in_t in = {.raw = 2000, .sensor_ok = 1};
		acore_out_t o;

		acore_step(&c, &p, &in, &o);
	}
	cmd(&lk, "Z 0");
	CHECK(strncmp(out_text, "OK Z", 4) == 0 && saved == 2 && p.zero_valid, "Z: %s", out_text);
	cmd(&lk, "G 10.5 100");
	CHECK(strncmp(out_text, "OK G", 4) == 0, "G: %s", out_text);
	CHECK(fabs(R2D(c.target) - 10.5) < 1e-4 && fabs(R2D(c.el_target) - 100) < 1e-4, "G values");
	cmd(&lk, "G 1e1 9x");
	CHECK(strncmp(out_text, "ERR G", 5) == 0, "bad number accepted");
	cmd(&lk, "P accel_dps2 90");
	CHECK(strncmp(out_text, "P,accel_dps2,90.0,", 18) == 0, "P set: %s", out_text);
	CHECK(fabs(R2D(p.accel) - 90.0) < 1e-4, "accel value");
	cmd(&lk, "P ts 0.02");
	CHECK(strncmp(out_text, "ERR P -3", 8) == 0, "ts writable: %s", out_text);
	cmd(&lk, "P mf_e_in 3");
	CHECK(strncmp(out_text, "ERR P -6", 8) == 0 && p.mf_e_in < 1.0f, "range: %s", out_text);
	cmd(&lk, "PX r21 3F000000");
	CHECK(p.rules[2][1] == 0.5f, "PX rule");
	cmd(&lk, "P seq_az3 -45");
	CHECK(fabs(R2D(p.seq_az[3]) + 45.0) < 1e-4, "seq_az3");
	cmd(&lk, "P");
	CHECK(strstr(out_text, "P,r44,1.0,3F800000") != NULL && strstr(out_text, "OK P") != NULL,
	      "listing");
	cmd(&lk, "T 5");
	CHECK(strncmp(out_text, "ERR T", 5) == 0, "T 5 accepted");
	cmd(&lk, "T 20");
	CHECK(lk.telemetry_ms == 20u, "T");
	cmd(&lk, "H");
	CHECK(lk.heartbeat == 1 && out_len == 0, "H");

	/* number formatting / parsing */
	link_fmt_float(buf, -150.0f);
	CHECK(strcmp(buf, "-150.0") == 0, "fmt %s", buf);
	link_fmt_float(buf, 0.03f);
	CHECK(strcmp(buf, "0.03") == 0, "fmt %s", buf);
	s = "-12.5e-1 ";
	CHECK(link_parse_float(&s, &f) == 0 && fabsf(f + 1.25f) < 1e-6f, "parse %g", (double)f);

	/* PIL: X steps must equal direct calls of the core, bit for bit */
	acore_params_default(&p);
	p.zero_valid = 1;
	p2 = p;
	acore_init(&c2, &p2);
	cmd(&lk, "M 1");
	CHECK(strncmp(out_text, "OK M", 4) == 0 && lk.pil, "M 1: %s", out_text);
	{
		int ok = 1;
		int32_t steps = 0;
		double acc = 0.0; /* fractional steps of the toy plant */

		for (int k = 0; k < 400 && ok; k++) {
			char line[96];
			acore_in_t in;
			acore_out_t o;
			uint32_t th, vc;
			int raw = (int)(fmod(steps * (16384.0 / 12800.0) + 16384.0 * 4, 16384.0));

			if (k == 1) {
				acore_cmd_goto(&c2, &p2, ACORE_GOTO_AZ | ACORE_GOTO_EL, D2R(20),
					       D2R(80), 0);
			}
			snprintf(line, sizeof(line), "X %d %d %d 3", k, raw, (int)steps);
			if (k == 1) {
				acore_cmd_goto(&c, &p, ACORE_GOTO_AZ | ACORE_GOTO_EL, D2R(20),
					       D2R(80), 0);
			}
			cmd(&lk, line);
			memset(&in, 0, sizeof(in));
			in.raw = (uint16_t)raw;
			in.steps = steps;
			in.sensor_ok = 1;
			in.heartbeat = 1;
			acore_step(&c2, &p2, &in, &o);
			memcpy(&th, &c2.theta, 4);
			memcpy(&vc, &c2.v_cmd, 4);
			{
				char expect[64];

				snprintf(expect, sizeof(expect), "Y,%d,%d,%d,%08X,%08X,", k, c2.mode,
					 c2.fault, (unsigned)th, (unsigned)vc);
				if (strncmp(out_text, expect, strlen(expect)) != 0) {
					printf("PIL mismatch at %d: %s vs %s\n", k, out_text, expect);
					ok = 0;
				}
			}
			if (o.half_period_us) {
				acc += 0.01 * 500000.0 / o.half_period_us * o.dir;
				steps = (int32_t)floor(acc + 0.5);
			}
		}
		CHECK(ok, "PIL bit exact");
		CHECK(fabs(R2D(c2.theta) - 20.0) < 0.05, "PIL target reached %g", R2D(c2.theta));
	}
	cmd(&lk, "M 0");
	CHECK(!lk.pil, "M 0");
}

int main(int argc, char **argv)
{
	if (argc > 1) {
		outdir = argv[1];
	}
	test_params();
	test_fuzzy();
	test_helpers();
	test_stepgen();
	test_closed_loop();
	test_faults();
	test_link();
	printf("%d checks, %d failures\n", checks, failures);
	return failures ? 1 : 0;
}
