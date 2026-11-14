#include <fmt/format.h>

int main() {
    fmt::print("{:>8} | {}\n", "level", "message");
    fmt::print("{:>8} | {}\n", "info", "started");
    return 0;
}
