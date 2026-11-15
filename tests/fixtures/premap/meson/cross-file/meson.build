project('sensor', 'c')
driver = static_library('driver', 'driver.c')
if meson.is_cross_build()
  executable('firmware', 'firmware.c', link_with: driver)
else
  executable('host_tests', 'tests.c', link_with: driver)
endif
