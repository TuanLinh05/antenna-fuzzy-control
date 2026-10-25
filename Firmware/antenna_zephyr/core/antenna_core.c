/*
 * Antenna V5 control core. See antenna_core.h.
 *
 * Azimuth: zero-order Sugeno fuzzy controller, 2 inputs x 5 triangular sets,
 * 25 rules, product AND, weighted-average defuzzification:
 *     x1 = e / E,  x2 = -omega_hat / V,  u = F(x1, x2),  v_des = v_max * u
 * followed by a stopping-distance governor and an acceleration limit. The
 * planned velocity is smoothed by a moving average of smooth_n periods before
 * it becomes the STEP rate: the antenna inertia on the belt and the stepper's
 * magnetic stiffness form a ~11 Hz torsional mode (see Simulation_V5), and a
 * ramp of acceleration lasting one period of that mode does not excite it.
 * The displacement still held in the filter ("pending") is added to the
 * measured angle, so the loop plans with the position the antenna will reach.
 * The STEP rate is converted to a half period for the TB6600 (1/16 microstep,
 * 4:1 GT2 belt -> 12800 STEP per antenna revolution).
 *
 * Elevation: the LD-1501MG keeps its internal position loop; the core only
 * ramps the angle command and maps it to a pulse width.
 */
#include "antenna_core.h"

#include <math.h>
#include <string.h>

#define DEG(x) ((x) * (ACORE_PI / 180.0f))

static float clampf(float x, float lo, float hi)
{
	return x < lo ? lo : (x > hi ? hi : x);
}

float acore_wrap_pi(float x)
{
	while (x > ACORE_PI) {
		x -= ACORE_TWO_PI;
	}
	while (x <= -ACORE_PI) {
		x += ACORE_TWO_PI;
	}
	return x;
}

void acore_params_default(acore_params_t *p)
{
	static const float centre[ACORE_NMF] = {-1.0f, -0.5f, 0.0f, 0.5f, 1.0f};

	memset(p, 0, sizeof(*p));
	p->ts = 0.01f;
	p->steps_rev = 200.0f * 16.0f * 4.0f;
	p->sensor_sign = 1;
	p->motor_sign = 1;
	p->zero_valid = 0;
	p->ctrl = ACORE_CTRL_FUZZY;
	p->zero_rad = 0.0f;

	p->az_min = DEG(-150.0f);
	p->az_max = DEG(150.0f);
	p->az_fault = DEG(155.0f);

	p->vel_src = ACORE_VEL_COMMAND;
	p->glitch_n = 3;
	p->smooth_n = 13; /* 130 ms >= one period of the ~11 Hz mode */
	/* Tuned on the V5 model (Simulation_V5/v5_tune): fastest set whose true
	 * antenna speed stays <= 30 deg/s with margin, POT <= 2 %. */
	p->e_scale = DEG(6.0f);
	p->de_scale = DEG(26.0f);
	p->v_max = DEG(26.0f);
	p->mf_e_in = 0.5f;
	p->mf_de_in = 0.5f;
	/* Rule base: u = sat(2*c_e + 0.5*c_de) on the nominal centres. Rows = e
	 * (NB NS ZE PS PB), columns = de/dt = -omega (NB NS ZE PS PB). */
	for (int i = 0; i < ACORE_NMF; i++) {
		for (int j = 0; j < ACORE_NMF; j++) {
			p->rules[i][j] = clampf(2.0f * centre[i] + 0.5f * centre[j], -1.0f, 1.0f);
		}
	}
	p->kp_lin = 5.8f; /* same small-signal gain as the fuzzy surface */

	p->accel = DEG(60.0f);
	p->db_in = DEG(0.03f);
	p->db_out = DEG(0.10f);
	p->vf_alpha = 0.3f;
	p->hp_min_us = 100.0f;

	p->trk_err = DEG(4.0f);
	p->trk_time = 0.3f;
	p->resync_time = 0.5f;
	p->glitch = DEG(3.0f);
	p->hb_timeout = 2.0f;

	p->el_min = DEG(45.0f);
	p->el_max = DEG(135.0f);
	p->el_rate = DEG(30.0f);
	p->el_init = DEG(90.0f);
	p->el_ref = DEG(90.0f);
	p->us_ref = 1500.0f;
	p->us_per_rad = 2000.0f / ACORE_PI; /* 500..2500 us = 0..180 deg nominal */
	p->us_min = 1000.0f;
	p->us_max = 2000.0f;

	/* Reference sequence of the course assignment: 60,150,30,90 deg, 12 s each. */
	p->seq_dwell = 12.0f;
	p->seq_n = 4;
	p->seq_az[0] = DEG(60.0f);
	p->seq_az[1] = DEG(150.0f);
	p->seq_az[2] = DEG(30.0f);
	p->seq_az[3] = DEG(90.0f);
	p->seq_el[0] = DEG(60.0f);
	p->seq_el[1] = DEG(90.0f);
	p->seq_el[2] = DEG(120.0f);
	p->seq_el[3] = DEG(80.0f);
}

