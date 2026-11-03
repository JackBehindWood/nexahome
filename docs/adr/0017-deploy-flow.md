# 0017. Deploy flow to the Mac mini

* **Status:** Proposed (drafted before the hardware; confirmed or corrected in P4 B2)
* **Date:** 2026-11-02

## Context
Code reaches the mini from GitHub and must start there without surprises. One owner, one target host, a public repository, SSH from the laptop ([ADR 0015](0015-remote-access.md)). The earlier idea of `make upgrade` through a Docker context over SSH is dropped: `make upgrade` was cut in P2, and a context would run the Makefile's `.env` creation and `scripts/backup.sh` on the client with client paths.

Requirements and how each is verified: D1 a deploy pulls, checks and starts on the target, stops at the first failure and prints the next command (rehearsed on the laptop with injected failures); D2 `make check` passes on the mini (exit 0, B2); D3 `hello` and `actual` are healthy on the mini (`make up`, `make ps`, B2); D4 a rollback to the previous commit works and data comes back with `make restore` (exercised once on the laptop, again in B2). D2 and D3 are Track B only.

## Decision
The mini keeps two checkouts, both under `$HOME` (the container runtime mounts only the home directory):

- **Deploy checkout** `~/nexahome`: never edited, pulls from the public repository over anonymous HTTPS (no key on the mini for this), push disabled with `git remote set-url --push origin no_push`. **Stacks start only from here:** `.env` secrets and `data/backup` live per checkout, so a second `make up` elsewhere would generate different secrets.
- **Workspace checkout** `~/dev/nexahome`: Remote-SSH, Claude Code, branches and pushes with the per-device key ([ADR 0015](0015-remote-access.md)). It never runs `make up`.

**One command**, at the desk or from the laptop:

```
cd ~/nexahome && make deploy
ssh <mini-alias> 'cd ~/nexahome && make deploy'
```

`make deploy` runs [`scripts/deploy.sh`](../../scripts/deploy.sh). Two guards (on `main`; no local changes), then `git pull --ff-only`, `SKIP=no-commit-to-branch make check`, `make up`. Each failure prints `FAIL <step>` and `Next: <command>`; once the pull has moved the checkout it also prints the previous commit and how to go back. It is safe to run again. It ends with `make ps` (`make up` already waits for health).

**Which stacks run here.** A gitignored `.config/stacks` in the deploy checkout lists them, one per line; the Makefile reads it, so `make up`, `down`, `ps` and `deploy` all honour it, and `STACK=name` still overrides. Without the file every stack is used (the laptop). First deploy on the mini:

```
git clone https://github.com/<owner>/nexahome.git ~/nexahome && cd ~/nexahome
sh scripts/setup.sh --deploy hello actual
make deploy
```

[`scripts/setup.sh`](../../scripts/setup.sh) is also what `make setup` runs (without `--deploy`, for the laptop, a workspace and CI). It checks `git`, `make` and `python3` (stops with the next command if one is missing), warns when Docker or its runtime is absent, creates `.venv` with the pinned tools, and with `--deploy` writes `.config/stacks` and disables push. It never installs system software and is safe to run again. `make up` creates each `.env` and generates secrets; copy them to the password manager. The mini needs Xcode command line tools, Homebrew and Colima first ([plan](../roadmap.md), B2).

**Rollback.** `git checkout <previous-sha> && make up`, then `git switch main` before the next deploy (a detached checkout is refused by the guard). Data: `make restore` (never overwrites; an app that migrated its data forward may not run on the old version, so restore a backup taken before the deploy).

## Consequences
Easier: one memorable command, failures name the next step, nothing special on the laptop, no secret on the mini for pulling, the mini cannot push from the deploy checkout. Harder: a deploy needs an SSH session or the desk; the checkout moves to the new commit before `make check` runs, so a failing check leaves it ahead of what runs (the message gives the way back); two checkouts to keep straight; the history of deploys is the git log and the session log.

Failure modes: check fails, nothing starts and the old stacks keep running; Colima stopped, stops at `up` with `colima start`; local changes or a detached HEAD, stopped by a guard before anything is pulled; GitHub unreachable, `git pull` fails and nothing changes; SSH drops mid-deploy, rerun it; unhealthy container, `up` fails after `--wait` (read `make ps` and the container logs).

Evolution: laptop to mini changes the checkout path, `.config/stacks`, data and backup directories and the Colima size; the command stays. Mini to NAS or Linux host: same command and script, always-on stacks move there with `make restore`.

