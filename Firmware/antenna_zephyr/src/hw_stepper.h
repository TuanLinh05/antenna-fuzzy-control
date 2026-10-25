/* TB6600 STEP/DIR/ENA outputs driven by the portable stepgen state machine. */
#ifndef HW_STEPPER_H
#define HW_STEPPER_H

#include <stdbool.h>
#include <stdint.h>

int hw_stepper_init(void);
/* New command from the control loop (half period in us, 0 = stop). */
void hw_stepper_command(uint32_t half_period_us, int8_t dir);
/* Rising edges emitted so far, signed by logical direction. */
int32_t hw_stepper_steps(void);
void hw_stepper_set_motor_sign(int8_t sign);
/* false: STEP held low and the driver released through ENA (PIL mode). */
void hw_stepper_enable(bool enable);

#endif
