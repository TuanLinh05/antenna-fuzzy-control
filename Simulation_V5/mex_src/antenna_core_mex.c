/*
 * MEX gateway to the firmware control core (../../Firmware/antenna_zephyr/core).
 * MATLAB runs exactly the C code that is flashed into the STM32 (SIL test).
 *
 *   p   = antenna_core_mex('defaults')            acore_params_default
 *   p   = antenna_core_mex('params')              parameters in use
 *         antenna_core_mex('init', p)             set parameters + acore_init
 *   y   = antenna_core_mex('step', raw, ok, hb, overrun, steps)
 *         y = [hp dir settled servo_us mode fault theta w_meas v_cmd v_des u_fz
 *              target el_cmd trk_dev bad_count v_out pending]
 *   rc  = antenna_core_mex('goto', mask, az, el, host) | ('stop') | ('estop')
 *         | ('clear') | ('sequence', loop) | ('zero', raw, az)
 *   u   = antenna_core_mex('fuzzy', x1, x2)        element-wise, single output
 *   s   = antenna_core_mex('state')
 *         antenna_core_mex('sg_init', guard_us)
 *   iv  = antenna_core_mex('sg_command', hp, dir)
 *   iv  = antenna_core_mex('sg_retime', elapsed_us)
 *   y   = antenna_core_mex('sg_tick')   y = [interval step_level dir dir_changed stepped steps]
 *   v   = antenna_core_mex('version')   [ACORE_VERSION sizeof(acore_params_t)]
 */
#include <math.h>
#include <stddef.h>
#include <string.h>

#include "mex.h"

#include "antenna_core.h"
#include "stepgen.h"

static acore_params_t P;
static acore_t C;
static stepgen_t SG;
static int initialised;

enum { T_F32, T_I8, T_U8, T_RULES, T_SEQ };
typedef struct {
	const char *name;
	size_t off;
	int type;
	int n;
} field_t;

#define F(n) {#n, offsetof(acore_params_t, n), T_F32, 1}
#define I8(n) {#n, offsetof(acore_params_t, n), T_I8, 1}
#define U8(n) {#n, offsetof(acore_params_t, n), T_U8, 1}

static const field_t fields[] = {
	F(ts), F(steps_rev), I8(sensor_sign), I8(motor_sign), U8(zero_valid), U8(ctrl),
	F(zero_rad), F(cal_a1), F(cal_b1), F(cal_a2), F(cal_b2), F(az_min), F(az_max),
	F(az_fault), U8(vel_src), U8(glitch_n), U8(smooth_n), F(e_scale), F(de_scale), F(v_max), F(mf_e_in),
	F(mf_de_in), {"rules", offsetof(acore_params_t, rules), T_RULES, 25}, F(kp_lin), F(accel),
	F(db_in), F(db_out), F(vf_alpha), F(hp_min_us), F(trk_err), F(trk_time), F(resync_time),
	F(glitch), F(hb_timeout), F(el_min), F(el_max), F(el_rate), F(el_init), F(el_ref),
	F(us_ref), F(us_per_rad), F(us_min), F(us_max), F(seq_dwell), U8(seq_n),
	{"seq_az", offsetof(acore_params_t, seq_az), T_SEQ, ACORE_SEQ_MAX},
	{"seq_el", offsetof(acore_params_t, seq_el), T_SEQ, ACORE_SEQ_MAX},
};
#define NFIELDS (sizeof(fields) / sizeof(fields[0]))

static mxArray *params_to_struct(const acore_params_t *p)
{
	const char *names[NFIELDS];
	mxArray *s;

	for (size_t k = 0; k < NFIELDS; k++) {
		names[k] = fields[k].name;
	}
	s = mxCreateStructMatrix(1, 1, (int)NFIELDS, names);
	for (size_t k = 0; k < NFIELDS; k++) {
		const unsigned char *src = (const unsigned char *)p + fields[k].off;
		mxArray *v = NULL;

		switch (fields[k].type) {
		case T_F32:
			v = mxCreateNumericMatrix(1, 1, mxSINGLE_CLASS, mxREAL);
			memcpy(mxGetData(v), src, sizeof(float));
			break;
		case T_I8:
			v = mxCreateNumericMatrix(1, 1, mxINT8_CLASS, mxREAL);
			memcpy(mxGetData(v), src, 1);
			break;
		case T_U8:
			v = mxCreateNumericMatrix(1, 1, mxUINT8_CLASS, mxREAL);
			memcpy(mxGetData(v), src, 1);
			break;
		case T_RULES: {
			float *dst;

			v = mxCreateNumericMatrix(5, 5, mxSINGLE_CLASS, mxREAL);
			dst = (float *)mxGetData(v);
			for (int i = 0; i < 5; i++) {
				for (int j = 0; j < 5; j++) {
					dst[i + 5 * j] = p->rules[i][j];
				}
			}
			break;
		}
		case T_SEQ:
			v = mxCreateNumericMatrix(1, ACORE_SEQ_MAX, mxSINGLE_CLASS, mxREAL);
			memcpy(mxGetData(v), src, sizeof(float) * ACORE_SEQ_MAX);
			break;
		}
		mxSetFieldByNumber(s, 0, (int)k, v);
	}
	return s;
}

