#include <stdio.h>
#include "util.h"

static int twice(int v) { return add(v, v); }

int add(int a, int b) { return a + b; }

int mul(int a, int b) { return twice(a) * b / 2; }

void log_message(const char *msg) { printf("%s\n", msg); }

void run_callback(struct handler *h, int value) {
    h->on_event(value);
#ifdef USE_FAST
    fast_path(value);
#else
    log_message("slow");
#endif
}
