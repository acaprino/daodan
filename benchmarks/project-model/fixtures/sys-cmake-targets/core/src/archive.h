#pragma once

#include <cstddef>
#include <string>

namespace calc::detail {

// Upper bound of the compressed size of n bytes.
std::size_t pack_bound(std::size_t n);

}  // namespace calc::detail
