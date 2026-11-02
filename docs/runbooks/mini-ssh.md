# SSH access to the Mac mini

Version 0.1 · Last reviewed 2026-11-02

**Status: drafted, not confirmed on a real mini.** Written before the hardware arrived; every step marked "not verified" is tested in the bring-up session (P4 B1) and this banner is removed only then.

**Audience:** the person who runs NexaHome. **Admin rights needed:** yes, on the mini: one step creates a file under `/etc/ssh/` with `sudo`, typed by you. Design: [ADR 0015](../adr/0015-remote-access.md). Placeholders: `<daily-user>` (standard user on the mini), `<admin-user>` (admin user on the mini), `<mini-host>` (the mini's name), `<mini-alias>` (short name in your laptop's SSH config), `<device>` (name of the client), `<lan-cidr>` (your home network range).

## Set your values once

Paste this block, with your own values, into each terminal you use below (laptop and mini). Every command then runs unchanged. Nothing is saved; nothing here is committed.

```sh
export MINI_USER=<daily-user> MINI_HOST=<mini-host>.local MINI_DEVICE=<device> LAN_CIDR=<lan-cidr>
```

## Five steps

1. Laptop: create a key for this client, with a passphrase.

   ```sh
   ssh-keygen -t ed25519 -a 100 -C "nexahome-$MINI_DEVICE" -f ~/.ssh/nexahome_mini
   ```

2. Mini, at the desk: System Settings, General, Sharing, Remote Login on; allow access for `<daily-user>` only.
3. Laptop: install the public key. Password login still works at this point; this is the last time it is used.

   ```sh
   ssh-copy-id -i ~/.ssh/nexahome_mini.pub "$MINI_USER@$MINI_HOST"
   ```

4. Mini, as `<admin-user>`: switch off passwords with a drop-in file. Keep a second SSH session open while you do this.

   ```sh
   grep -n '^Include' /etc/ssh/sshd_config      # expect: Include /etc/ssh/sshd_config.d/*
   sudo tee /etc/ssh/sshd_config.d/050-nexahome.conf >/dev/null <<EOF
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   PermitRootLogin no
   AuthenticationMethods publickey
   AllowUsers $MINI_USER
   MaxAuthTries 3
   AllowAgentForwarding no
   X11Forwarding no
   EOF
   sudo sshd -t                                 # expect: no output
   ```

5. Laptop: test both directions (next section).

## What you should see

| Step | Expect |
| :--- | :--- |
| 1 | Two files, `nexahome_mini` and `nexahome_mini.pub`. Never copy or print the first |
| 3 | "Number of key(s) added: 1" and a prompt for the **account** password, once |
| 4 | `Include` line found; `sshd -t` prints nothing. An error names the line to fix |
| 5 | The two tests below |

**Effective settings** (on the mini, as `<admin-user>`). The file content is not the proof; sshd's own answer is:

```sh
sudo sshd -T | grep -Ei 'passwordauth|kbdinteractive|permitroot|authenticationmethods|allowusers|maxauthtries|allowagent|x11forwarding'
```

Expect `passwordauthentication no`, `kbdinteractiveauthentication no`, `permitrootlogin no`, `authenticationmethods publickey`, `allowusers <daily-user>`, `maxauthtries 3`, `allowagentforwarding no`, `x11forwarding no`. Both password lines are needed: macOS enables PAM (`UsePAM yes` in its own drop-in), which can offer a password prompt through keyboard-interactive. Files in `sshd_config.d` are read first and the first value wins, so `050-` sorts before Apple's `100-macos.conf`. Not verified on the mini: file order and the `Include` line on the macOS version it ships with.

**Test from the laptop** (requirements P4-A1 and P4-A2):

```sh
ssh -i ~/.ssh/nexahome_mini -o IdentitiesOnly=yes "$MINI_USER@$MINI_HOST" true; echo $?   # expect: 0, no password prompt
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password "$MINI_USER@$MINI_HOST"   # expect: Permission denied (publickey)
```

