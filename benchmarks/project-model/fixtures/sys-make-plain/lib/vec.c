#include <math.h>
#include "mini.h"

double mini_vec_len(mini_vec v)
{
    return sqrt(v.x * v.x + v.y * v.y);
}
