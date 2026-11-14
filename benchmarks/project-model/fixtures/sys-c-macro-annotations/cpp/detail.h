// detail.h -- C++ only, despite the .h extension
#pragma once

#include <string_view>

namespace zminipp::detail {

template <typename Byte>
inline const Byte* data_of(std::basic_string_view<Byte> s) noexcept {
    return s.data();
}

}  // namespace zminipp::detail