## First connect: check the host key (P4-A4)

The first connection prints a fingerprint (`SHA256:...`). Before you type `yes`, compare it at the mini:

```sh
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

If they differ, answer no and stop: you are not talking to the mini.

## Laptop SSH config (local file, never committed)

Add to `~/.ssh/config`, then use `ssh <mini-alias>`:

```
Host <mini-alias>
    HostName <mini-host>.local
    User <daily-user>
    IdentityFile ~/.ssh/nexahome_mini
    IdentitiesOnly yes
    AddKeysToAgent yes
    UseKeychain yes
    ForwardAgent no
    ServerAliveInterval 30
    ExitOnForwardFailure yes
    StrictHostKeyChecking yes
```

`UseKeychain` is macOS only; on Linux delete that line. To reach a model server that listens on the mini's loopback, open a tunnel instead of a port: `ssh -N -L 11434:127.0.0.1:11434 <mini-alias>`, then use `127.0.0.1:11434` on the laptop.

## Finding the mini on Wi-Fi

Default: the Bonjour name `<mini-host>.local`. If it stops resolving, give the mini a fixed address with a DHCP reservation in the router and use that address as `HostName`. Neither is verified on this network.

## Tighten a key to your network

Once login works, prefix the key's line in `~/.ssh/authorized_keys` on the mini (as `<daily-user>`) with `from="<lan-cidr>" `, for example `from="<lan-cidr>" ssh-ed25519 AAAA... nexahome-<device>`. A copied key then fails from outside the home network. Test that key login still works from the laptop. Not verified: that the mini sees your laptop's address inside the range.

## Add a client, revoke a key, review

- **Add a client** (a third machine): run step 1 on it with its own `<device>` name, then step 3. One key per client; never copy a private key between machines.
- **Revoke a lost key:** at the desk (or through another client), open `~/.ssh/authorized_keys` on the mini and delete the line with that `<device>` comment. On the other clients nothing changes.
- **Review now and then:** `cat ~/.ssh/authorized_keys` on the mini: one line per client you still own, none you do not recognise. Recent attempts: `log show --predicate 'process == "sshd"' --last 1d` (not verified on the mini).

## Git access from the mini

The deploy checkout pulls with a read-only deploy key; the workspace checkout pushes with a per-device user key (passphrase, Keychain). Agent forwarding is off, so a compromised mini cannot use the laptop's keys. Set up in the bring-up sessions; [ADR 0015](../adr/0015-remote-access.md).

## Recovery

A wrong drop-in only affects remote login. Log in at the desk (or as `<admin-user>`), delete `/etc/ssh/sshd_config.d/050-nexahome.conf`, and if sshd still refuses, turn Remote Login off and on in System Settings. A rebooted mini waits for the disk password at the desk before SSH answers (FileVault).

## Evidence and limits

Not run on a mini. Rehearsal of 2026-11-02 on the laptop (macOS 27.0.1, OpenSSH 10.3, not the 26.x the mini will run), against a throwaway `sshd` started without `sudo` on a loopback port, with scratch keys and a scratch drop-in of the same lines, all deleted afterwards. Results: `sshd -t` clean; `sshd -T` showed every value in the list above and `allowtcpforwarding yes`; key login exited 0; the recorded host key equalled the server's fingerprint; the password attempt and a wrong key ended "Permission denied (publickey)"; a tunnel to a loopback web server answered 200; `ssh -A` left no agent socket on the server; a `from=` range that excluded the client refused a correct key (the server log said so). Findings: start such an `sshd` with an absolute path to its config (a relative path made every connection reset), and the exit code printed by `ssh ... | filter` is the filter's, so read the message, not `$?`. Not covered: PAM (`UsePAM no` in the scratch), `/etc/ssh/sshd_config.d` itself, Remote Login, Bonjour, VS Code Remote-SSH, the `log show` query. Not verified: everything on the mini.

Changelog: 0.1 (2026-11-02): initial draft, A1.
