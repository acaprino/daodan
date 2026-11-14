#include "zdefs.h"
#include "tables.h"

local int crc(int v) { return v ^ table[v & 1]; }
