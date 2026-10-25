/*
 * STEP/DIR pulse generator state machine for the TB6600 - portable C99.
 *
 * The firmware calls stepgen_tick() from a hardware timer interrupt; the
 * return value is the time to the next interrupt. MATLAB calls the same logic
 * (through the MEX or its M-code mirror) to place the STEP edges exactly in
 * the plant simulation.
 *
 * Waveform: 50 % duty, one rising edge = one microstep. A direction change is
 * only made while STEP is low and is followed by an extra low interval of at
 * least dir_guard_us, so DIR is stable >= one half period around every edge
 * whichever edge the opto-isolated driver uses (TB6600 asks for >= 5 us).
 *
 * A new rate normally takes effect at the next edge. When the rate rises
 * while a long interval is running (start-up from a very low rate), the
 * caller asks stepgen_retime() to shorten the interval in progress; without
 * this the motor would stay idle for up to 65 ms and then jump, which the
 * simulation showed to excite the ~11 Hz antenna/belt mode.
 */
#ifndef ANTENNA_STEPGEN_H
#define ANTENNA_STEPGEN_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define STEPGEN_START_US        20u
#define STEPGEN_RETIME_MARGIN_US 20u
#define STEPGEN_DIR_SIGN_BIT    0x80000000u

typedef struct {
	volatile uint32_t pending;  /* half period [us] | STEPGEN_DIR_SIGN_BIT for negative */
	volatile int32_t steps;     /* rising edges, signed by logical direction */
	uint32_t hp;                /* half period in use [us] */
	uint32_t interval;          /* length of the timer interval in progress [us] */
	uint32_t dir_guard_us;
	int8_t dir;                 /* logical direction currently on the DIR pin */
	uint8_t level;              /* STEP pin level */
	volatile uint8_t running;   /* timer armed */
	uint8_t retimable;          /* interval in progress is a plain half period */
} stepgen_t;

typedef struct {
	uint8_t step_level;
	int8_t dir;
	uint8_t dir_changed;
	uint8_t stepped;
} stepgen_pins_t;

void stepgen_init(stepgen_t *sg, uint32_t dir_guard_us);
/* Thread context. Returns the first timer interval [us] if the caller must
 * start the timer (generator was idle), otherwise 0. */
uint32_t stepgen_command(stepgen_t *sg, uint32_t half_period_us, int8_t dir);
/* Thread context, generator running, elapsed_us = time since the last tick.
 * Returns the shortened interval to load into the timer, or 0 to keep it. */
uint32_t stepgen_retime(stepgen_t *sg, uint32_t elapsed_us);
/* Timer context. Updates the pins and returns the next interval [us];
 * 0 means stop the timer (STEP stays low). */
uint32_t stepgen_tick(stepgen_t *sg, stepgen_pins_t *pins);

#ifdef __cplusplus
}
#endif
#endif /* ANTENNA_STEPGEN_H */
