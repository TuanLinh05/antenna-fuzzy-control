/* ASCII line protocol. See link_proto.h. */
#include "link_proto.h"

#include <stddef.h>
#include <string.h>

#define DEG2RAD (ACORE_PI / 180.0f)
#define RAD2DEG (180.0f / ACORE_PI)

enum { PT_F32, PT_I8, PT_U8 };
#define PF_RO 0x01u

typedef struct {
	const char *name;
	uint16_t offset;
	uint8_t type;
	uint8_t flags;
	float scale; /* internal = user * scale */
} param_desc_t;

#define PF(n, f, s) {n, (uint16_t)offsetof(acore_params_t, f), PT_F32, 0u, s}
#define PI8(n, f)   {n, (uint16_t)offsetof(acore_params_t, f), PT_I8, 0u, 1.0f}
#define PU8(n, f)   {n, (uint16_t)offsetof(acore_params_t, f), PT_U8, 0u, 1.0f}

static const param_desc_t params[] = {
	{"ts", (uint16_t)offsetof(acore_params_t, ts), PT_F32, PF_RO, 1.0f},
	PF("steps_rev", steps_rev, 1.0f),
	PI8("sensor_sign", sensor_sign),
	PI8("motor_sign", motor_sign),
	PU8("zero_valid", zero_valid),
	PU8("ctrl", ctrl),
	PF("zero_deg", zero_rad, DEG2RAD),
	PF("cal_a1_deg", cal_a1, DEG2RAD),
	PF("cal_b1_deg", cal_b1, DEG2RAD),
	PF("cal_a2_deg", cal_a2, DEG2RAD),
	PF("cal_b2_deg", cal_b2, DEG2RAD),
	PF("az_min_deg", az_min, DEG2RAD),
	PF("az_max_deg", az_max, DEG2RAD),
	PF("az_fault_deg", az_fault, DEG2RAD),
	PU8("vel_src", vel_src),
	PU8("glitch_n", glitch_n),
	PU8("smooth_n", smooth_n),
	PF("e_scale_deg", e_scale, DEG2RAD),
	PF("de_scale_dps", de_scale, DEG2RAD),
	PF("v_max_dps", v_max, DEG2RAD),
	PF("mf_e_in", mf_e_in, 1.0f),
	PF("mf_de_in", mf_de_in, 1.0f),
	PF("kp_lin", kp_lin, 1.0f),
	PF("accel_dps2", accel, DEG2RAD),
	PF("db_in_deg", db_in, DEG2RAD),
	PF("db_out_deg", db_out, DEG2RAD),
	PF("vf_alpha", vf_alpha, 1.0f),
	PF("hp_min_us", hp_min_us, 1.0f),
	PF("trk_err_deg", trk_err, DEG2RAD),
	PF("trk_time", trk_time, 1.0f),
	PF("resync_time", resync_time, 1.0f),
	PF("glitch_deg", glitch, DEG2RAD),
	PF("hb_timeout", hb_timeout, 1.0f),
	PF("el_min_deg", el_min, DEG2RAD),
	PF("el_max_deg", el_max, DEG2RAD),
	PF("el_rate_dps", el_rate, DEG2RAD),
	PF("el_init_deg", el_init, DEG2RAD),
	PF("el_ref_deg", el_ref, DEG2RAD),
	PF("us_ref", us_ref, 1.0f),
	PF("us_per_deg", us_per_rad, RAD2DEG),
	PF("us_min", us_min, 1.0f),
	PF("us_max", us_max, 1.0f),
	PF("seq_dwell", seq_dwell, 1.0f),
	PU8("seq_n", seq_n),
};
#define NPARAMS (sizeof(params) / sizeof(params[0]))
/* plus r00..r44 (rules, normalised) and seq_az0..7 / seq_el0..7 (deg) */

typedef struct {
	void *ptr;
	uint8_t type;
	uint8_t flags;
	float scale;
} param_ref_t;

static int digit(char ch)
{
	return ch >= '0' && ch <= '9';
}

