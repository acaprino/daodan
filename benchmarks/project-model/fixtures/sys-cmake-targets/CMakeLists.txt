cmake_minimum_required(VERSION 3.20)
project(calc VERSION 1.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ZLIB 1.2.11 REQUIRED)

add_subdirectory(core)
add_subdirectory(app)
