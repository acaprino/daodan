#include "driver.h"

volatile uint32_t last_mv;

int main(void)
{
    for (;;) {
        last_mv = sensor_millivolts(2048);
    }
}
