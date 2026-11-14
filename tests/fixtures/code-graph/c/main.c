#include <string.h>
#include "util.h"

static void on_event_impl(int value) { LOG("event"); }

int main(void) {
    struct handler h = { on_event_impl, add };
    void (*fp)(int) = on_event_impl;
    int n = /* é */ add(1, 2);
    n += SQUARE(n);
    n += h.compute(n, 1);
    (*fp)(n);
    run_callback(&h, n);
    n += (int)strlen("abc");
    n += SQUARE(add(n, 1));
    return platform_init() + n;
}