static int resolve(acore_params_t *p, const char *name, param_ref_t *r)
{
	for (size_t i = 0; i < NPARAMS; i++) {
		if (strcmp(name, params[i].name) == 0) {
			r->ptr = (uint8_t *)p + params[i].offset;
			r->type = params[i].type;
			r->flags = params[i].flags;
			r->scale = params[i].scale;
			return 0;
		}
	}
	if (name[0] == 'r' && digit(name[1]) && digit(name[2]) && name[3] == 0) {
		int i = name[1] - '0', j = name[2] - '0';

		if (i < ACORE_NMF && j < ACORE_NMF) {
			r->ptr = &p->rules[i][j];
			r->type = PT_F32;
			r->flags = 0;
			r->scale = 1.0f;
			return 0;
		}
	}
	if (strncmp(name, "seq_az", 6) == 0 || strncmp(name, "seq_el", 6) == 0) {
		if (digit(name[6]) && name[7] == 0 && name[6] - '0' < ACORE_SEQ_MAX) {
			int k = name[6] - '0';

			r->ptr = (name[5] == 'z') ? &p->seq_az[k] : &p->seq_el[k];
			r->type = PT_F32;
			r->flags = 0;
			r->scale = DEG2RAD;
			return 0;
		}
	}
	return -1;
}

/* ---------- formatting ---------- */

size_t link_fmt_i32(char *buf, int32_t v)
{
	char tmp[12];
	size_t n = 0, k = 0;
	uint32_t u = (v < 0) ? (uint32_t)(-(v + 1)) + 1u : (uint32_t)v;

	if (v < 0) {
		buf[n++] = '-';
	}
	do {
		tmp[k++] = (char)('0' + u % 10u);
		u /= 10u;
	} while (u != 0u);
	while (k) {
		buf[n++] = tmp[--k];
	}
	buf[n] = 0;
	return n;
}

size_t link_fmt_hex32(char *buf, uint32_t v)
{
	static const char hex[] = "0123456789ABCDEF";

	for (int i = 0; i < 8; i++) {
		buf[i] = hex[(v >> (28 - 4 * i)) & 0xFu];
	}
	buf[8] = 0;
	return 8;
}

/* Fixed point with 6 decimals, trailing zeros trimmed. Enough for the
 * parameter listing; exact values travel as hex. */
size_t link_fmt_float(char *buf, float v)
{
	size_t n = 0;
	uint32_t ip, fp;
	float a;

	if (v != v) {
		strcpy(buf, "nan");
		return 3;
	}
	if (v < 0.0f) {
		buf[n++] = '-';
		v = -v;
	}
	if (v > 2.0e9f) {
		strcpy(buf + n, "inf");
		return n + 3;
	}
	a = v + 0.0000005f;
	ip = (uint32_t)a;
	fp = (uint32_t)((a - (float)ip) * 1000000.0f);
	if (fp > 999999u) {
		fp = 999999u;
	}
	n += link_fmt_i32(buf + n, (int32_t)ip);
	buf[n++] = '.';
	for (uint32_t d = 100000u; d > 0u; d /= 10u) {
		buf[n++] = (char)('0' + (fp / d) % 10u);
	}
	while (buf[n - 1] == '0' && buf[n - 2] != '.') {
		n--;
	}
	buf[n] = 0;
	return n;
}

/* ---------- parsing ---------- */

static void skip_spaces(const char **s)
{
	while (**s == ' ' || **s == '\t' || **s == ',') {
		(*s)++;
	}
}

int link_parse_float(const char **s, float *out)
{
	const char *p;
	float v = 0.0f, scale = 1.0f;
	int sign = 1, digits = 0, ex = 0, exsign = 1;

	skip_spaces(s);
	p = *s;
	if (*p == '-' || *p == '+') {
		sign = (*p == '-') ? -1 : 1;
		p++;
	}
	while (digit(*p)) {
		v = v * 10.0f + (float)(*p++ - '0');
		digits++;
	}
	if (*p == '.') {
		p++;
		while (digit(*p)) {
			scale *= 0.1f;
			v += scale * (float)(*p++ - '0');
			digits++;
		}
	}
	if (!digits) {
		return -1;
	}
	if (*p == 'e' || *p == 'E') {
		p++;
		if (*p == '-' || *p == '+') {
			exsign = (*p == '-') ? -1 : 1;
			p++;
		}
		if (!digit(*p)) {
			return -1;
		}
		while (digit(*p)) {
			ex = ex * 10 + (*p++ - '0');
			if (ex > 30) {
				return -1;
			}
		}
		while (ex--) {
			v = exsign > 0 ? v * 10.0f : v * 0.1f;
		}
	}
	if (*p != 0 && *p != ' ' && *p != '\t' && *p != ',') {
		return -1;
	}
	*out = (float)sign * v;
	*s = p;
	return 0;
}

