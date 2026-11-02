#!/bin/sh
# Deploy on this machine (make deploy): pull, check, start. Run it in the deploy-only checkout.
# Stops at the first failure and prints the next command. Safe to run again.
set -u
old=$(git rev-parse --short HEAD) || exit 1
moved=

fail() {
	printf 'FAIL  %s\nNext: %s\n' "$1" "$2" >&2
	[ -z "$moved" ] || [ "$(git rev-parse --short HEAD)" = "$old" ] || printf 'Was at %s. To go back: git checkout %s && make up (then git switch main)\n' "$old" "$old" >&2
	exit 1
}
step() {
	name=$1; next=$2; shift 2
	printf '==> %s\n' "$name"
	"$@" || fail "$name" "$next"
}

[ "$(git symbolic-ref -q HEAD)" = refs/heads/main ] || fail "not on main" "git switch main"
git diff --quiet HEAD || fail "local changes" "git status -s (this checkout is never edited; git restore . discards them)"
step pull "git status, fix the checkout, then make deploy" git pull --ff-only
moved=1
step check "fix it in the workspace and merge; if .venv is missing: make setup; then make deploy" env SKIP=no-commit-to-branch make check
step up "colima start (over ssh: docker must be on the PATH of a non-login shell), then make deploy" make up
printf 'deployed %s..%s. Then: make ps\n' "$old" "$(git rev-parse --short HEAD)"
