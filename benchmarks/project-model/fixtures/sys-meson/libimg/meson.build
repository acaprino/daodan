libimg_inc = include_directories('include')

libimg = static_library('img', 'img.c',
  include_directories : libimg_inc,
  dependencies : [zlib_dep, m_dep],
  c_args : ['-DIMG_MAX_SIDE=4096'])

libimg_dep = declare_dependency(
  link_with : libimg,
  include_directories : libimg_inc)
