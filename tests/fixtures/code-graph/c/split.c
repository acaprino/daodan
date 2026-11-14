#include "util.h"

int split(int v) {
    int n = add(v, 1);
    if (n > 2)
#ifdef SPLIT_FAST
        return mul(n, 2);
#else
        return add(n, 2);
#endif
    return n;
}
