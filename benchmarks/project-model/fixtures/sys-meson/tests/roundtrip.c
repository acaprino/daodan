#include "img.h"

int main(void)
{
    unsigned char px[4] = {1, 2, 3, 4}, out[64];
    return img_pack(px, 2, 2, out, sizeof out) > 0 ? 0 : 1;
}