static void struct_to_params(const mxArray *s, acore_params_t *p)
{
	if (!mxIsStruct(s)) {
		mexErrMsgIdAndTxt("antenna_core_mex:params", "parameter struct expected");
	}
	for (size_t k = 0; k < NFIELDS; k++) {
		const mxArray *v = mxGetField(s, 0, fields[k].name);
		unsigned char *dst = (unsigned char *)p + fields[k].off;
		size_t n;

		if (!v) {
			mexErrMsgIdAndTxt("antenna_core_mex:params", "missing field %s", fields[k].name);
		}
		n = mxGetNumberOfElements(v);
		if ((int)n != fields[k].n) {
			mexErrMsgIdAndTxt("antenna_core_mex:params", "field %s: %d elements expected",
					  fields[k].name, fields[k].n);
		}
		switch (fields[k].type) {
		case T_F32: {
			float f = (float)mxGetScalar(v);

			memcpy(dst, &f, sizeof(f));
			break;
		}
		case T_I8:
			*(int8_t *)dst = (int8_t)mxGetScalar(v);
			break;
		case T_U8:
			*(uint8_t *)dst = (uint8_t)mxGetScalar(v);
			break;
		case T_RULES:
		case T_SEQ: {
			float *fd = (float *)dst;

			for (size_t i = 0; i < n; i++) {
				double x;

				if (mxIsSingle(v)) {
					x = ((const float *)mxGetData(v))[i];
				} else if (mxIsDouble(v)) {
					x = mxGetPr(v)[i];
				} else {
					mexErrMsgIdAndTxt("antenna_core_mex:params", "%s must be single or double",
							  fields[k].name);
					x = 0.0;
				}
				if (fields[k].type == T_RULES) {
					/* MATLAB column-major (i + 5 j) -> C rules[i][j] */
					p->rules[i % 5][i / 5] = (float)x;
				} else {
					fd[i] = (float)x;
				}
			}
			break;
		}
		}
	}
}

static double arg(int nrhs, const mxArray *prhs[], int k)
{
	if (k >= nrhs) {
		mexErrMsgIdAndTxt("antenna_core_mex:args", "missing argument %d", k);
	}
	return mxGetScalar(prhs[k]);
}

static mxArray *row(const double *v, int n)
{
	mxArray *m = mxCreateDoubleMatrix(1, (mwSize)n, mxREAL);

	memcpy(mxGetPr(m), v, sizeof(double) * (size_t)n);
	return m;
}

static mxArray *scalar(double v)
{
	return mxCreateDoubleScalar(v);
}

