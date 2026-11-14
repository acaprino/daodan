#include "zdefs.h"

#define ROUND(a) \
    do { /* keep it small */ \
        (a) %= zlimit; \
    } while (0)

#   /* a null directive */

local int fold(int v) { return v + 1; }

int checksum(const unsigned char far_ptr *buf, int len) {
    word count = 0;
    int sum = 0;
    for (; (int)count < len; count++) sum = fold(sum + buf[count]);
    ROUND(sum);
    return sum;
}
