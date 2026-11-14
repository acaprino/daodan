add_library(calc_core STATIC
  src/expr.cpp
  src/archive.cpp
)
target_include_directories(calc_core
  PUBLIC include
  PRIVATE src
)
target_compile_definitions(calc_core PUBLIC CALC_WITH_ZLIB=1)
target_link_libraries(calc_core PUBLIC ZLIB::ZLIB)
