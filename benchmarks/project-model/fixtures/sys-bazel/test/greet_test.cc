#include "gtest/gtest.h"
#include "lib/greet.h"

TEST(Greet, Loud) { EXPECT_EQ(greeter::greet("x"), "HELLO, x!"); }
