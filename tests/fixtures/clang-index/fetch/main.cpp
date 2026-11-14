#include <fmt/core.h>

int plain(int value);

int main() {
    fmt::print("{}
", plain(1));
    return plain(2);
}
