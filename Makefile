# The MIT License (MIT)
# 
# Copyright (c) 2018-2022 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

$(shell mkdir -p bin)

LLVM_CONFIG ?= llvm-config
DESTDIR ?= /usr/local

CXX ?= g++

CXXFLAGS = $(shell $(LLVM_CONFIG) --cflags) -std=c++11 -g -Wall -Wextra -Werror
LDFLAGS = $(shell $(LLVM_CONFIG) --ldflags) -Wl,--warn-common

ifneq (,$(COVERAGE))
  DEBUG = 1
  CXXFLAGS += --coverage -DNDEBUG
  LDFLAGS += --coverage
endif
ifeq (,$(DEBUG))
  CXXFLAGS += -O2
  LDFLAGS += -Wl,-O2
else
  CXXFLAGS += -O0
endif
ifneq (,$(ASAN))
  CXXFLAGS += -fsanitize=address -fsanitize-address-use-after-scope -U_FORTIFY_SOURCE -fno-common -D_GLIBCXX_DEBUG -D_GLIBCXX_SANITIZE_VECTOR
  LDFLAGS += -fsanitize=address
endif
ifneq (,$(UBSAN))
  ifneq (,$(shell $(CXX) --version | grep clang))
    # Isan is clang-only...
    CXXFLAGS += -fsanitize=undefined,integer -fno-sanitize-recover=undefined,integer
    LDFLAGS += -fsanitize=undefined,integer -fno-sanitize-recover=undefined,integer
  else
    CXXFLAGS += -fsanitize=undefined -fno-sanitize-recover=undefined
    LDFLAGS += -fsanitize=undefined -fno-sanitize-recover=undefined
  endif
endif

all: bin/read_header_api

install:
	mkdir -p $(DESTDIR)
	install bin/read_header_api $(DESTDIR)/bin

check:
	shlibvischeck-debian libacl1

pylint:
	pylint shlibvischeck

bin/read_header_api: bin/read_header_api.o Makefile bin/FLAGS
	$(CXX) $(LDFLAGS) -o $@ $(filter %.o, $^) -lclang

bin/%.o: src/%.cc Makefile bin/FLAGS
	$(CXX) $(CXXFLAGS) -o $@ -c $<

bin/FLAGS: FORCE
	if test x"$(CXXFLAGS) $(LDFLAGS)" != x"$$(cat $@)"; then \
		echo "$(CXXFLAGS) $(LDFLAGS)" > $@; \
	fi

clean:
	rm -rf bin/* build dist *.egg-info
	find -name \*.gcov -o -name \*.gcno -o -name \*.gcda | xargs rm -rf
	find -o -name .coverage -o -name \*.xml | xargs rm -rf

.PHONY: check all install clean pylint FORCE
