project('imgconv', 'c',
  version : '0.3.0',
  license : 'MIT',
  meson_version : '>=1.1.0',
  default_options : ['c_std=c11', 'warning_level=2'])

zlib_dep = dependency('zlib', version : '>=1.2.11')
m_dep = meson.get_compiler('c').find_library('m', required : false)

subdir('libimg')

executable('imgconv', 'src/main.c',
  dependencies : [libimg_dep],
  install : true)

if get_option('tests')
  subdir('tests')
endif
