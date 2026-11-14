int pick(int w) {
    if (w == 1) {
        w = 2;
    }
#ifdef GZIP
    else if (w == 2) {
        w = 3;
    }
#endif
    return w;
}
