#!/bin/sh
# Back up every volume labelled nexahome.backup=true, plus each backed-up stack's .env, with restic.
# Usage: scripts/backup.sh init | backup [stack] | restore <stack> | fingerprint <volume> | status | restic <restic arguments>   (see make help)
# Settings come from the environment or stacks/backup/.env; see stacks/backup/.env.example.
set -eu
cd "$(dirname "$0")/.."

[ -f stacks/backup/.env ] && { set -a; . stacks/backup/.env; set +a; }
ROOT=$(pwd)
DIR=${NEXAHOME_BACKUP_DIR:-$ROOT/data/backup}
PW=${NEXAHOME_RESTIC_PASSWORD_FILE:-$ROOT/.config/restic-password}
export NEXAHOME_BACKUP_DIR="$DIR" NEXAHOME_RESTIC_PASSWORD_FILE="$PW"

die() { echo "backup: $*" >&2; exit 1; }

# Run restic in the one-shot job container; extra docker options (volumes) come before "restic".
job() { docker compose -f stacks/backup/compose.yaml run --rm -T "$@"; }

need_runtime() {
	docker info >/dev/null 2>&1 ||
		die "no container runtime is running. On macOS start Colima as in the README (colima start --cpu 2 --memory 2 --disk 20)."
}

# Fail closed: never create anything here, only check.
need_repo() {
	[ -f "$PW" ] || die "password file missing: $PW. Run 'make backup-init' (first time), or restore your saved copy there."
	[ "$(ls -ld "$PW" | cut -c5-10)" = "------" ] || die "password file is readable by others; run: chmod 600 '$PW'"
	[ -f "$DIR/config" ] || die "no repository at $DIR. Run 'make backup-init', or mount the right directory. If it is outside your home directory it must be shared with the Colima VM (stacks/backup/README.md)."
}

STOPPED=
restart_stopped() {
	for s in $STOPPED; do (cd "stacks/$s" && docker compose start) || echo "backup: could not restart $s; run: make up STACK=$s" >&2; done
	STOPPED=
}

