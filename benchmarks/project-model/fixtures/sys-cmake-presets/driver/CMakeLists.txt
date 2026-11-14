add_library(sensor_driver STATIC driver.c)
target_include_directories(sensor_driver PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(sensor_driver PUBLIC SENSOR_BOARD_NAME="${SENSOR_BOARD}")
