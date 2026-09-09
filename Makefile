.PHONY: install test smoke demo demo-offline

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -U pip
	$(BIN)/pip install -e ".[dev]"

test:
	$(BIN)/pytest -q

smoke: test
	$(BIN)/python -m tero demo --offline --yes --quiet

demo-offline:
	$(BIN)/python -m tero demo --offline --yes

demo:
	$(BIN)/python -m tero demo --yes
