#include "util.h"

static int twice(int v) { return v - v; }

int decoy(int v) { return twice(v); }
