#include "api.h"
#include "geo.hpp"

namespace geo {
int twice(int v) { return area(v) * 2; }
}

int plain(int v) { return area(v); }
int boxed(geo::Box b) { return size(b); }
int run(int v) { return square(v); }
