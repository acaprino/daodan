#pragma once

#include <array>
#include <concepts>
#include <optional>

#include "ringbuf/config.h"

namespace ringbuf {

template <std::semiregular T, std::size_t N = default_capacity>
class ring {
public:
    bool push(const T& v) {
        if (size_ == N) return false;
        data_[(head_ + size_++) % N] = v;
        return true;
    }

    std::optional<T> pop() {
        if (size_ == 0) return std::nullopt;
        T v = data_[head_];
        head_ = (head_ + 1) % N;
        --size_;
        return v;
    }

    [[nodiscard]] std::size_t size() const noexcept { return size_; }

private:
    std::array<T, N> data_{};
    std::size_t head_ = 0;
    std::size_t size_ = 0;
};

}  // namespace ringbuf
