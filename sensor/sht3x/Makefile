# define the C compiler to use
CC = /opt/loongarch64-linux-gnu-gcc13.3/bin/loongarch64-loongson-linux-gnu-gcc

# define any compile-time flags
CFLAGS = -Wall -g -O

# define the C source files
SRCS = main.c sht3x.c

# define the C object files 
OBJS = $(SRCS:.c=.o)

# define the executable file 
MAIN = sht31e

.PHONY: depend clean

all: $(MAIN)
@echo: $(MAIN) have been compiled

$(MAIN): $(OBJS) 
	$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJS) $(LFLAGS) $(LIBS)

.c.o:
	$(CC) $(CFLAGS) $(INCLUDES) -c $<  -o $@

clean:
	$(RM) *.o *~ $(MAIN)

depend: $(SRCS)
	makedepend $(INCLUDES) $^
