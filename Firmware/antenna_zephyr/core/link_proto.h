/*
 * ASCII line protocol between the board and MATLAB / a serial terminal.
 * Portable: used by the Zephyr firmware and by the host "virtual board".
 *
 * One command per line, '\n' terminated, '\r' ignored. Angles in degrees.
 *   H                    heartbeat (no reply)
 *   G <az> <el>          go to azimuth/elevation      A <az> | E <el>
 *   GX <mask> <az> <el>  same with raw IEEE-754 radians in hex (mask 1 az, 2 el, 3 both)
 *   S | F | C            stop (decelerate, hold) | emergency stop (latched) | clear faults
 *   Z [az]               current position becomes az (default 0), saved
 *   Q [1]                run the built-in sequence (1 = loop)
 *   T <ms>               telemetry period, 0 = off     ?  one telemetry line
 *   P                    list parameters               P <name> <value>  set (user units)
 *   PX <name> <hex>      set the raw IEEE-754/integer value (bit exact)
 *   W | D | L            save to flash | defaults | reload saved parameters
 *   M <0|1>              processor-in-the-loop mode off/on (STEP output disabled)
 *   X <k> <raw> <steps> <flags>   PIL: one control step with the given inputs
 *   V                    version
 */
#ifndef ANTENNA_LINK_PROTO_H
#define ANTENNA_LINK_PROTO_H

#include <stddef.h>
#include <stdint.h>

#include "antenna_core.h"

#ifdef __cplusplus
extern "C" {
#endif

#define LINK_LINE_MAX 96
#define LINK_FW_VERSION "1.0.0"

typedef struct link_ctx link_ctx_t;

typedef struct {
	void (*write)(link_ctx_t *lk, const char *text);           /* append text to UART */
	int (*save_params)(link_ctx_t *lk);                        /* 0 = ok */
	int (*load_params)(link_ctx_t *lk);                        /* 0 = ok, restores saved set */
	int (*read_raw)(link_ctx_t *lk, uint16_t *raw);            /* 0 = ok */
	void (*set_pil)(link_ctx_t *lk, int on);                   /* hardware side of 'M' */
	uint32_t (*cycles_now)(link_ctx_t *lk);                    /* cycle counter, may be NULL */
	void (*params_changed)(link_ctx_t *lk);                    /* e.g. motor_sign -> ISR copy */
	void (*telemetry)(link_ctx_t *lk);                         /* '?': one line with live data */
} link_hooks_t;

struct link_ctx {
	acore_t *core;
	acore_params_t *par;
	const link_hooks_t *hooks;
	void *user;
	volatile uint8_t heartbeat;   /* set by 'H', consumed by the control loop */
	volatile uint8_t pil;         /* PIL mode active */
	uint32_t telemetry_ms;
	uint32_t pil_cycles;          /* execution time of the last PIL step */
};

void link_init(link_ctx_t *lk, acore_t *core, acore_params_t *par, const link_hooks_t *hooks,
	       void *user);
/* Parse and execute one line (NUL-terminated, modified in place). */
void link_handle_line(link_ctx_t *lk, char *line);
/* Telemetry: T,ms,mode,fault,ref_mdeg,az_mdeg,vcmd_mdeg_s,wmeas_mdeg_s,steps,raw,
 *            el_cdeg,servo_us,half_period_us,loop_us,settled,pil */
size_t link_format_telemetry(char *buf, size_t n, const acore_t *c, uint32_t t_ms, int32_t steps,
			     uint16_t raw, uint32_t loop_us, uint8_t pil);

/* small formatting / parsing helpers (no stdio, no float printf) */
size_t link_fmt_i32(char *buf, int32_t v);
size_t link_fmt_hex32(char *buf, uint32_t v);
size_t link_fmt_float(char *buf, float v);
int link_parse_float(const char **s, float *out);
int link_parse_i32(const char **s, int32_t *out);
int link_parse_hex32(const char **s, uint32_t *out);

#ifdef __cplusplus
}
#endif
#endif /* ANTENNA_LINK_PROTO_H */
