#include <ringbuf/ringbuf.hpp>

int main() {
    ringbuf::ring<int, 2> r;
    if (!r.push(1) || !r.push(2) || r.push(3)) return 1;
    return r.pop() == 1 && r.size() == 1 ? 0 : 1;
}