int acore_params_check(const acore_params_t *p)
{
	if (!(p->ts >= 0.002f && p->ts <= 0.05f)) {
		return 1;
	}
	if (!(p->steps_rev >= 200.0f && p->steps_rev <= 409600.0f)) {
		return 2;
	}
	if ((p->sensor_sign != 1 && p->sensor_sign != -1) ||
	    (p->motor_sign != 1 && p->motor_sign != -1)) {
		return 3;
	}
	if (!(p->az_min < p->az_max && p->az_max < p->az_fault && -p->az_min < p->az_fault &&
	      p->az_fault < ACORE_PI)) {
		return 4;
	}
	if (!(p->e_scale > 0.0f && p->de_scale > 0.0f && p->v_max > 0.0f && p->v_max < 3.0f)) {
		return 5;
	}
	if (!(p->mf_e_in > 0.05f && p->mf_e_in < 0.95f && p->mf_de_in > 0.05f &&
	      p->mf_de_in < 0.95f)) {
		return 6;
	}
	for (int i = 0; i < ACORE_NMF; i++) {
		for (int j = 0; j < ACORE_NMF; j++) {
			if (!(p->rules[i][j] >= -1.0f && p->rules[i][j] <= 1.0f)) {
				return 7;
			}
		}
	}
	if (!(p->accel > 0.0f && p->db_in >= 0.0f && p->db_out >= p->db_in &&
	      p->vf_alpha > 0.0f && p->vf_alpha <= 1.0f && p->hp_min_us >= 20.0f)) {
		return 8;
	}
	if (!(p->trk_err > 0.0f && p->trk_time > 0.0f && p->glitch > 0.0f && p->glitch_n >= 1 &&
	      p->hb_timeout >= 0.0f && p->resync_time > 0.0f)) {
		return 9;
	}
	if (!(p->el_min < p->el_max && p->el_rate > 0.0f && p->us_min >= 400.0f &&
	      p->us_max <= 2600.0f && p->us_min < p->us_max && p->us_per_rad != 0.0f)) {
		return 10;
	}
	if (!(p->ctrl <= ACORE_CTRL_LINEAR && p->vel_src <= ACORE_VEL_MEASURED &&
	      p->kp_lin > 0.0f)) {
		return 11;
	}
	if (!(p->seq_n <= ACORE_SEQ_MAX && p->seq_dwell > 0.0f)) {
		return 12;
	}
	if (!(p->smooth_n >= 1 && p->smooth_n <= ACORE_SMOOTH_MAX)) {
		return 13;
	}
	return 0;
}

/* Five triangular sets with centres -1,-a,0,a,1 (Ruspini partition). Each
 * set is evaluated like MATLAB trimf; the outer sets have virtual feet beyond
 * +-1 so that the input, clamped to [-1,1], keeps membership 1 at the ends. */
