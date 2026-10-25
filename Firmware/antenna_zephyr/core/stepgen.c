/* STEP/DIR generator state machine. See stepgen.h. */
#include "stepgen.h"

#include <string.h>

void stepgen_init(stepgen_t *sg, uint32_t dir_guard_us)
{
	memset(sg, 0, sizeof(*sg));
	sg->dir = 1;
	sg->dir_guard_us = dir_guard_us;
}

uint32_t stepgen_command(stepgen_t *sg, uint32_t half_period_us, int8_t dir)
{
	uint32_t word = half_period_us & 0xFFFFu;

	if (word != 0u && dir < 0) {
		word |= STEPGEN_DIR_SIGN_BIT;
	}
	sg->pending = word; /* single 32-bit store: atomic for the timer ISR */
	if (!sg->running && word != 0u) {
		sg->running = 1;
		sg->level = 0;
		sg->interval = STEPGEN_START_US;
		sg->retimable = 0;
		return STEPGEN_START_US;
	}
	return 0u;
}

uint32_t stepgen_retime(stepgen_t *sg, uint32_t elapsed_us)
{
	uint32_t hp = sg->pending & 0xFFFFu;
	uint32_t iv;

	if (!sg->running || !sg->retimable || hp == 0u || hp >= sg->interval) {
		return 0u;
	}
	iv = hp;
	if (iv < elapsed_us + STEPGEN_RETIME_MARGIN_US) {
		iv = elapsed_us + STEPGEN_RETIME_MARGIN_US;
	}
	if (iv >= sg->interval) {
		return 0u;
	}
	sg->interval = iv;
	return iv;
}

uint32_t stepgen_tick(stepgen_t *sg, stepgen_pins_t *pins)
{
	uint32_t word = sg->pending;
	uint32_t hp = word & 0xFFFFu;
	int8_t dir = (word & STEPGEN_DIR_SIGN_BIT) ? -1 : 1;

	pins->dir_changed = 0;
	pins->stepped = 0;
	pins->dir = sg->dir;
	pins->step_level = 0;
	if (sg->level) {
		/* falling edge, then the low half of the current period (or of a
		 * faster pending one) */
		sg->level = 0;
		if (hp != 0u && hp < sg->hp) {
			sg->hp = hp;
		}
		sg->interval = sg->hp;
		sg->retimable = 1;
		return sg->hp;
	}
	if (hp == 0u) {
		sg->running = 0;
		sg->retimable = 0;
		return 0u;
	}
	if (dir != sg->dir) {
		sg->dir = dir;
		pins->dir = dir;
		pins->dir_changed = 1;
		sg->interval = hp > sg->dir_guard_us ? hp : sg->dir_guard_us;
		sg->retimable = 0; /* keep the DIR set-up time */
		return sg->interval;
	}
	sg->level = 1;
	sg->hp = hp;
	sg->steps += dir;
	pins->step_level = 1;
	pins->stepped = 1;
	sg->interval = hp;
	sg->retimable = 1;
	return hp;
}