int link_parse_i32(const char **s, int32_t *out)
{
	const char *p;
	int32_t v = 0;
	int sign = 1, digits = 0;

	skip_spaces(s);
	p = *s;
	if (*p == '-' || *p == '+') {
		sign = (*p == '-') ? -1 : 1;
		p++;
	}
	while (digit(*p)) {
		if (v > 214748363) {
			return -1;
		}
		v = v * 10 + (*p++ - '0');
		digits++;
	}
	if (!digits || (*p != 0 && *p != ' ' && *p != '\t' && *p != ',')) {
		return -1;
	}
	*out = sign * v;
	*s = p;
	return 0;
}

int link_parse_hex32(const char **s, uint32_t *out)
{
	const char *p;
	uint32_t v = 0;
	int digits = 0;

	skip_spaces(s);
	p = *s;
	if (p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) {
		p += 2;
	}
	for (;;) {
		char ch = *p;
		uint32_t d;

		if (digit(ch)) {
			d = (uint32_t)(ch - '0');
		} else if (ch >= 'a' && ch <= 'f') {
			d = (uint32_t)(ch - 'a' + 10);
		} else if (ch >= 'A' && ch <= 'F') {
			d = (uint32_t)(ch - 'A' + 10);
		} else {
			break;
		}
		if (++digits > 8) {
			return -1;
		}
		v = (v << 4) | d;
		p++;
	}
	if (!digits || (*p != 0 && *p != ' ' && *p != '\t' && *p != ',')) {
		return -1;
	}
	*out = v;
	*s = p;
	return 0;
}

static int at_end(const char *s)
{
	skip_spaces(&s);
	return *s == 0;
}

/* ---------- output helpers ---------- */

typedef struct {
	char buf[LINK_LINE_MAX + 32];
	size_t n;
} line_t;

static void put_s(line_t *l, const char *s)
{
	while (*s && l->n < sizeof(l->buf) - 2) {
		l->buf[l->n++] = *s++;
	}
	l->buf[l->n] = 0;
}

static void put_c(line_t *l, char c)
{
	if (l->n < sizeof(l->buf) - 2) {
		l->buf[l->n++] = c;
		l->buf[l->n] = 0;
	}
}

static void put_i(line_t *l, int32_t v)
{
	char tmp[12];

	link_fmt_i32(tmp, v);
	put_s(l, tmp);
}

static void put_x(line_t *l, uint32_t v)
{
	char tmp[9];

	link_fmt_hex32(tmp, v);
	put_s(l, tmp);
}

static void put_f(line_t *l, float v)
{
	char tmp[24];

	link_fmt_float(tmp, v);
	put_s(l, tmp);
}

static uint32_t f2u(float f)
{
	uint32_t u;

	memcpy(&u, &f, sizeof(u));
	return u;
}

static float u2f(uint32_t u)
{
	float f;

	memcpy(&f, &u, sizeof(f));
	return f;
}

static void send(link_ctx_t *lk, line_t *l)
{
	put_c(l, '\n');
	lk->hooks->write(lk, l->buf);
}

static void reply(link_ctx_t *lk, const char *cmd, int code)
{
	line_t l = {.n = 0};

	l.buf[0] = 0;
	if (code == 0) {
		put_s(&l, "OK ");
		put_s(&l, cmd);
	} else {
		put_s(&l, "ERR ");
		put_s(&l, cmd);
		put_c(&l, ' ');
		put_i(&l, code);
	}
	send(lk, &l);
}

static int32_t mdeg(float rad)
{
	float v = rad * (180000.0f / ACORE_PI);

	if (v > 2.0e9f) {
		v = 2.0e9f;
	}
	if (v < -2.0e9f) {
		v = -2.0e9f;
	}
	return (int32_t)(v < 0.0f ? v - 0.5f : v + 0.5f);
}

size_t link_format_telemetry(char *buf, size_t n, const acore_t *c, uint32_t t_ms, int32_t steps,
			     uint16_t raw, uint32_t loop_us, uint8_t pil)
{
	line_t l = {.n = 0};
	const int32_t fields[] = {
		(int32_t)c->mode, (int32_t)c->fault, mdeg(c->target), mdeg(c->theta),
		mdeg(c->v_out), mdeg(c->w_meas), steps, (int32_t)raw, mdeg(c->el_cmd) / 10,
		(int32_t)c->out.servo_us, (int32_t)c->out.half_period_us, (int32_t)loop_us,
		(int32_t)c->settled, (int32_t)pil,
	};

	l.buf[0] = 0;
	put_s(&l, "T,");
	put_i(&l, (int32_t)t_ms);
	for (size_t i = 0; i < sizeof(fields) / sizeof(fields[0]); i++) {
		put_c(&l, ',');
		put_i(&l, fields[i]);
	}
	put_c(&l, '\n');
	if (l.n + 1 > n) {
		return 0;
	}
	memcpy(buf, l.buf, l.n + 1);
	return l.n;
}

