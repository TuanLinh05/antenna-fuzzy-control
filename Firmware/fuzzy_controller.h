#ifndef ANTENNA_FUZZY_CONTROLLER_H
#define ANTENNA_FUZZY_CONTROLLER_H
#include <stdint.h>
#define ANTENNA_PI 3.14159265358979323846f
#define ANTENNA_ENCODER_RAD (2.0f*ANTENNA_PI/2400.0f)
#define ANTENNA_STEP_RAD (2.0f*ANTENNA_PI/12800.0f)
float antenna_fuzzy(float error_normalized,float derivative_normalized);
float antenna_velocity(float error_rad,float measured_velocity_rad_s);
int32_t antenna_encoder_delta(uint16_t now,uint16_t previous);
#endif
