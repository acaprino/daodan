#pragma once

#include <cstdint>
#include <string_view>

namespace zminipp {

// Adler-32 of a byte string, through the C library.
std::uint32_t adler32(std::string_view bytes);

}  // namespace zminipp
