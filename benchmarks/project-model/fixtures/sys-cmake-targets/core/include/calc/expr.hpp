#pragma once

#include <string>

namespace calc {

// Evaluates "a+b" or "a*b" with integer operands.
long evaluate(const std::string& expr);

// Compresses text with zlib; empty on failure.
std::string pack(const std::string& text);

}  // namespace calc
