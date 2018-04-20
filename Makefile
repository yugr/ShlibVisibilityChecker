# The MIT License (MIT)
# 
# Copyright (c) 2018 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

$(shell mkdir -p bin)

LLVM_CONFIG = llvm-config-5.0

CXX = g++

CXXFLAGS = $(shell $(LLVM_CONFIG) --cflags)
CXXFLAGS += -std=c++11 -Wall -Wextra -Werror
CXXFLAGS += -g -O0

LDFLAGS = $(shell $(LLVM_CONFIG) --ldflags)

all: bin/read_header_api

check:
	scripts/ifacecheck libacl1

bin/read_header_api: bin/read_header_api.o
	$(CXX) $(LDFLAGS) -o $@ $^ -lclang

bin/%.o: src/%.cc
	$(CXX) $(CXXFLAGS) -o $@ -c $^

clean:
	rm -f bin/*

.PHONY: check all
