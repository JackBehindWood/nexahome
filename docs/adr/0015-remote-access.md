# 0015. Remote access to the Mac mini

* **Status:** Proposed (drafted before the hardware; confirmed or corrected in P4 B1)
* **Date:** 2026-11-02

## Context
The goal is decided: SSH from the laptop to the Mac mini for administration, deployment, VS Code Remote-SSH, Claude Code and file transfer ([register](../project.md#decision-register)). The method is not. Use is at the desk, over Wi-Fi, for one owner with two machines, and nothing on the mini must stay up ([architecture](../architecture.md#remote-access)).

Threats: other devices on the home network, a compromised container or dependency, a lost or stolen device, an over-reaching AI agent. A targeted attacker is out of scope.

Requirements and how each is verified (P4-A1 and P4-A2 only on the mini): A1 key login works with no password prompt (`ssh <alias> true` exits 0); A2 password and keyboard-interactive login are refused (the attempt ends "Permission denied (publickey)"); A3 the runbook works for someone cold and holds no real host, user or address (cold read, `make check`); A4 the host key is checked at first connect (fingerprint compared at the mini); A5 the effective sshd values equal the list below (`sshd -T`); X1 nothing personal in tracked files (`make check`, `git diff --staged`).

## Decision
SSH with keys only, on the LAN only: no port forward, no public DNS, no VPN until a need exists. The commands live once, in the [runbook](../runbooks/mini-ssh.md).

- **Server:** a drop-in `/etc/ssh/sshd_config.d/050-nexahome.conf` with `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no`, `AuthenticationMethods publickey`, `AllowUsers <daily-user>`, `MaxAuthTries 3`, `AllowAgentForwarding no`, `X11Forwarding no`. TCP forwarding stays on (model tunnel, Remote-SSH). The daily user is not an admin; the agent never holds `sudo`.
- **Keys:** ed25519 with a passphrase, one per client, never copied between machines. Each `authorized_keys` line may carry `from="<lan-cidr>"`. `restrict` is not used (it would disable what Remote-SSH needs).
- **Model server:** listens on the mini's loopback only and is reached through an SSH tunnel, not a port.
- **Git:** the deploy checkout pulls over anonymous HTTPS (the repository is public; no key, push disabled, see [ADR 0017](0017-deploy-flow.md)); the workspace checkout pushes with a per-device user key (passphrase, Keychain). Agent forwarding is rejected both ways (client `ForwardAgent no`, server `AllowAgentForwarding no`): a compromised mini must not borrow the laptop's keys.
- **Finding the mini:** Bonjour name, or a DHCP reservation in the router.

### Remote access from outside the home (decision deferred)
Trigger to build: the first need to reach the mini away from home. Built in P6 ([roadmap](../roadmap.md)); the gate in [ADR 0011](0011-edge-and-local-hostnames.md) for leaving loopback stays the precondition.

| | WireGuard on the router or a server | Tailscale Personal |
| :-- | :-- | :-- |
| Control plane | none, you run it | third-party coordination server and account |
| Setup | needs a router or host that supports it (not verified) and one open port | one install per device; free-tier terms not read at the source |
| Cost | none | free tier as reported, not verified |

Leaning: WireGuard (open, no third party); Tailscale only if the router cannot do it.

## Consequences
Easier: a small surface, nothing public, one runbook, the same settings on a Linux host later. Harder: no access away from home until P6; a lost key means editing `authorized_keys` at the desk; a rebooted mini does not answer SSH until the disk password is typed at the desk (FileVault; the power and update policy is in [ADR 0016](0016-mac-mini-power-and-updates.md)).

Failure modes: key lost, other client or desk login; wrong drop-in, desk login and delete the file (only remote login is affected); macOS update changes SSH defaults, desk login and correct the runbook (re-check `sshd -T` after every update); Wi-Fi drops or the address changes, Bonjour name or reservation.

Evolution: mini to NAS or Linux host keeps the same settings and runbook shape (the drop-in directory is common on Linux, not verified); P6 turns the comparison above into a build.

## Alternatives
Deferred or rejected, with the trigger to reconsider:

| Option | Decision | Reconsider when |
| :-- | :-- | :-- |
| Password SSH | rejected | never |
| SSH certificates, SSO, bastion host | rejected: one person, two machines | a third machine or a second human |
| FIDO2 hardware keys (`ed25519-sk`) | deferred | a lost-key scare, or keys on more than two machines |
| Keys in the Secure Enclave via a third-party app | rejected: ECDSA only, one more dependency | never for now |
| fail2ban | rejected: no password path to brute-force | passwords are ever enabled |
| Agent forwarding | rejected (above) | never |
| Tailscale SSH | rejected: needs the VPN decision first | P6 |
| Screen Sharing / VNC | deferred | a task that needs the mini's GUI from the laptop |
| `ssh-audit` or similar checker | not added | B1, with the install questions asked first |
| Docker context over SSH | rejected for deploy ([ADR 0017](0017-deploy-flow.md)) | never |

## Verification and status
Rehearsed on 2026-11-02 against a throwaway non-root `sshd` on the laptop (macOS 27, not the mini's version): A1, A2 and A5 behaved as written, A4's procedure worked, `from=` and the tunnel worked. Details are in the runbook's evidence section. **Not confirmed on a real mini** (P4-X4): `sshd_config.d` handling and PAM on its macOS version, Remote Login, Bonjour on this network, the `from=` range as seen by the mini, VS Code Remote-SSH, rsync over SSH and Full Disk Access (B3), Tailscale terms, router VPN support. B1 tests the first group, B3 and B4 the rest.
