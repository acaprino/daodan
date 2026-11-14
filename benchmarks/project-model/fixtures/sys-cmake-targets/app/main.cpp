#include "calc/expr.hpp"

#include <iostream>

int main(int argc, char** argv) {
    const std::string expr = argc > 1 ? argv[1] : "6*7";
    std::cout << expr << " = " << calc::evaluate(expr) << "\n";
    std::cout << "packed " << calc::pack(expr).size() << " bytes\n";
    return 0;
}
