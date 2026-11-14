CC ?= cc
AR ?= ar
CFLAGS ?= -O2
CFLAGS += -std=c99 -Wall -Iinclude
CPPFLAGS += -DMINI_LOG_LEVEL=2
LDLIBS = -lm

LIB = build/libmini.a
APP = build/mini
OBJS = build/vec.o build/log.o

.PHONY: all test install clean

all: $(APP)

$(APP): app/main.c $(LIB)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(CPPFLAGS) -o $@ app/main.c $(LIB) $(LDLIBS)

$(LIB): $(OBJS)
	$(AR) rcs $@ $^

build/%.o: lib/%.c include/mini.h
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ $<

test: $(APP)
	./$(APP) --self-test

install: $(APP)
	install -m 755 $(APP) $(DESTDIR)/usr/local/bin/mini

clean:
	rm -rf build
