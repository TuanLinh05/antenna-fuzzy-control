/* Parameter persistence in the 4 KB storage partition (Zephyr NVS). */
#ifndef PARAMS_STORE_H
#define PARAMS_STORE_H

#include "antenna_core.h"

int params_store_init(void);
/* 0 = loaded; negative = nothing valid stored (p is not modified). */
int params_store_load(acore_params_t *p);
int params_store_save(const acore_params_t *p);

#endif
