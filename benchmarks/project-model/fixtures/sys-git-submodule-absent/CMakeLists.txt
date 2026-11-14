cmake_minimum_required(VERSION 3.16)
project(logfmt VERSION 0.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

# fmt is a git submodule: run "git submodule update --init" first.
add_subdirectory(third_party/fmt EXCLUDE_FROM_ALL)

add_executable(logfmt src/main.cpp)
target_link_libraries(logfmt PRIVATE fmt::fmt)
