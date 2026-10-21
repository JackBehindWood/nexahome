VENV  := .venv
BIN   := $(VENV)/bin
# STACK=name acts on one stack. Without it, every stack except the template and the backup tool.
STACKS = $(if $(STACK),$(STACK),$(filter-out _template backup,$(notdir $(patsubst %/,%,$(wildcard stacks/*/)))))

.DEFAULT_GOAL := help
.PHONY: help up down ps status backup-init backup snapshots setup hooks unhooks check

##@ Use

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^##@ / {printf "\n%s\n", substr($$0, 5)} /^[a-z-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start stacks and wait until healthy (all, or STACK=name)
	@set -e; for s in $(STACKS); do \
		d=stacks/$$s; \
		[ -f $$d/compose.yaml ] || { echo "no such stack: $$s"; exit 1; }; \
		if [ ! -f $$d/.env ] && [ -f $$d/.env.example ]; then \
			cp $$d/.env.example $$d/.env; echo "created $$d/.env from .env.example"; fi; \
		if [ -f $$d/.env ] && grep -qE '^[A-Za-z_][A-Za-z0-9_]*=CHANGE_ME' $$d/.env; then \
			echo "$$d/.env: set a real value for each of these, then run make up again:"; \
			grep -E '^[A-Za-z_][A-Za-z0-9_]*=CHANGE_ME' $$d/.env | cut -d= -f1 | sed 's/^/  /'; exit 1; fi; \
	done
	@set -e; for s in $(STACKS); do (cd stacks/$$s && docker compose up -d --wait); done

down: ## Stop stacks; data volumes are kept (all, or STACK=name)
	@set -e; for s in $(STACKS); do (cd stacks/$$s && docker compose down); done

ps: ## Show stack status and health (all, or STACK=name)
	@set -e; for s in $(STACKS); do (cd stacks/$$s && docker compose ps); done

status: ## Show stack health and how recent the backup is
	@$(MAKE) --no-print-directory ps || echo "(no container runtime running; start it as in the README)"
	@sh scripts/backup.sh status

backup-init: ## Create the backup repository and password file (once)
	@sh scripts/backup.sh init

backup: ## Back up labelled volumes and .env files (all, or STACK=name)
	@sh scripts/backup.sh backup $(STACK)

snapshots: ## List the snapshots in the backup repository
	@sh scripts/backup.sh restic snapshots

##@ Develop

setup: ## Create .venv and install the pinned dev tools (uv if installed, else pip)
	@if command -v uv >/dev/null 2>&1; then \
		uv venv -q $(VENV) && uv pip install -q --python $(BIN)/python -r requirements-dev.txt; \
	else \
		python3 -m venv $(VENV) && $(BIN)/python -m pip install -q -r requirements-dev.txt; \
	fi

hooks: ## Install the git pre-commit hook in this repo only (opt-in)
	$(BIN)/pre-commit install

unhooks: ## Remove that hook
	$(BIN)/pre-commit uninstall

check: ## Run all checks: hooks on every file plus the Compose policy
	$(BIN)/pre-commit run --all-files
	$(BIN)/python scripts/check_compose.py
