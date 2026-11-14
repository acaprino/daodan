#ifndef UTIL_H
#define UTIL_H

#define SQUARE(x) mul((x), (x))
#define LOG(msg) log_message(msg)

struct handler {
    void (*on_event)(int);
    int (*compute)(int, int);
};

int add(int a, int b);
int mul(int a, int b);
void log_message(const char *msg);
void run_callback(struct handler *h, int value);
int platform_init(void);

#endif
