cmake_minimum_required(VERSION 3.21)
project(ringbuf VERSION 2.0.1 LANGUAGES CXX)

add_library(ringbuf INTERFACE)
add_library(ringbuf::ringbuf ALIAS ringbuf)
target_include_directories(ringbuf INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(ringbuf INTERFACE cxx_std_20)

if(PROJECT_IS_TOP_LEVEL)
  enable_testing()
  add_subdirectory(tests)
endif()
