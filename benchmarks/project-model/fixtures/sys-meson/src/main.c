#include <stdio.h>
#include "img.h"

int main(void)
{
    unsigned char px[16] = {0}, out[64];
    printf("packed %zu bytes, gamma %u\n",
           img_pack(px, 4, 4, out, sizeof out), img_gamma(128, 2.2));
    return 0;
}