/* ---------- parameters ---------- */

static void param_line(link_ctx_t *lk, const char *name, const param_ref_t *r)
{
	line_t l = {.n = 0};
	uint32_t bits;

	l.buf[0] = 0;
	put_s(&l, "P,");
	put_s(&l, name);
	put_c(&l, ',');
	if (r->type == PT_F32) {
		float v;

		memcpy(&v, r->ptr, sizeof(v));
		put_f(&l, v / r->scale);
		bits = f2u(v);
	} else if (r->type == PT_I8) {
		int8_t v = *(int8_t *)r->ptr;

		put_i(&l, v);
		bits = (uint32_t)(int32_t)v;
	} else {
		uint8_t v = *(uint8_t *)r->ptr;

		put_i(&l, v);
		bits = v;
	}
	put_c(&l, ',');
	put_x(&l, bits);
	send(lk, &l);
}

static void list_params(link_ctx_t *lk)
{
	param_ref_t r;
	char name[10];

	for (size_t i = 0; i < NPARAMS; i++) {
		resolve(lk->par, params[i].name, &r);
		param_line(lk, params[i].name, &r);
	}
	for (int i = 0; i < ACORE_NMF; i++) {
		for (int j = 0; j < ACORE_NMF; j++) {
			name[0] = 'r';
			name[1] = (char)('0' + i);
			name[2] = (char)('0' + j);
			name[3] = 0;
			resolve(lk->par, name, &r);
			param_line(lk, name, &r);
		}
	}
	for (int k = 0; k < ACORE_SEQ_MAX; k++) {
		for (int e = 0; e < 2; e++) {
			strcpy(name, e ? "seq_el0" : "seq_az0");
			name[6] = (char)('0' + k);
			resolve(lk->par, name, &r);
			param_line(lk, name, &r);
		}
	}
}

static int is_moving(const link_ctx_t *lk)
{
	return lk->core->v_cmd != 0.0f || lk->core->v_out != 0.0f ||
	       lk->core->out.half_period_us != 0u;
}

static int set_param(link_ctx_t *lk, const char *args, int exact)
{
	char name[16];
	size_t n = 0;
	param_ref_t r;
	acore_params_t backup = *lk->par;
	const char *s = args;

	skip_spaces(&s);
	while (*s && *s != ' ' && *s != '\t' && n < sizeof(name) - 1) {
		name[n++] = *s++;
	}
	name[n] = 0;
	if (resolve(lk->par, name, &r) != 0) {
		return -2;
	}
	if (r.flags & PF_RO) {
		return -3;
	}
	if (exact) {
		uint32_t bits;

		if (link_parse_hex32(&s, &bits) != 0 || !at_end(s)) {
			return -4;
		}
		if (r.type == PT_F32) {
			float v = u2f(bits);

			memcpy(r.ptr, &v, sizeof(v));
		} else if (r.type == PT_I8) {
			*(int8_t *)r.ptr = (int8_t)bits;
		} else {
			*(uint8_t *)r.ptr = (uint8_t)bits;
		}
	} else {
		float v;

		if (link_parse_float(&s, &v) != 0 || !at_end(s)) {
			return -4;
		}
		if (r.type == PT_F32) {
			float iv = v * r.scale;

			memcpy(r.ptr, &iv, sizeof(iv));
		} else if (r.type == PT_I8) {
			if (v < -128.0f || v > 127.0f) {
				return -5;
			}
			*(int8_t *)r.ptr = (int8_t)(v < 0.0f ? v - 0.5f : v + 0.5f);
		} else {
			if (v < 0.0f || v > 255.0f) {
				return -5;
			}
			*(uint8_t *)r.ptr = (uint8_t)(v + 0.5f);
		}
	}
	if (acore_params_check(lk->par) != 0) {
		*lk->par = backup;
		return -6;
	}
	if (lk->hooks->params_changed) {
		lk->hooks->params_changed(lk);
	}
	param_line(lk, name, &r);
	return 0;
}

/* ---------- PIL ---------- */

