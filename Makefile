.PHONY: install test smoke demo demo-offline tui

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
	$(BIN)/python -m tero demo --offline --yes --quiet --carpeta examples/carpeta-demo

demo-offline:
	$(BIN)/python -m tero demo --offline --yes --carpeta examples/carpeta-demo

demo:
	$(BIN)/python -m tero demo --yes --carpeta examples/carpeta-demo

tui:
	$(BIN)/python -m tero tui --offline
