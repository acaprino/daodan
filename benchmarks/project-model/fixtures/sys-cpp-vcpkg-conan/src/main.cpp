#include <fmt/core.h>
#include <zlib.h>

int main() {
    fmt::print("imgtool with zlib {}\n", zlibVersion());
    return 0;
}
