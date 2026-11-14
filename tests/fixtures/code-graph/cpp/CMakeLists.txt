cmake_minimum_required(VERSION 3.13)
project(cppfixture CXX)
set(CMAKE_CXX_STANDARD 17)
add_library(app STATIC main.cpp shapes.cpp)
