#include "checksum.hpp"
#include "detail.h"

#include <zmini.h>

namespace zminipp {

std::uint32_t adler32(std::string_view bytes) {
    const auto* p = reinterpret_cast<const Bytef*>(detail::data_of(bytes));
    return static_cast<std::uint32_t>(zm_adler(1UL, p, static_cast<unsigned>(bytes.size())));
}

}  // namespace zminipp
