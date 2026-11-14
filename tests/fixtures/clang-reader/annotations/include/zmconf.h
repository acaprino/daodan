/* zmconf.h -- configuration of the zmini library, in the style of zconf.h */
#ifndef ZMCONF_H
#define ZMCONF_H

#if defined(_WIN32) && defined(ZMINI_DLL)
#  define ZEXPORT __stdcall
#  define ZEXTERN extern __declspec(dllimport)
#else
#  define ZEXPORT
#  define ZEXTERN extern
#endif

#ifndef FAR
#  define FAR
#endif

/* prototypes, kept for compilers without them */
#ifndef OF
#  define OF(args) args
#endif

#define local static

typedef unsigned char Byte;
typedef Byte FAR Bytef;
typedef unsigned long uLong;

#endif /* ZMCONF_H */
