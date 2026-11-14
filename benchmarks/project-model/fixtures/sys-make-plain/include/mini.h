#ifndef MINI_H
#define MINI_H

#include <stddef.h>

typedef struct {
    double x, y;
} mini_vec;

double mini_vec_len(mini_vec v);
void mini_log(int level, const char *msg);

#endif
