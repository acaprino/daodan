#include <fmt/core.h>

int plain(int value);

int main() {
    fmt::print("{}\n", plain(1));
    return plain(2);
}
