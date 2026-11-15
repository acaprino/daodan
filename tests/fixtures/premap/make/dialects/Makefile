CFLAGS = -O2 -Iinclude

all: prog sublib

prog: prog.o util.o

sublib:
	$(MAKE) -C sub

test: prog
	./prog --check

clean:
	rm -f prog *.o
