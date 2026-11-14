#include <iostream>

#include "lib/greet.h"

int main() {
    std::cout << greeter::greet("bazel") << "\n";
    return 0;
}
