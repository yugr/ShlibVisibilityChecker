# The MIT License (MIT)
# 
# Copyright (c) 2018-2020 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

$(shell mkdir -p bin)

LLVM_CONFIG ?= llvm-config
DESTDIR ?= /usr/local/bin

CXX = g++

CXXFLAGS = $(shell $(LLVM_CONFIG) --cflags) -std=c++11 -g -Wall -Wextra -Werror
LDFLAGS = $(shell $(LLVM_CONFIG) --ldflags)

ifeq (,$(DEBUG))
  CXXFLAGS += -O2
  LDFLAGS += -Wl,-O2
else
  CXXFLAGS += -O0
endif
ifneq (,$(ASAN))
  CXXFLAGS += -fsanitize=address
  LDFLAGS += -fsanitize=address
endif
ifneq (,$(UBSAN))
  CXXFLAGS += -fsanitize=undefined
  LDFLAGS += -fsanitize=undefined
endif

all: bin/read_header_api

install:
	mkdir -p $(DESTDIR)
	install bin/read_header_api $(DESTDIR)

check:
	shlibvischeck-debian libacl1

pylint:
	pylint shlibvischeck

bin/read_header_api: bin/read_header_api.o
	$(CXX) $(LDFLAGS) -o $@ $^ -lclang

bin/%.o: src/%.cc
	$(CXX) $(CXXFLAGS) -o $@ -c $^

clean:
	rm -f bin/* build dist *.egg-info

.PHONY: check all install clean pylint