cmd_init() {
	[ ! -e "$PW" ] || die "password file already exists: $PW (not overwriting)"
	[ ! -e "$DIR/config" ] || die "a repository already exists at $DIR (not overwriting)"
	for f in "$PW" "$DIR"; do
		case "$f" in "$ROOT"/*)
			git check-ignore -q "$f" || die "$f is inside the repository but not gitignored; refusing to write there." ;;
		esac
	done
	need_runtime
	mkdir -p "$DIR"
	(umask 077; mkdir -p "$(dirname "$PW")"; LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 40 >"$PW")
	if ! job restic init || [ ! -f "$DIR/config" ]; then
		rm -f "$PW"
		die "repository was not created on the host. A directory outside your home directory must be shared with the Colima VM; see stacks/backup/README.md."
	fi
	cat <<EOF

Repository:    $DIR   (delete this folder to remove all backups)
Password file: $PW

Save a copy of the password file in a password manager now. Without it every snapshot is
unreadable, and nothing can recover it. Keep the copy away from this laptop and the backup disk.
A repository on the same disk as your data is a drill, not protection: copy it to an
external disk, or point NEXAHOME_BACKUP_DIR at one.

Next: make backup
EOF
}

cmd_backup() {
	only=${1:-}
	need_runtime
	need_repo
	pairs=$(docker volume ls -q --filter label=nexahome.backup=true | while read -r v; do
		p=$(docker volume inspect -f '{{index .Labels "com.docker.compose.project"}}' "$v")
		echo "${p#nexahome-} $v"
	done)
	[ -n "$pairs" ] || die "no volume is labelled nexahome.backup=true; start a stack first (make up)."
	stacks=$(echo "$pairs" | cut -d' ' -f1 | sort -u)
	if [ -n "$only" ]; then
		echo "$stacks" | grep -qx "$only" || die "no labelled volume for stack '$only'."
		stacks=$only
	fi
	trap restart_stopped EXIT INT TERM
	n=0
	for s in $stacks; do
		set --
		for v in $(echo "$pairs" | awk -v s="$s" '$1 == s {print $2}'); do set -- "$@" -v "$v:/data/$v:ro"; done
		paths=/data
		[ -f "stacks/$s/.env" ] && paths="$paths /stacks/$s/.env"
		if [ -d "stacks/$s" ] && [ -n "$(cd "stacks/$s" && docker compose ps -q 2>/dev/null)" ]; then
			echo "stopping $s for a consistent copy"
			(cd "stacks/$s" && docker compose stop)
			STOPPED="$STOPPED $s"
		fi
		echo "backing up $s"
		# shellcheck disable=SC2086  # $paths is a list of simple paths
		job "$@" restic backup --tag "stack=$s" $paths
		restart_stopped
		n=$((n + 1))
	done
	job restic check
	echo "backup ok: $n stack(s) saved, repository checked. Not trusted until you have restored it once: docs/runbooks/restore.md."
}

# Restore a stack's snapshot into new volumes (project nexahome-<stack>[-<TARGET>]). Never deletes anything.
# The volumes are first created from the app image (compose create), which gives them the app's ownership;
# restic then fills them as the job user, with each volume mounted at its original path and --target /.
cmd_restore() {
	s=${1:-}
	[ -n "$s" ] || die "usage: make restore STACK=name [SNAPSHOT=id] [TARGET=suffix]  (ids: make snapshots)"
	[ -f "stacks/$s/compose.yaml" ] || die "no such stack: $s"
	snap=${SNAPSHOT:-latest}
	proj=nexahome-$s${TARGET:+-$TARGET}
	cleanup="(cd stacks/$s && docker compose -p $proj down -v)"
	need_runtime
	need_repo
	keys=$(job restic ls --tag "stack=$s" "$snap" /data | sed -n 's|^/data/\([^/][^/]*\)$|\1|p') || keys=
	[ -n "$keys" ] || die "no snapshot of stack '$s' found (snapshot: $snap). See: make snapshots"
	for key in $keys; do
		nv=${proj}_${key#nexahome-"${s}"_}
		if docker volume inspect "$nv" >/dev/null 2>&1; then
			die "volume $nv already exists; restore does not overwrite. For a separate copy add TARGET=<suffix>. To replace it, stop the stack and remove the volume yourself (docker volume rm $nv), then run this again."
		fi
	done
	# .env first (compose may need it); only when absent, written on the host, never printed.
	if [ ! -e "stacks/$s/.env" ] && job restic ls --tag "stack=$s" "$snap" "/stacks/$s/.env" | grep -qx "/stacks/$s/.env"; then
		(umask 077; job restic dump --tag "stack=$s" "$snap" "/stacks/$s/.env" >"stacks/$s/.env") ||
			{ rm -f "stacks/$s/.env"; die "could not restore stacks/$s/.env"; }
		echo "restored stacks/$s/.env"
	fi
	(cd "stacks/$s" && docker compose -p "$proj" create) || die "could not create the volumes. Clean up with: $cleanup"
	for key in $keys; do
		nv=${proj}_${key#nexahome-"${s}"_}
		echo "restoring $key into volume $nv"
		job -v "$nv:/data/$key" restic restore "$snap" --tag "stack=$s" --target / --include "/data/$key" --verify ||
			die "restore failed. Remove the partial copy with: $cleanup"
	done
	cat <<EOF

Restored into project $proj (snapshot: $snap).
EOF
	if [ -n "${TARGET:-}" ]; then
		echo "Start it:   (cd stacks/$s && docker compose -p $proj up -d --wait)   (set the stack's port variable to a free port)"
		echo "Remove it:  $cleanup   (it carries the backup label; the next make backup would save it)"
	else
		echo "Start it:   make up STACK=$s"
	fi
}

# One hash over uid:gid, mode, content hash and path of every file in a volume, plus the file count.
# Compare before and after a restore, with the stack stopped.
cmd_fingerprint() {
	v=${1:-}
	[ -n "$v" ] || die "usage: scripts/backup.sh fingerprint <volume>"
	need_runtime
	need_repo
	job -v "$v:/v:ro" --entrypoint sh restic -c \
		'cd /v && find . -type f | sort | while read -r f; do echo "$(stat -c "%u:%g %a" "$f") $(sha256sum "$f")"; done | sha256sum; find . -type f | wc -l'
}

cmd_status() {
	if [ ! -f "$DIR/config" ]; then
		echo "backup: no repository at $DIR (make backup-init)"
		return 0
	elif [ -n "$(find "$DIR/snapshots" -type f -mtime -7 2>/dev/null | head -n 1)" ]; then
		echo "backup: last snapshot within 7 days"
	elif [ -n "$(find "$DIR/snapshots" -type f 2>/dev/null | head -n 1)" ]; then
		echo "backup: last snapshot OLDER than 7 days (make backup)"
	else
		echo "backup: repository has no snapshots yet (make backup)"
	fi
	echo "backup: repository size $(du -sh "$DIR" | cut -f1) in $DIR"
}

case "${1:-}" in
	init) cmd_init ;;
	backup) shift; cmd_backup "$@" ;;
	restore) shift; cmd_restore "$@" ;;
	fingerprint) shift; cmd_fingerprint "$@" ;;
	status) cmd_status ;;
	restic) shift; need_runtime; need_repo; job restic "$@" ;;
	*) die "usage: scripts/backup.sh init | backup [stack] | restore <stack> | fingerprint <volume> | status | restic <arguments>" ;;
esac
