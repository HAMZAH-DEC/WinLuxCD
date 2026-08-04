SHELL := /usr/bin/env bash

.PHONY: all install uninstall test icons help

all: test

install:
	./install.sh install

uninstall:
	./install.sh uninstall

test:
	bash tests/run-tests.sh

icons:
	bash scripts/make-icon.sh

help:
	@echo "targets: install  uninstall  test  icons"
