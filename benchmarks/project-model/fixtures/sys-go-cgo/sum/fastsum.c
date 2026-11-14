#include <math.h>
#include "fastsum.h"

#ifndef FASTSUM_UNROLL
#define FASTSUM_UNROLL 1
#endif

double fastsum(const double *xs, size_t n)
{
    double t = 0.0;
    size_t i = 0;
#if FASTSUM_UNROLL >= 4
    for (; i + 4 <= n; i += 4)
        t += xs[i] + xs[i + 1] + xs[i + 2] + xs[i + 3];
#endif
    for (; i < n; i++)
        t += xs[i];
    return isfinite(t) ? t : 0.0;
}