void acore_memberships(float x, float inner, float mu[ACORE_NMF])
{
	const float c[ACORE_NMF] = {-1.0f, -inner, 0.0f, inner, 1.0f};

	x = clampf(x, -1.0f, 1.0f);
	for (int k = 0; k < ACORE_NMF; k++) {
		float a = (k == 0) ? c[0] - (c[1] - c[0]) : c[k - 1];
		float b = c[k];
		float d = (k == ACORE_NMF - 1) ? c[4] + (c[4] - c[3]) : c[k + 1];
		float up = (x - a) / (b - a);
		float down = (d - x) / (d - b);
		float m = up < down ? up : down;

		mu[k] = m > 0.0f ? m : 0.0f;
	}
}

float acore_fuzzy(const acore_params_t *p, float x1, float x2)
{
	float m1[ACORE_NMF], m2[ACORE_NMF];
	float num = 0.0f, den = 0.0f;

	acore_memberships(x1, p->mf_e_in, m1);
	acore_memberships(x2, p->mf_de_in, m2);
	/* 25 rules: IF e is E_i AND de is D_j THEN u = r_ij (product AND). */
	for (int i = 0; i < ACORE_NMF; i++) {
		for (int j = 0; j < ACORE_NMF; j++) {
			float w = m1[i] * m2[j];

			num += w * p->rules[i][j];
			den += w;
		}
	}
	return den > 0.0f ? num / den : 0.0f;
}

float acore_sensor_angle(const acore_params_t *p, uint16_t raw)
{
	float phi = (float)(raw & (ACORE_SENSOR_COUNTS - 1u)) *
		    (ACORE_TWO_PI / (float)ACORE_SENSOR_COUNTS);

	if (p->cal_a1 != 0.0f || p->cal_b1 != 0.0f || p->cal_a2 != 0.0f || p->cal_b2 != 0.0f) {
		phi -= p->cal_a1 * cosf(phi) + p->cal_b1 * sinf(phi) +
		       p->cal_a2 * cosf(2.0f * phi) + p->cal_b2 * sinf(2.0f * phi);
	}
	return phi;
}

float acore_raw_to_az(const acore_params_t *p, uint16_t raw)
{
	float d = acore_wrap_pi(acore_sensor_angle(p, raw) - p->zero_rad);

	return p->sensor_sign > 0 ? d : -d;
}

/* Largest speed from which a ZOH velocity command, reduced by accel*ts per
 * period, stops within abs_err: v^2/(2a) + v*ts/2 = |e|. */
float acore_brake_speed(float accel, float ts, float abs_err)
{
	float h = 0.5f * accel * ts;

	return sqrtf(h * h + 2.0f * accel * abs_err) - h;
}

uint32_t acore_velocity_to_half_period(const acore_params_t *p, float v)
{
	float f = fabsf(v) * p->steps_rev * (1.0f / ACORE_TWO_PI); /* STEP/s */
	float hp;

	if (f < 500000.0f / 65535.0f) {
		return 0u; /* slower than the 16-bit timer allows: no stepping */
	}
	hp = 500000.0f / f + 0.5f;
	if (hp < p->hp_min_us) {
		hp = p->hp_min_us;
	}
	if (hp > 65535.0f) {
		hp = 65535.0f;
	}
	return (uint32_t)hp;
}

uint16_t acore_servo_us(const acore_params_t *p, float el)
{
	float us = p->us_ref + (el - p->el_ref) * p->us_per_rad;

	us = clampf(us, p->us_min, p->us_max);
	return (uint16_t)(us + 0.5f);
}

void acore_init(acore_t *c, const acore_params_t *p)
{
	memset(c, 0, sizeof(*c));
	c->first = 1;
	c->mode = p->zero_valid ? ACORE_MODE_ACTIVE : ACORE_MODE_NOZERO;
	if (acore_params_check(p) != 0) {
		c->mode = ACORE_MODE_FAULT;
		c->fault = ACORE_F_PARAM;
	}
	c->el_cmd = clampf(p->el_init, p->el_min, p->el_max);
	c->el_target = c->el_cmd;
	c->out.servo_us = acore_servo_us(p, c->el_cmd);
	c->out.dir = 1;
}

