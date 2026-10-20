VENV  := .venv
BIN   := $(VENV)/bin
STACK ?= hello

.PHONY: help setup hooks unhooks check up down ps

help:
	@echo "setup    create ./.venv and install pinned dev tools (uses uv if installed, else pip)"
	@echo "hooks    install the git pre-commit hook in this repo only (opt-in)"
	@echo "unhooks  remove that hook"
	@echo "check    run all checks (hooks on every file + compose policy)"
	@echo "up/down/ps  manage a stack, e.g. make up STACK=hello"

setup:
	@if command -v uv >/dev/null 2>&1; then \
		uv venv -q $(VENV) && uv pip install -q --python $(BIN)/python -r requirements-dev.txt; \
	else \
		python3 -m venv $(VENV) && $(BIN)/python -m pip install -q -r requirements-dev.txt; \
	fi

hooks:
	$(BIN)/pre-commit install

unhooks:
	$(BIN)/pre-commit uninstall

check:
	$(BIN)/pre-commit run --all-files
	$(BIN)/python scripts/check_compose.py

up:
	cd stacks/$(STACK) && docker compose up -d --wait

down:
	cd stacks/$(STACK) && docker compose down

ps:
	cd stacks/$(STACK) && docker compose ps
