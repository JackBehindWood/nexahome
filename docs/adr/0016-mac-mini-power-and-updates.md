# 0016. Mac mini sleep, power, FileVault and updates

* **Status:** Proposed (drafted before the hardware; confirmed or corrected in P4 B1 and B2)
* **Date:** 2026-11-02

## Context
The mini is used at the desk, mostly idle, with nothing on it that must stay up ([architecture](../architecture.md)). SSH from the laptop ([ADR 0015](0015-remote-access.md)) only answers while the mini is awake and unlocked. The owner wants to sleep or shut it down by hand whenever they like, wants it to come back by itself after a power cut, keeps FileVault on, and has Wi-Fi only today but wants Ethernet to be plug and play.

Requirements and how each is verified (both on the mini): S1 `pmset -g custom` shows system sleep 0 and display sleep 10 and `pmset -g` shows autorestart on (B1); S2 after a reboot and login, `colima start && make up` restores the stacks and SSH answers (B2). Nothing personal in tracked files is the existing `make check`.

## Decision
- **Sleep and power:** no automatic system sleep on power, display sleep after 10 minutes, restart automatically after a power failure, every other power setting at its default. Manual sleep and shutdown stay allowed; while the mini sleeps or is off, SSH, deploy and local AI are unavailable and nothing else is affected.
- **FileVault:** on. Before a planned restart the admin runs `sudo fdesetup authrestart`. After a power cut the mini starts itself and waits for the disk password at the desk.
- **Updates:** no automatic macOS install. Check monthly with `softwareupdate -l`, install by hand, log the version, and re-check `sshd -T` afterwards ([ADR 0015](0015-remote-access.md)). A major upgrade waits for the owner: a mini that ships with 27 (reported, not verified) stays on it until they decide. Time sync stays at its default.
- **After a reboot:** type the disk password, then `colima start && make up`, then `make ps` (`make smoke` fails on a host without the edge, open in [ADR 0017](0017-deploy-flow.md)). Autostart is deferred (trigger: a stack that must stay up unattended), as is headless use (trigger: the mini leaves the desk).
- **Network:** Wi-Fi now. Plugging in Ethernet needs no setting (macOS prefers a wired link; not verified). Only the address changes, so keep using the Bonjour name or a DHCP reservation; if a key carries `from="<lan-cidr>"`, check the range covers both links. Wake-on-LAN is not relied on and `womp` stays at its default.
- The agent never holds `sudo`; the owner types every command below.

Operating it (the only place these live; the same values can be set in System Settings, Energy, not verified on the mini's macOS, reported as 27; B1):

| Do | Command |
| :-- | :-- |
| Apply | `sudo pmset -a sleep 0 displaysleep 10 autorestart 1` |
| Check (read-only) | `pmset -g custom` and `pmset -g` |
| Planned restart | `sudo fdesetup authrestart` |
| Monthly | `softwareupdate -l`, then install by hand |
| Undo | `sudo pmset -a restoredefaults` |

## Consequences
Easier: SSH answers whenever the mini is on and unlocked; no wake logic; a power cut needs one password and two commands. Harder: a cut or reboot leaves SSH, deploy and local AI down until the password is typed at the desk (the laptop and its stacks are unaffected); a cut is an unclean shutdown, so run `make ps` after it and `make verify` if a stack misbehaves; about 4 W idle is the M4 figure, no M6 figure was found.

Failure modes: autorestart while the owner is away leaves the mini at the prompt, harmless; an update changes defaults, re-check the values and `sshd -T`. Evolution: on a NAS or Linux host `pmset`, `fdesetup` and `softwareupdate` become systemd and power settings, LUKS and apt; a UPS (P5) removes the power-cut question. Evidence reused: [ADR 0013](0013-health-view.md) session 3 (laptop sleep: a 127 s gap in checks, clocks equal after wake, Pocket ID restarted itself, identity is not placed on the mini); re-measure only if automatic sleep is ever chosen.

## Alternatives
| Option | Decision | Reconsider when |
| :-- | :-- | :-- |
| Automatic sleep after idle | rejected: SSH and deploy fail while asleep, remote wake unreliable | never planned; the owner can sleep it by hand |
| Wake-on-LAN | rejected: reported unreliable on Apple silicon, wakes a sleeping Mac, never a powered-off one | automatic sleep is chosen |
| `caffeinate` or a launchd keep-awake, `disablesleep` | rejected: `pmset` values are visible, `disablesleep` blocks manual sleep | never |
| `disksleep 0` | rejected: little effect on an SSD, one more key to verify | a disk that spins |
| FileVault off, auto-login | rejected: the owner keeps FileVault; auto-login needs it off | never |
| SSH unlock of FileVault before login (reported for macOS 26 on Apple silicon) | not decided: one B1 test; may need a password, which key-only SSH forbids | B1 result |
| MDM or unattended update tooling | rejected: one machine | a second machine |

## Verification and status
Read-only on the laptop (macOS 27.0.1, FileVault on): `sleep`, `displaysleep` and `womp` exist and read back with `pmset -g custom`. The laptop has no `autorestart` key, so that setting is unchecked here. **Not verified:** the `pmset` keys and `autorestart` on the M6 with its macOS (reported 27) and FileVault, `authrestart`, SSH unlock before login, M6 idle power, the macOS version the mini ships with, `softwareupdate -l` output, Ethernet behaviour (no cable yet), the effect of an unclean shutdown on Colima volumes. Sources are forums and blogs, not Apple documents: [macpowerusers](https://talk.macpowerusers.com/t/mac-mini-as-server/9362), [TidBITS on Wake-on-LAN](https://talk.tidbits.com/t/wake-on-lan-with-apple-silicon/33183), [Jeff Geerling on FileVault in macOS 26](https://www.jeffgeerling.com/blog/2025/you-can-finally-manage-macs-filevault-remotely-tahoe/).
