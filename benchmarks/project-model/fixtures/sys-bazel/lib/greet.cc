#include "lib/greet.h"

namespace greeter {

std::string greet(const std::string& name) {
#if GREET_LOUD
    return "HELLO, " + name + "!";
#else
    return "hello, " + name;
#endif
}

}  // namespace greeter
