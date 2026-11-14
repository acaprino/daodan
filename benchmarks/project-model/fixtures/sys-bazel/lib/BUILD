load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "greet",
    srcs = ["greet.cc"],
    hdrs = ["greet.h"],
    local_defines = ["GREET_LOUD=1"],
    visibility = ["//visibility:public"],
)