static void clear_motion(acore_t *c)
{
	c->v_cmd = 0.0f;
	c->v_des = 0.0f;
	c->v_out = 0.0f;
	c->pending = 0.0f;
	memset(c->vhist, 0, sizeof(c->vhist));
}

static void enter_fault(acore_t *c, uint16_t bits)
{
	c->fault |= bits;
	c->mode = ACORE_MODE_FAULT;
	clear_motion(c);
	c->seq_active = 0;
	c->hb_required = 0;
	c->el_target = c->el_cmd; /* servo holds where it is */
}

static void resync(acore_t *c, const acore_in_t *in)
{
	c->step_ref = in->steps;
	c->theta_ref = c->theta;
	c->trk_timer = 0.0f;
	c->trk_dev = 0.0f;
}

static void sequence_point(acore_t *c, const acore_params_t *p)
{
	uint8_t i = c->seq_idx;

	c->target = clampf(p->seq_az[i], p->az_min, p->az_max);
	c->el_target = clampf(p->seq_el[i], p->el_min, p->el_max);
	c->settled = 0;
	c->seq_timer = 0.0f;
}

void acore_step(acore_t *c, const acore_params_t *p, const acore_in_t *in, acore_out_t *out)
{
	const float ts = p->ts;
	const float step_angle = ACORE_TWO_PI / p->steps_rev;

	c->tick++;

	/* ---- 1. Measurement: MT6701 -> calibrated azimuth, plausibility ---- */
	if (c->first) {
		if (in->sensor_ok) {
			c->theta = acore_raw_to_az(p, in->raw);
			c->target = c->theta;
			c->first = 0;
			c->settled = 1;
			c->bad_count = 0;
			resync(c, in);
		} else if (++c->bad_count >= p->glitch_n) {
			enter_fault(c, ACORE_F_SENSOR);
		}
	} else {
		float predicted = c->theta + c->v_out * ts;
		float th = in->sensor_ok ? acore_raw_to_az(p, in->raw) : predicted;
		float d = acore_wrap_pi(th - c->theta);

		if (!in->sensor_ok || fabsf(d) > p->glitch) {
			/* reject the sample, coast on the commanded motion */
			if (c->bad_count < 255u) {
				c->bad_count++;
			}
			th = acore_wrap_pi(predicted);
			d = acore_wrap_pi(th - c->theta);
			if (c->bad_count >= p->glitch_n) {
				enter_fault(c, ACORE_F_SENSOR);
			}
		} else {
			c->bad_count = 0;
		}
		c->theta = th;
		c->w_meas += p->vf_alpha * (d / ts - c->w_meas);
	}

	/* ---- 2. Supervision ---- */
	if (in->overrun) {
		if (++c->overrun_count >= 3u) {
			enter_fault(c, ACORE_F_OVERRUN);
		}
	} else {
		c->overrun_count = 0;
	}
	if (!c->first && c->mode != ACORE_MODE_NOZERO && fabsf(c->theta) > p->az_fault) {
		enter_fault(c, ACORE_F_LIMIT);
	}
	if (c->hb_required) {
		if (in->heartbeat) {
			c->hb_age = 0.0f;
		} else {
			c->hb_age += ts;
		}
		if (p->hb_timeout > 0.0f && c->hb_age > p->hb_timeout) {
			enter_fault(c, ACORE_F_HEARTBEAT);
		}
	}
	if (!c->first) {
		if (c->out.half_period_us == 0u && c->v_cmd == 0.0f && c->v_out == 0.0f) {
			c->idle_time += ts;
			if (c->idle_time >= p->resync_time) {
				resync(c, in); /* absorb backlash / belt preload offsets */
			}
		} else {
			c->idle_time = 0.0f;
		}
		c->trk_dev = (float)(in->steps - c->step_ref) * step_angle - (c->theta - c->theta_ref);
		if (c->mode == ACORE_MODE_ACTIVE && fabsf(c->trk_dev) > p->trk_err) {
			c->trk_timer += ts;
			if (c->trk_timer >= p->trk_time) {
				enter_fault(c, ACORE_F_STALL);
			}
		} else {
			c->trk_timer = 0.0f;
		}
	}

	/* ---- 3. Built-in sequence ---- */
	if (c->seq_active && c->mode == ACORE_MODE_ACTIVE) {
		/* point k is applied at the step whose time is k*dwell (first by the command) */
		if (c->seq_timer >= p->seq_dwell - 0.5f * ts) {
			c->seq_idx++;
			if (c->seq_idx >= p->seq_n) {
				if (c->seq_loop) {
					c->seq_idx = 0;
				} else {
					c->seq_active = 0;
				}
			}
			if (c->seq_active) {
				sequence_point(c, p);
			}
		}
		c->seq_timer += ts;
	}

	/* ---- 4. Azimuth control law ---- */
	if (c->mode == ACORE_MODE_ACTIVE && !c->first) {
		/* plan from the position reached once the smoothing filter has emptied;
		 * no wrap: the travel never crosses +-180 deg */
		float e = c->target - (c->theta + c->pending);
		float ae = fabsf(e);

		if (c->settled) {
			if (ae > p->db_out) {
				c->settled = 0;
			}
		} else if (ae < p->db_in) {
			c->settled = 1;
		}
		if (c->settled) {
			c->v_des = 0.0f;
			c->u_fz = 0.0f;
		} else {
			float vb;

			if (p->ctrl == ACORE_CTRL_FUZZY) {
				float w_hat = (p->vel_src == ACORE_VEL_COMMAND) ? c->v_cmd : c->w_meas;
				float x1 = clampf(e / p->e_scale, -1.0f, 1.0f);
				float x2 = clampf(-w_hat / p->de_scale, -1.0f, 1.0f);

				c->u_fz = acore_fuzzy(p, x1, x2);
				c->v_des = p->v_max * c->u_fz;
			} else {
				c->u_fz = 0.0f;
				c->v_des = clampf(p->kp_lin * e, -p->v_max, p->v_max);
			}
			/* stopping-distance governor (kinematic limit, not a fuzzy rule) */
			vb = acore_brake_speed(p->accel, ts, ae);
			c->v_des = clampf(c->v_des, -vb, vb);
		}
		c->v_cmd += clampf(c->v_des - c->v_cmd, -p->accel * ts, p->accel * ts);
	} else {
		clear_motion(c);
		c->u_fz = 0.0f;
	}

	/* ---- 4b. Command smoothing: moving average over smooth_n periods ---- */
	if (p->smooth_n != c->vh_n) {
		memset(c->vhist, 0, sizeof(c->vhist));
		c->vh_n = p->smooth_n;
	}
	if (c->vh_n <= 1u) {
		c->v_out = c->v_cmd;
		c->pending = 0.0f;
	} else {
		float sum = 0.0f;
		int idle = 1;

		c->vhist[c->tick % c->vh_n] = c->v_cmd;
		for (unsigned i = 0; i < c->vh_n; i++) {
			sum += c->vhist[i];
			if (c->vhist[i] != 0.0f) {
				idle = 0;
			}
		}
		c->v_out = sum / (float)c->vh_n;
		c->pending = idle ? 0.0f : c->pending + (c->v_cmd - c->v_out) * ts;
	}

	/* ---- 5. Elevation command ramp ---- */
	if (c->mode != ACORE_MODE_FAULT) {
		c->el_cmd += clampf(c->el_target - c->el_cmd, -p->el_rate * ts, p->el_rate * ts);
	}

	/* ---- 6. Outputs ---- */
	c->out.half_period_us = acore_velocity_to_half_period(p, c->v_out);
	if (c->out.half_period_us != 0u) {
		c->out.dir = c->v_out > 0.0f ? 1 : -1;
	}
	c->out.settled = c->settled;
	c->out.servo_us = acore_servo_us(p, c->el_cmd);
	*out = c->out;
}

