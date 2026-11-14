add_executable(ringbuf_tests test_ring.cpp)
target_link_libraries(ringbuf_tests PRIVATE ringbuf::ringbuf)
add_test(NAME ring COMMAND ringbuf_tests)
