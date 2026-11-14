#include "archive.h"
#include "calc/expr.hpp"

#include <zlib.h>

namespace calc {

namespace detail {
std::size_t pack_bound(std::size_t n) { return compressBound(static_cast<uLong>(n)); }
}  // namespace detail

std::string pack(const std::string& text) {
#if CALC_WITH_ZLIB
    std::string out(detail::pack_bound(text.size()), '\0');
    uLongf len = static_cast<uLongf>(out.size());
    if (compress(reinterpret_cast<Bytef*>(out.data()), &len,
                 reinterpret_cast<const Bytef*>(text.data()), static_cast<uLong>(text.size())) != Z_OK)
        return {};
    out.resize(len);
    return out;
#else
    return text;
#endif
}

}  // namespace calc
