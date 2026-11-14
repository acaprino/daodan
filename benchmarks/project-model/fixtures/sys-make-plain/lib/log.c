#include <stdio.h>
#include "mini.h"

#ifndef MINI_LOG_LEVEL
#define MINI_LOG_LEVEL 0
#endif

void mini_log(int level, const char *msg)
{
    if (level <= MINI_LOG_LEVEL)
        fprintf(stderr, "[%d] %s\n", level, msg);
}
