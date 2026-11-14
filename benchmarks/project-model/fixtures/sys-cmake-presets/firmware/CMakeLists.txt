add_executable(sensor_fw main.c)
target_link_libraries(sensor_fw PRIVATE sensor_driver)
set_target_properties(sensor_fw PROPERTIES SUFFIX ".elf")
