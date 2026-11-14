cmake_minimum_required(VERSION 3.24)
project(imgtool VERSION 0.4.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Dependencies come from vcpkg (CMAKE_TOOLCHAIN_FILE=.../vcpkg.cmake) or from
# Conan (CMakeDeps + CMakeToolchain): both provide the same CMake packages.
find_package(fmt CONFIG REQUIRED)
find_package(ZLIB REQUIRED)

add_subdirectory(src)