static void pil_step(link_ctx_t *lk, const char *args)
{
	int32_t k, raw, steps, flags;
	acore_in_t in;
	acore_out_t out;
	uint32_t c0 = 0, c1 = 0;
	line_t l = {.n = 0};
	const acore_t *c = lk->core;

	if (!lk->pil) {
		reply(lk, "X", -1);
		return;
	}
	if (link_parse_i32(&args, &k) || link_parse_i32(&args, &raw) ||
	    link_parse_i32(&args, &steps) || link_parse_i32(&args, &flags) || !at_end(args) ||
	    raw < 0 || raw > 16383) {
		reply(lk, "X", -4);
		return;
	}
	memset(&in, 0, sizeof(in));
	in.raw = (uint16_t)raw;
	in.steps = steps;
	in.sensor_ok = (flags & 1) ? 1u : 0u;
	in.heartbeat = (flags & 2) ? 1u : 0u;
	in.overrun = (flags & 4) ? 1u : 0u;
	if (lk->hooks->cycles_now) {
		c0 = lk->hooks->cycles_now(lk);
	}
	acore_step(lk->core, lk->par, &in, &out);
	if (lk->hooks->cycles_now) {
		c1 = lk->hooks->cycles_now(lk);
	}
	lk->pil_cycles = c1 - c0;

	l.buf[0] = 0;
	put_s(&l, "Y,");
	put_i(&l, k);
	put_c(&l, ',');
	put_i(&l, c->mode);
	put_c(&l, ',');
	put_i(&l, c->fault);
	put_c(&l, ',');
	put_x(&l, f2u(c->theta));
	put_c(&l, ',');
	put_x(&l, f2u(c->v_cmd));
	put_c(&l, ',');
	put_x(&l, f2u(c->u_fz));
	put_c(&l, ',');
	put_x(&l, f2u(c->w_meas));
	put_c(&l, ',');
	put_x(&l, f2u(c->v_out));
	put_c(&l, ',');
	put_i(&l, (int32_t)out.half_period_us);
	put_c(&l, ',');
	put_i(&l, out.dir);
	put_c(&l, ',');
	put_i(&l, out.servo_us);
	put_c(&l, ',');
	put_i(&l, out.settled);
	put_c(&l, ',');
	put_i(&l, (int32_t)lk->pil_cycles);
	send(lk, &l);
}

/* ---------- dispatcher ---------- */

void link_init(link_ctx_t *lk, acore_t *core, acore_params_t *par, const link_hooks_t *hooks,
	       void *user)
{
	memset(lk, 0, sizeof(*lk));
	lk->core = core;
	lk->par = par;
	lk->hooks = hooks;
	lk->user = user;
}

