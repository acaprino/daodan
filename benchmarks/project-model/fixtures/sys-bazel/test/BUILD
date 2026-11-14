load("@rules_cc//cc:defs.bzl", "cc_test")

cc_test(
    name = "greet_test",
    srcs = ["greet_test.cc"],
    deps = [
        "//lib:greet",
        "@googletest//:gtest_main",
    ],
)
