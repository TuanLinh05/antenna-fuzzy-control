/* LD-1501MG servo pulse on TIM4_CH1 (PB6), 50 Hz frame. */
#ifndef HW_SERVO_H
#define HW_SERVO_H

#include <stdint.h>

int hw_servo_init(uint16_t pulse_us);
/* Applied by the timer at the start of the next 20 ms frame (preload). */
int hw_servo_set_us(uint16_t pulse_us);

#endif