void link_handle_line(link_ctx_t *lk, char *line)
{
	const char *s = line;
	char cmd[3] = {0, 0, 0};
	float a, b;
	int32_t iv;
	int rc;

	skip_spaces(&s);
	if (*s == 0) {
		return;
	}
	cmd[0] = *s++;
	if ((cmd[0] == 'P' || cmd[0] == 'G') && *s == 'X') {
		cmd[1] = *s++;
	}
	if (*s != 0 && *s != ' ' && *s != '\t') {
		reply(lk, "?", -1);
		return;
	}

	switch (cmd[0]) {
	case 'H':
		lk->heartbeat = 1;
		return;
	case 'G':
		if (cmd[1] == 'X') {
			/* GX <mask> <az_bits> <el_bits>: exact IEEE-754 targets in rad (PIL) */
			uint32_t ua, ub;

			if (link_parse_i32(&s, &iv) || link_parse_hex32(&s, &ua) ||
			    link_parse_hex32(&s, &ub) || !at_end(s) || iv < 1 || iv > 3) {
				reply(lk, cmd, -4);
				return;
			}
			rc = acore_cmd_goto(lk->core, lk->par, (uint8_t)iv, u2f(ua), u2f(ub), 1);
			reply(lk, cmd, rc);
			return;
		}
		if (link_parse_float(&s, &a) || link_parse_float(&s, &b) || !at_end(s)) {
			reply(lk, cmd, -4);
			return;
		}
		rc = acore_cmd_goto(lk->core, lk->par, ACORE_GOTO_AZ | ACORE_GOTO_EL, a * DEG2RAD,
				    b * DEG2RAD, 1);
		reply(lk, cmd, rc);
		return;
	case 'A':
	case 'E':
		if (link_parse_float(&s, &a) || !at_end(s)) {
			reply(lk, cmd, -4);
			return;
		}
		rc = acore_cmd_goto(lk->core, lk->par, cmd[0] == 'A' ? ACORE_GOTO_AZ : ACORE_GOTO_EL,
				    a * DEG2RAD, a * DEG2RAD, 1);
		reply(lk, cmd, rc);
		return;
	case 'S':
		acore_cmd_stop(lk->core, lk->par);
		reply(lk, cmd, 0);
		return;
	case 'F':
		acore_cmd_estop(lk->core);
		reply(lk, cmd, 0);
		return;
	case 'C':
		reply(lk, cmd, acore_cmd_clear(lk->core, lk->par));
		return;
	case 'Q':
		iv = 0;
		if (!at_end(s) && (link_parse_i32(&s, &iv) || !at_end(s))) {
			reply(lk, cmd, -4);
			return;
		}
		reply(lk, cmd, acore_cmd_sequence(lk->core, lk->par, iv != 0));
		return;
	case 'Z': {
		uint16_t raw;

		a = 0.0f;
		if (!at_end(s) && (link_parse_float(&s, &a) || !at_end(s))) {
			reply(lk, cmd, -4);
			return;
		}
		if (lk->pil || !lk->hooks->read_raw || lk->hooks->read_raw(lk, &raw) != 0) {
			reply(lk, cmd, -7);
			return;
		}
		rc = acore_set_zero(lk->core, lk->par, raw, a * DEG2RAD);
		if (rc == 0 && lk->hooks->save_params) {
			rc = lk->hooks->save_params(lk) ? -8 : 0;
		}
		reply(lk, cmd, rc);
		return;
	}
	case 'T':
		if (link_parse_i32(&s, &iv) || !at_end(s) || iv < 0 || (iv > 0 && iv < 10)) {
			reply(lk, cmd, -4);
			return;
		}
		lk->telemetry_ms = (uint32_t)iv;
		reply(lk, cmd, 0);
		return;
	case '?': {
		char buf[LINK_LINE_MAX + 32];

		if (lk->hooks->telemetry) {
			lk->hooks->telemetry(lk);
		} else if (link_format_telemetry(buf, sizeof(buf), lk->core, 0u, 0, 0, 0, lk->pil)) {
			lk->hooks->write(lk, buf);
		}
		return;
	}
	case 'P':
		if (cmd[1] == 0 && at_end(s)) {
			list_params(lk);
			reply(lk, cmd, 0);
			return;
		}
		reply(lk, cmd, set_param(lk, s, cmd[1] == 'X'));
		return;
	case 'W':
		if (is_moving(lk) || lk->pil) {
			reply(lk, cmd, -9);
			return;
		}
		reply(lk, cmd, lk->hooks->save_params ? (lk->hooks->save_params(lk) ? -8 : 0) : -7);
		return;
	case 'D':
		if (is_moving(lk)) {
			reply(lk, cmd, -9);
			return;
		}
		acore_params_default(lk->par);
		if (lk->hooks->params_changed) {
			lk->hooks->params_changed(lk);
		}
		acore_init(lk->core, lk->par);
		reply(lk, cmd, 0);
		return;
	case 'L':
		if (is_moving(lk)) {
			reply(lk, cmd, -9);
			return;
		}
		rc = lk->hooks->load_params ? lk->hooks->load_params(lk) : -7;
		if (lk->hooks->params_changed) {
			lk->hooks->params_changed(lk);
		}
		acore_init(lk->core, lk->par);
		reply(lk, cmd, rc);
		return;
	case 'M':
		if (link_parse_i32(&s, &iv) || !at_end(s) || iv < 0 || iv > 1) {
			reply(lk, cmd, -4);
			return;
		}
		if (iv == 1 && is_moving(lk) && !lk->pil) {
			reply(lk, cmd, -9);
			return;
		}
		lk->pil = (uint8_t)iv;
		if (lk->hooks->set_pil) {
			lk->hooks->set_pil(lk, iv);
		}
		if (!iv && lk->hooks->load_params) {
			(void)lk->hooks->load_params(lk);
			if (lk->hooks->params_changed) {
				lk->hooks->params_changed(lk);
			}
		}
		acore_init(lk->core, lk->par);
		reply(lk, cmd, 0);
		return;
	case 'X':
		pil_step(lk, s);
		return;
	case 'V': {
		line_t l = {.n = 0};

		l.buf[0] = 0;
		put_s(&l, "V,antenna_v5," LINK_FW_VERSION ",core=");
		put_x(&l, ACORE_VERSION);
		put_s(&l, ",params=");
		put_i(&l, (int32_t)sizeof(acore_params_t));
		send(lk, &l);
		return;
	}
	default:
		reply(lk, cmd, -1);
		return;
	}
}