**Open (decide in B2): `make smoke` on a partial host.** `scripts/smoke.sh` fails with "edge: not running" on any host that does not run the edge, so a hello-and-actual mini cannot pass it (rehearsed). Until decided, ADR 0016's "then `make smoke`" after a reboot reads `make ps`. Fixes: give smoke a partial-host mode that reads `.config/stacks`, or run the edge on the mini (which reverses part of the [workload table in ADR 0014](0014-mac-mini-hardware.md)).

## Alternatives
Practice was checked in a short web look at homelab threads and tool pages, plus general knowledge; nothing here rests on one source.

| Option | Decision | Reconsider when |
| :-- | :-- | :-- |
| Pull on the target over SSH | adopted | never planned |
| One script behind one make target | adopted: sh glue of about 25 lines, no logic copied into a third script | the script passes about 100 lines ([code package](../roadmap.md)) |
| `docker context` over SSH | rejected: the Makefile's `.env` and backup paths run on the client | never |
| Read-only deploy key for pull | rejected while the repository is public: one more secret to create and lose for no gain | the repository goes private |
| Self-hosted CI runner or webhook pull | rejected: runs code from a public repository on the mini | never planned |
| launchd or systemd timer that pulls and starts | deferred: FileVault and a manual Colima start make unattended deploys moot | a stack must stay up unattended, or the mini is always on |
| Watchtower, Flux, Argo, Portainer or Komodo | rejected: unpinned tags, Kubernetes, or a UI for many hosts; Dependabot pull requests are the update path | more than one host |
| Laptop `make deploy` wrapper with host variables | rejected by the owner for now: two ways to do one thing | the `ssh` line is typed often enough to hurt |
| One checkout, or a `git worktree` | rejected: one checkout would switch the running stacks with every branch; a worktree adds a concept and breaks when its parent is deleted | never |
| Automated bootstrap of the whole mini (a script that installs Homebrew, Colima and the rest) | rejected: it changes system settings, needs `sudo` and GUI steps, and differs per macOS version; `setup.sh` only prepares a checkout | a second rebuild of any host |
| Configuration management (Ansible) | rejected: one machine, the runbook is the configuration | a third machine |

## Verification and status
Rehearsed on 2026-11-02 on the laptop (macOS 27, GNU make 3.81, Colima), in a second checkout under `data/` against a throwaway bare repository, with `hello` only under a throwaway project name and port; everything removed afterwards and the Docker state matched the start.

| Case | Result |
| :-- | :-- |
| Clean deploy (pull, check, up) | pass, hello healthy |
| Plain `git pull --ff-only` with a non-overlapping local change | it does not refuse, hence the explicit guard |
| `make deploy` with a local change | stopped at the guard, nothing pulled |
| Failing check (bad commit upstream) | stopped at `check`, running container untouched, previous commit and way back printed |
| Rollback `git checkout <sha>` and `make up`, then deploy on the detached checkout | guard says `git switch main`; the Compose files were identical, so the container did not change: the rollback is only mechanically exercised |
| Recovery by an upstream revert | pass |
| `make check` on `main` without `SKIP` | fails at the no-commit hook, hence `SKIP` |
| `.config/stacks` | `make -n up` lists only the file's stacks; without it, all six as before |
| `make smoke` on a hello-only host | fails: edge not running (open item above) |
| Colima stopped | stopped at `up` with the `colima start` hint |
| `scripts/setup.sh`, scratch copy | uv path and pip path (modern Python) pass; a second run is safe; `--deploy` writes the list and disables push; an unknown stack, a missing argument and a missing tool stop with the next command; a venv built on an old Python fails with the Python version named. Found and fixed: a half-made `.venv` made the second run fail |

Findings along the way: the checkout must be under `$HOME` (a checkout in `/private/tmp` gave hello an empty web root and an unhealthy container); `COMPOSE_PROJECT_NAME` must not be exported while `make check` runs (`check_compose.py` enforces `nexahome-<stack>`), so the rehearsal set it in hello's `.env`.

**Not confirmed on a real mini** (P4-X4): D2 and D3; `make setup` (the rehearsal reused the laptop's `.venv`); GNU make version and Xcode command line tools there; anonymous HTTPS from the mini's network; whether `docker` and `colima` are on the PATH of a non-login shell, which is what `ssh <mini-alias> '...'` starts (a Homebrew PATH set only in `~/.zprofile` is not seen; `~/.zshenv` is; docker case is inference, check with `ssh <mini-alias> 'command -v docker'` in B2); behaviour with `actual` and image tag changes; Linux; a rollback that changes Compose files.
