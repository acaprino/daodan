add_library(zminipp STATIC checksum.cpp)
target_include_directories(zminipp PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(zminipp PUBLIC zmini)
