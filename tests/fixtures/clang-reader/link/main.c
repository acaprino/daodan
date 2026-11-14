#include <stdio.h>
#include "api.h"

int main(void) {
    int n = add(1, 2);
    n += deep(n);
    n += helper();
    n += quiet(n);
    n += hidden(n);
    printf("%d\n", n);
    return 0;
}
