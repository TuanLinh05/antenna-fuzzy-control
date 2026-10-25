/*
 * Antenna V5 control core - portable C99, no RTOS or hardware dependency.
 *
 * The same source is compiled into:
 *   - the Zephyr firmware for STM32F103 (Blue Pill),
 *   - the MATLAB MEX used for software-in-the-loop (SIL) simulation,
 *   - the host unit tests and the virtual board used to test the PIL link.
 *
 * Units inside the core are SI: rad, rad/s, rad/s^2, s. Azimuth is the
 * antenna (output) shaft angle measured by the MT6701 after the 4:1 belt.
 * Positive azimuth = increasing calibrated sensor angle (after sensor_sign).
 */
#ifndef ANTENNA_CORE_H
#define ANTENNA_CORE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ACORE_VERSION        0x0106u   /* bump when params layout changes */
#define ACORE_PI             3.14159265358979323846f
#define ACORE_TWO_PI         6.28318530717958647692f
#define ACORE_SENSOR_COUNTS  16384u    /* MT6701: 14-bit absolute angle */
#define ACORE_NMF            5         /* triangular sets per input */
#define ACORE_SEQ_MAX        8
#define ACORE_SMOOTH_MAX     16        /* longest command smoothing FIR */

/* Operating modes */
enum {
	ACORE_MODE_NOZERO = 0, /* no valid mechanical zero: azimuth motion refused */
	ACORE_MODE_ACTIVE = 1, /* closed loop on target (holding or moving) */
	ACORE_MODE_FAULT  = 2  /* latched fault: no STEP, servo holds */
};

/* Fault bits (latched until 'clear') */
#define ACORE_F_HEARTBEAT 0x0001u /* host heartbeat lost while host owns motion */
#define ACORE_F_LIMIT     0x0002u /* measured azimuth outside +-az_fault */
#define ACORE_F_STALL     0x0004u /* STEP-derived and measured motion disagree */
#define ACORE_F_OVERRUN   0x0008u /* control period overran repeatedly */
#define ACORE_F_ESTOP     0x0010u /* emergency stop command */
#define ACORE_F_SENSOR    0x0020u /* MT6701 read error / implausible jumps */
#define ACORE_F_PARAM     0x0040u /* parameter set rejected by acore_params_check */

/* Controller type */
enum { ACORE_CTRL_FUZZY = 0, ACORE_CTRL_LINEAR = 1 };
/* Source of the velocity used as the fuzzy derivative input */
enum { ACORE_VEL_COMMAND = 0, ACORE_VEL_MEASURED = 1 };

typedef struct {
	/* --- timing and transmission --- */
	float ts;              /* control period [s] */
	float steps_rev;       /* STEP pulses per output-shaft revolution: 200*16*4 */
	int8_t sensor_sign;    /* +1/-1: MT6701 direction relative to azimuth */
	int8_t motor_sign;     /* +1/-1: DIR level relative to azimuth (used by firmware) */
	uint8_t zero_valid;    /* 1 when zero_rad has been set ('Z') */
	uint8_t ctrl;          /* ACORE_CTRL_* */
	float zero_rad;        /* calibrated sensor angle that maps to azimuth 0 */
	/* sensor harmonic correction: err(phi) = a1 cos phi + b1 sin phi + a2 cos 2phi + b2 sin 2phi */
	float cal_a1, cal_b1, cal_a2, cal_b2; /* [rad] */
	/* --- travel --- */
	float az_min, az_max;  /* setpoint limits [rad] */
	float az_fault;        /* |measured| above this -> LIMIT fault [rad] */
	/* --- fuzzy azimuth controller --- */
	uint8_t vel_src;       /* ACORE_VEL_* */
	uint8_t glitch_n;      /* consecutive bad sensor samples before SENSOR fault */
	uint8_t smooth_n;      /* moving-average length of the STEP velocity (1 = off) */
	uint8_t pad0;
	float e_scale;         /* error normalisation E [rad]: x1 = e/E */
	float de_scale;        /* derivative normalisation V [rad/s]: x2 = -omega/V */
	float v_max;           /* output scale [rad/s]: v = v_max * u */
	float mf_e_in;         /* inner centre of NS/PS for x1 (0..1): centres -1,-a,0,a,1 */
	float mf_de_in;        /* inner centre of NS/PS for x2 */
	float rules[ACORE_NMF][ACORE_NMF]; /* singleton u for (e_i, de_j), normalised */
	float kp_lin;          /* baseline linear controller gain [1/s] */
	/* --- motion shaping (outside the rule base) --- */
	float accel;           /* acceleration limit [rad/s^2] */
	float db_in;           /* stop stepping when |e| < db_in [rad] */
	float db_out;          /* resume when |e| > db_out [rad] (hysteresis) */
	float vf_alpha;        /* measured velocity IIR coefficient (0..1] */
	float hp_min_us;       /* minimum STEP half period [us] */
	/* --- supervision --- */
	float trk_err;         /* STEP vs sensor disagreement threshold [rad] */
	float trk_time;        /* persistence before STALL fault [s] */
	float resync_time;     /* idle time before STEP/sensor references resync [s] */
	float glitch;          /* max plausible change per sample [rad] */
	float hb_timeout;      /* host heartbeat timeout [s], 0 = disabled */
	/* --- elevation servo (LD-1501MG internal position loop) --- */
	float el_min, el_max;  /* [rad] */
	float el_rate;         /* command ramp [rad/s] */
	float el_init;         /* command at boot [rad] */
	float el_ref;          /* calibration point angle [rad] */
	float us_ref;          /* pulse at el_ref [us] */
	float us_per_rad;      /* pulse slope [us/rad] (sign = servo direction) */
	float us_min, us_max;  /* hard pulse limits [us] */
	/* --- built-in demo sequence ('Q') --- */
	float seq_dwell;       /* [s] per point */
	uint8_t seq_n;
	uint8_t pad1[3];
	float seq_az[ACORE_SEQ_MAX];
	float seq_el[ACORE_SEQ_MAX];
} acore_params_t;

