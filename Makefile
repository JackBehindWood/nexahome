VENV  := .venv
BIN   := $(VENV)/bin
EDGE_NET := nexahome-edge
CORE := edge identity
ALL = $(filter-out _template backup,$(notdir $(patsubst %/,%,$(wildcard stacks/*/))))
# STACK=name acts on one stack. Without it, every stack except the template and the backup tool,
# with the core stacks (edge, identity) first.
STACKS = $(if $(STACK),$(STACK),$(filter $(CORE),$(ALL)) $(filter-out $(CORE),$(ALL)))

.DEFAULT_GOAL := help
.PHONY: help up down ps status smoke open backup-init backup restore snapshots setup hooks unhooks check

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
		if [ -f $$d/.env ] && grep -q '=GENERATE$$' $$d/.env; then \
			(umask 077; while IFS= read -r l || [ -n "$$l" ]; do \
				case "$$l" in *=GENERATE) printf '%s=%s\n' "$${l%%=*}" "$$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 48)";; \
				*) printf '%s\n' "$$l";; esac; done <$$d/.env >$$d/.env.tmp) && mv $$d/.env.tmp $$d/.env; \
			echo "generated secrets in $$d/.env (not shown); copy them to your password manager"; fi; \
	done
	@set -e; for s in $(STACKS); do \
		if grep -q 'name: $(EDGE_NET)' stacks/$$s/compose.yaml; then \
			docker network inspect $(EDGE_NET) >/dev/null 2>&1 || docker network create $(EDGE_NET) >/dev/null; fi; \
		(cd stacks/$$s && docker compose up -d --wait); done

down: ## Stop stacks; data volumes are kept (all, or STACK=name)
	@set -e; for s in $(STACKS); do (cd stacks/$$s && docker compose down); done

ps: ## Show stack status and health (all, or STACK=name)
	@set -e; for s in $(STACKS); do (cd stacks/$$s && docker compose ps); done

status: ## Show stack health and how recent the backup is
	@if docker info >/dev/null 2>&1; then $(MAKE) --no-print-directory ps; else echo "no container runtime running (start it as in the README)"; fi
	@sh scripts/backup.sh status

smoke: ## Read-only checks of what runs (WAIT=60 retries, VERBOSE=1 shows evidence)
	@WAIT=$(WAIT) VERBOSE=$(VERBOSE) sh scripts/smoke.sh

open: ## Open a stack's page in the browser (STACK=name; none = the sign-in page)
	@d=$$(sed -n 's/^NEXAHOME_DOMAIN=//p' stacks/edge/.env 2>/dev/null); p=$$(sed -n 's/^EDGE_PORT=//p' stacks/edge/.env 2>/dev/null); \
	url="http://$(if $(filter portal,$(STACK)),home,$(if $(filter-out identity,$(STACK)),$(STACK),id)).$${d:-nexahome.localhost}:$${p:-8088}/"; echo "$$url"; \
	if [ "$$(uname)" = Darwin ]; then open "$$url"; else xdg-open "$$url"; fi

backup-init: ## Create the backup repository and password file (once)
	@sh scripts/backup.sh init

backup: ## Back up labelled volumes and .env files (all, or STACK=name)
	@sh scripts/backup.sh backup $(STACK)

restore: ## Restore a stack into new volumes: STACK=name [SNAPSHOT=id] [TARGET=suffix]
	@SNAPSHOT=$(SNAPSHOT) TARGET=$(TARGET) sh scripts/backup.sh restore $(STACK)

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
