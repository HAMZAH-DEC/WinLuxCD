SHELL := /usr/bin/env bash

.PHONY: all install uninstall test windows-test windows icons help

all: test

install:
	./install.sh install

uninstall:
	./install.sh uninstall

test:
	bash tests/run-tests.sh

windows-test:
	@if command -v python3 >/dev/null 2>&1; then \
		PYTHONPATH="$(CURDIR)" python3 tests/test_winluxcd.py; \
	elif command -v python.exe >/dev/null 2>&1; then \
		python.exe tests/test_winluxcd.py; \
	else \
		printf '%s\n' 'Install Python 3 before running WinLuxCD tests'; \
		exit 1; \
	fi

windows:
	@if command -v python.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then \
		python.exe "$$(wslpath -w "$(CURDIR)/build.py")"; \
	else \
		printf '%s\n' 'Build from Windows PowerShell with: python build.py'; \
		exit 1; \
	fi

icons:
	bash scripts/make-icon.sh

help:
	@echo "targets: install  uninstall  test  windows-test  windows  icons"
