#include <math.h>
#include <zlib.h>
#include "img.h"

size_t img_pack(const unsigned char *pixels, unsigned w, unsigned h,
                unsigned char *out, size_t cap)
{
    uLongf len = (uLongf)cap;
    if (w > IMG_MAX_SIDE || h > IMG_MAX_SIDE)
        return 0;
    if (compress(out, &len, pixels, (uLong)w * h) != Z_OK)
        return 0;
    return (size_t)len;
}

unsigned char img_gamma(unsigned char v, double gamma)
{
    return (unsigned char)(255.0 * pow(v / 255.0, 1.0 / gamma) + 0.5);
}
