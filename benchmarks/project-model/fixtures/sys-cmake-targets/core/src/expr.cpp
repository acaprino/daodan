#include "calc/expr.hpp"

#include <stdexcept>

namespace calc {

long evaluate(const std::string& expr) {
    const auto op = expr.find_first_of("+*");
    if (op == std::string::npos) throw std::invalid_argument(expr);
    const long a = std::stol(expr.substr(0, op));
    const long b = std::stol(expr.substr(op + 1));
    return expr[op] == '+' ? a + b : a * b;
}

}  // namespace calc
