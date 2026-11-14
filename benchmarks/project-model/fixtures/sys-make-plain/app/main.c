#include <stdio.h>
#include <string.h>
#include "mini.h"

int main(int argc, char **argv)
{
    mini_vec v = {3.0, 4.0};
    if (argc > 1 && strcmp(argv[1], "--self-test") == 0)
        return mini_vec_len(v) == 5.0 ? 0 : 1;
    mini_log(1, "starting");
    printf("%g\n", mini_vec_len(v));
    return 0;
}
