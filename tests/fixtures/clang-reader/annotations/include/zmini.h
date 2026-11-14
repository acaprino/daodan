/* zmini.h -- public interface, shared by the C library and its C++ wrapper */
#ifndef ZMINI_H
#define ZMINI_H

#include "zmconf.h"

#define ZMINI_VERSION "1.0.3"

#ifdef __cplusplus
extern "C" {
#endif

ZEXTERN uLong ZEXPORT zm_adler OF((uLong adler, const Bytef *buf, unsigned len));
ZEXTERN const char * ZEXPORT zm_version OF((void));

#ifdef __cplusplus
}
#endif

#endif /* ZMINI_H */
