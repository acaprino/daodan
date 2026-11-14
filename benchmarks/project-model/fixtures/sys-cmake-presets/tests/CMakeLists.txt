add_executable(sensor_tests test_driver.c)
target_link_libraries(sensor_tests PRIVATE sensor_driver)
add_test(NAME driver COMMAND sensor_tests)
