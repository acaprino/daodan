/* zmini.c -- Adler-32 in the declarator style of zlib */
#include "zutil.h"

local uLong FAR mod_base OF((uLong x));

local uLong FAR mod_base(x)
    uLong x;
{
    return x % BASE;
}

uLong ZEXPORT zm_adler(adler, buf, len)
    uLong adler;
    const Bytef *buf;
    unsigned len;
{
    uLong a = adler & 0xffff;
    uLong b = (adler >> 16) & 0xffff;

    while (len--) {
        a = mod_base(a + *buf++);
        b = mod_base(b + a);
    }
    return (b << 16) | a;
}

const char * ZEXPORT zm_version()
{
    return ZMINI_VERSION;
}
