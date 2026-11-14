cmake_minimum_required(VERSION 3.21)
project(sensor VERSION 0.9.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(SENSOR_BOARD "host" CACHE STRING "Board the firmware runs on")
option(SENSOR_BUILD_TESTS "Build the host unit tests" ON)

add_subdirectory(driver)

if(CMAKE_CROSSCOMPILING)
  add_subdirectory(firmware)
endif()

if(SENSOR_BUILD_TESTS AND NOT CMAKE_CROSSCOMPILING)
  enable_testing()
  add_subdirectory(tests)
endif()