static mxArray *state_struct(void)
{
	static const char *names[] = {"tick", "mode", "first", "settled", "hb_required", "fault",
				      "bad_count", "theta", "w_meas", "v_cmd", "v_des", "u_fz",
				      "target", "hb_age", "trk_timer", "idle_time", "trk_dev",
				      "step_ref", "theta_ref", "el_cmd", "el_target", "seq_active",
				      "seq_idx", "seq_timer", "half_period_us", "dir", "servo_us",
				      "v_out", "pending"};
	const double v[] = {C.tick, C.mode, C.first, C.settled, C.hb_required, C.fault,
			    C.bad_count, C.theta, C.w_meas, C.v_cmd, C.v_des, C.u_fz,
			    C.target, C.hb_age, C.trk_timer, C.idle_time, C.trk_dev,
			    C.step_ref, C.theta_ref, C.el_cmd, C.el_target, C.seq_active,
			    C.seq_idx, C.seq_timer, C.out.half_period_us, C.out.dir,
			    C.out.servo_us, C.v_out, C.pending};
	const int n = (int)(sizeof(names) / sizeof(names[0]));
	mxArray *s = mxCreateStructMatrix(1, 1, n, names);

	for (int k = 0; k < n; k++) {
		mxSetFieldByNumber(s, 0, k, scalar(v[k]));
	}
	return s;
}

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{
	char cmd[32];

	(void)nlhs;
	if (nrhs < 1 || mxGetString(prhs[0], cmd, sizeof(cmd)) != 0) {
		mexErrMsgIdAndTxt("antenna_core_mex:args", "first argument must be a command string");
	}
	if (!initialised) {
		acore_params_default(&P);
		acore_init(&C, &P);
		stepgen_init(&SG, 50u);
		initialised = 1;
	}

	if (!strcmp(cmd, "defaults")) {
		acore_params_t d;

		acore_params_default(&d);
		plhs[0] = params_to_struct(&d);
	} else if (!strcmp(cmd, "params")) {
		plhs[0] = params_to_struct(&P);
	} else if (!strcmp(cmd, "init")) {
		if (nrhs > 1) {
			struct_to_params(prhs[1], &P);
		}
		acore_init(&C, &P);
		plhs[0] = scalar(acore_params_check(&P));
	} else if (!strcmp(cmd, "step")) {
		acore_in_t in;
		acore_out_t out;
		double y[17];

		memset(&in, 0, sizeof(in));
		in.raw = (uint16_t)arg(nrhs, prhs, 1);
		in.sensor_ok = arg(nrhs, prhs, 2) != 0.0;
		in.heartbeat = arg(nrhs, prhs, 3) != 0.0;
		in.overrun = arg(nrhs, prhs, 4) != 0.0;
		in.steps = (int32_t)arg(nrhs, prhs, 5);
		acore_step(&C, &P, &in, &out);
		y[0] = out.half_period_us;
		y[1] = out.dir;
		y[2] = out.settled;
		y[3] = out.servo_us;
		y[4] = C.mode;
		y[5] = C.fault;
		y[6] = C.theta;
		y[7] = C.w_meas;
		y[8] = C.v_cmd;
		y[9] = C.v_des;
		y[10] = C.u_fz;
		y[11] = C.target;
		y[12] = C.el_cmd;
		y[13] = C.trk_dev;
		y[14] = C.bad_count;
		y[15] = C.v_out;
		y[16] = C.pending;
		plhs[0] = row(y, 17);
	} else if (!strcmp(cmd, "goto")) {
		plhs[0] = scalar(acore_cmd_goto(&C, &P, (uint8_t)arg(nrhs, prhs, 1),
						(float)arg(nrhs, prhs, 2), (float)arg(nrhs, prhs, 3),
						(uint8_t)(arg(nrhs, prhs, 4) != 0.0)));
	} else if (!strcmp(cmd, "stop")) {
		acore_cmd_stop(&C, &P);
		plhs[0] = scalar(0);
	} else if (!strcmp(cmd, "estop")) {
		acore_cmd_estop(&C);
		plhs[0] = scalar(0);
	} else if (!strcmp(cmd, "clear")) {
		plhs[0] = scalar(acore_cmd_clear(&C, &P));
	} else if (!strcmp(cmd, "sequence")) {
		plhs[0] = scalar(acore_cmd_sequence(&C, &P, (uint8_t)(arg(nrhs, prhs, 1) != 0.0)));
	} else if (!strcmp(cmd, "zero")) {
		plhs[0] = scalar(acore_set_zero(&C, &P, (uint16_t)arg(nrhs, prhs, 1),
						(float)arg(nrhs, prhs, 2)));
	} else if (!strcmp(cmd, "fuzzy")) {
		size_t n;
		float *u;

		if (nrhs < 3 || mxGetNumberOfElements(prhs[1]) != mxGetNumberOfElements(prhs[2]) ||
		    !mxIsDouble(prhs[1]) || !mxIsDouble(prhs[2])) {
			mexErrMsgIdAndTxt("antenna_core_mex:args", "fuzzy(x1, x2): double arrays of equal size");
		}
		n = mxGetNumberOfElements(prhs[1]);
		plhs[0] = mxCreateNumericArray(mxGetNumberOfDimensions(prhs[1]),
					       mxGetDimensions(prhs[1]), mxSINGLE_CLASS, mxREAL);
		u = (float *)mxGetData(plhs[0]);
		for (size_t k = 0; k < n; k++) {
			u[k] = acore_fuzzy(&P, (float)mxGetPr(prhs[1])[k], (float)mxGetPr(prhs[2])[k]);
		}
	} else if (!strcmp(cmd, "state")) {
		plhs[0] = state_struct();
	} else if (!strcmp(cmd, "sg_init")) {
		stepgen_init(&SG, (uint32_t)arg(nrhs, prhs, 1));
		plhs[0] = scalar(0);
	} else if (!strcmp(cmd, "sg_command")) {
		plhs[0] = scalar(stepgen_command(&SG, (uint32_t)arg(nrhs, prhs, 1),
						 (int8_t)arg(nrhs, prhs, 2)));
	} else if (!strcmp(cmd, "sg_retime")) {
		plhs[0] = scalar(stepgen_retime(&SG, (uint32_t)arg(nrhs, prhs, 1)));
	} else if (!strcmp(cmd, "sg_tick")) {
		stepgen_pins_t pins;
		uint32_t iv = stepgen_tick(&SG, &pins);
		double y[6] = {iv, pins.step_level, pins.dir, pins.dir_changed, pins.stepped, SG.steps};

		plhs[0] = row(y, 6);
	} else if (!strcmp(cmd, "version")) {
		double y[2] = {ACORE_VERSION, (double)sizeof(acore_params_t)};

		plhs[0] = row(y, 2);
	} else {
		mexErrMsgIdAndTxt("antenna_core_mex:args", "unknown command '%s'", cmd);
	}
}
