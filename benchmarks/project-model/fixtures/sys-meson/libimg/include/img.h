#ifndef IMG_H
#define IMG_H

#include <stddef.h>

/* Compresses a grayscale image of w*h bytes; returns the packed size or 0. */
size_t img_pack(const unsigned char *pixels, unsigned w, unsigned h,
                unsigned char *out, size_t cap);

/* Gamma-corrects one 8-bit sample. */
unsigned char img_gamma(unsigned char v, double gamma);

#endif
