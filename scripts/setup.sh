#!/bin/sh
# First-time setup of this checkout (make setup). Checks what is needed, creates .venv with the
# pinned dev tools, prints what to do next. Never installs system software and changes nothing
# outside this folder.
#   sh scripts/setup.sh                       laptop, workspace or CI: tools only
#   sh scripts/setup.sh --deploy hello actual  deploy checkout: also the stacks this host runs
#                                             (.config/stacks) and push disabled (ADR 0017)
set -u
cd "$(dirname "$0")/.." || exit 1
die() { printf 'FAIL  %s\nNext: %s\n' "$1" "$2" >&2; exit 1; }
warn() { printf 'warn  %s\n      %s\n' "$1" "$2"; }

deploy=
[ "${1:-}" != --deploy ] || { deploy=1; shift; }
[ -z "$deploy" ] || [ $# -gt 0 ] || die "--deploy needs the stacks that run on this host" "sh scripts/setup.sh --deploy hello actual"
[ -n "$deploy" ] || [ $# -eq 0 ] || die "unknown argument: $1" "sh scripts/setup.sh [--deploy stack...]"

for s in "$@"; do [ -f "stacks/$s/compose.yaml" ] || die "no such stack: $s" "ls stacks"; done
for t in git make python3; do
	command -v "$t" >/dev/null 2>&1 || die "$t is not installed" "install $t (on macOS: xcode-select --install), then run setup again"
done
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
	warn "docker with compose not found" "needed for make up, not for make check; see Needs in README.md"
elif ! docker info >/dev/null 2>&1; then
	warn "no container runtime running" "start it before make up (README.md; on macOS: colima start)"
fi

# Safe to run again: an existing .venv is kept and the pinned tools are installed into it.
if command -v uv >/dev/null 2>&1; then
	{ [ -x .venv/bin/python ] || uv venv -q .venv; } && uv pip install -q --python .venv/bin/python -r requirements-dev.txt
else
	{ [ -x .venv/bin/python ] || python3 -m venv .venv; } && .venv/bin/python -m pip install -q -r requirements-dev.txt
fi || die "could not set up .venv ($(.venv/bin/python --version 2>&1 || python3 --version 2>&1))" "read the error above: no network, or a python3 too old for the pinned tools (requirements-dev.txt); fix it, then run setup again"
echo "ok    .venv with the pinned dev tools"

if [ -n "$deploy" ]; then
	mkdir -p .config && printf '%s\n' "$@" >.config/stacks && echo "ok    .config/stacks: $*"
	git remote set-url --push origin no_push && echo "ok    push disabled in this checkout"
	echo "Next: make deploy"
else
	echo "Next: make check"
fi
