#include <stdio.h>
#include "driver.h"

int main(void)
{
    if (sensor_millivolts(4095) != 3300u) {
        printf("full scale wrong on %s\n", sensor_board());
        return 1;
    }
    return 0;
}