int acore_cmd_goto(acore_t *c, const acore_params_t *p, uint8_t mask, float az, float el,
		   uint8_t host_owned)
{
	if (c->mode == ACORE_MODE_FAULT) {
		return -1;
	}
	if ((mask & ACORE_GOTO_AZ) && (c->mode == ACORE_MODE_NOZERO || c->first)) {
		return -2;
	}
	if (az != az || el != el) { /* NaN */
		return -3;
	}
	if (mask & ACORE_GOTO_AZ) {
		c->target = clampf(az, p->az_min, p->az_max);
		c->settled = 0;
	}
	if (mask & ACORE_GOTO_EL) {
		c->el_target = clampf(el, p->el_min, p->el_max);
	}
	c->seq_active = 0;
	c->hb_required = (host_owned && p->hb_timeout > 0.0f) ? 1u : 0u;
	c->hb_age = 0.0f;
	return 0;
}

void acore_cmd_stop(acore_t *c, const acore_params_t *p)
{
	c->seq_active = 0;
	c->hb_required = 0;
	if (c->mode == ACORE_MODE_ACTIVE && !c->first) {
		/* decelerate at the configured rate, then hold */
		float v = c->v_cmd;
		float dist = v * fabsf(v) / (2.0f * p->accel) + 0.5f * v * p->ts;

		c->target = clampf(c->theta + c->pending + dist, p->az_min, p->az_max);
		c->settled = 0;
	}
	c->el_target = c->el_cmd;
}

