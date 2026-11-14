#ifndef SENSOR_DRIVER_H
#define SENSOR_DRIVER_H

#include <stdint.h>

/* Converts a raw 12-bit ADC sample to millivolts (3.3 V reference). */
uint32_t sensor_millivolts(uint16_t raw);

/* Name of the board the driver was built for. */
const char *sensor_board(void);

#endif