typedef struct {
	uint16_t raw;          /* MT6701 14-bit angle */
	uint8_t sensor_ok;     /* 0 = bus error or invalid frame */
	uint8_t heartbeat;     /* 1 = host heartbeat received since previous step */
	uint8_t overrun;       /* 1 = previous control period was late */
	uint8_t pad[3];
	int32_t steps;         /* STEP pulses emitted so far (signed, logical direction) */
} acore_in_t;

typedef struct {
	uint32_t half_period_us; /* 0 = no stepping */
	int8_t dir;              /* +1 / -1 logical direction */
	uint8_t settled;
	uint16_t servo_us;
} acore_out_t;

typedef struct {
	uint32_t tick;
	uint8_t mode;
	uint8_t first;        /* waiting for first valid sensor sample */
	uint8_t settled;      /* deadband latch */
	uint8_t hb_required;
	uint16_t fault;
	uint8_t bad_count;
	uint8_t overrun_count;
	float theta;          /* calibrated azimuth [rad] */
	float w_meas;         /* filtered measured velocity [rad/s] */
	float v_cmd;          /* planned output velocity (accel-limited) [rad/s] */
	float v_out;          /* executed STEP velocity = moving average of v_cmd [rad/s] */
	float pending;        /* planned but not yet executed displacement [rad] */
	float v_des;          /* desired velocity before acceleration limit [rad/s] */
	float u_fz;           /* last normalised fuzzy output */
	float target;         /* azimuth target [rad] */
	float hb_age;         /* [s] */
	float trk_timer;      /* [s] */
	float idle_time;      /* [s] */
	float trk_dev;        /* last STEP-vs-sensor deviation [rad] */
	int32_t step_ref;
	float theta_ref;
	float el_cmd;         /* ramped elevation command [rad] */
	float el_target;      /* [rad] */
	uint8_t seq_active, seq_loop, seq_idx, vh_n;
	float seq_timer;      /* [s] */
	float vhist[ACORE_SMOOTH_MAX]; /* last planned velocities, slot = tick % vh_n */
	acore_out_t out;      /* last outputs */
} acore_t;

void acore_params_default(acore_params_t *p);
/* Returns 0 if valid, otherwise a positive code identifying the first bad field. */
int acore_params_check(const acore_params_t *p);

void acore_init(acore_t *c, const acore_params_t *p);
void acore_step(acore_t *c, const acore_params_t *p, const acore_in_t *in, acore_out_t *out);

/* Commands. Return 0 on success, negative if refused. They take effect at the next step. */
#define ACORE_GOTO_AZ 0x01u
#define ACORE_GOTO_EL 0x02u
int acore_cmd_goto(acore_t *c, const acore_params_t *p, uint8_t mask, float az, float el,
		   uint8_t host_owned);
void acore_cmd_stop(acore_t *c, const acore_params_t *p);
void acore_cmd_estop(acore_t *c);
int acore_cmd_clear(acore_t *c, const acore_params_t *p);
int acore_cmd_sequence(acore_t *c, const acore_params_t *p, uint8_t loop);
/* Sets p->zero_rad so that the given raw reading corresponds to azimuth az_now. */
int acore_set_zero(acore_t *c, acore_params_t *p, uint16_t raw, float az_now);

/* Building blocks, exported for tests and MATLAB comparison. */
float acore_fuzzy(const acore_params_t *p, float x1, float x2);
void acore_memberships(float x, float inner, float mu[ACORE_NMF]);
float acore_sensor_angle(const acore_params_t *p, uint16_t raw); /* calibrated, before zero */
float acore_raw_to_az(const acore_params_t *p, uint16_t raw);
float acore_brake_speed(float accel, float ts, float abs_err);
uint32_t acore_velocity_to_half_period(const acore_params_t *p, float v);
uint16_t acore_servo_us(const acore_params_t *p, float el);
float acore_wrap_pi(float x);

#ifdef __cplusplus
}
#endif
#endif /* ANTENNA_CORE_H */
