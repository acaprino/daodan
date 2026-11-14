#include "driver.h"

uint32_t sensor_millivolts(uint16_t raw)
{
    return ((uint32_t)(raw & 0x0FFFu) * 3300u) / 4095u;
}

const char *sensor_board(void)
{
    return SENSOR_BOARD_NAME;
}