void acore_cmd_estop(acore_t *c)
{
	enter_fault(c, ACORE_F_ESTOP);
}

int acore_cmd_clear(acore_t *c, const acore_params_t *p)
{
	if (acore_params_check(p) != 0) {
		enter_fault(c, ACORE_F_PARAM);
		return -1;
	}
	c->fault = 0;
	c->bad_count = 0;
	c->overrun_count = 0;
	c->hb_required = 0;
	c->trk_timer = 0.0f;
	clear_motion(c);
	c->target = c->theta;
	c->settled = 1;
	c->idle_time = p->resync_time; /* STEP/sensor references resync at the next step */
	c->mode = p->zero_valid ? ACORE_MODE_ACTIVE : ACORE_MODE_NOZERO;
	return 0;
}

int acore_cmd_sequence(acore_t *c, const acore_params_t *p, uint8_t loop)
{
	if (c->mode != ACORE_MODE_ACTIVE || c->first || p->seq_n == 0u) {
		return -1;
	}
	c->seq_active = 1;
	c->seq_loop = loop ? 1u : 0u;
	c->seq_idx = 0;
	c->hb_required = 0;
	sequence_point(c, p);
	return 0;
}

int acore_set_zero(acore_t *c, acore_params_t *p, uint16_t raw, float az_now)
{
	float phi = acore_sensor_angle(p, raw);

	if (c->mode == ACORE_MODE_ACTIVE &&
	    (c->v_cmd != 0.0f || c->v_out != 0.0f || c->out.half_period_us != 0u)) {
		return -1; /* only while stopped */
	}
	if (fabsf(az_now) > p->az_max) {
		return -2;
	}
	p->zero_rad = acore_wrap_pi(phi - (p->sensor_sign > 0 ? az_now : -az_now));
	p->zero_valid = 1;
	c->theta = acore_raw_to_az(p, raw);
	c->target = c->theta;
	c->settled = 1;
	c->w_meas = 0.0f;
	c->idle_time = p->resync_time;
	if (c->mode == ACORE_MODE_NOZERO) {
		c->mode = ACORE_MODE_ACTIVE;
	}
	return 0;
}
