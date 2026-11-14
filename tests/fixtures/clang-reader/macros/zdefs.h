#ifndef ZDEFS_H
#define ZDEFS_H

#ifdef SYS16BIT
#  define far_ptr far
#else
#  define far_ptr
#endif
#define local static
#ifdef BUILD_DLL
#  define zextern extern __declspec(dllexport)
#else
#  define zextern extern
#endif
#define zlimit 15
#define word unsigned

#ifdef __cplusplus
extern "C" {
#endif

zextern int checksum(const unsigned char far_ptr *buf, int len);

#ifdef __cplusplus
}
#endif

#endif
