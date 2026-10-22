VENV_DIR := venv
PYTHON := python3

.PHONY: all venv install clean run debug lint lint-strict

all: install

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install pydantic pygame

run: install
	$(VENV_DIR)/bin/python fly_in.py

clean:
	rm -rf $(VENV_DIR)