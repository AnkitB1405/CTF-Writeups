# Privilege Escalation — sudo Misconfiguration

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | TryHackMe — Pickle Rick |
| **Category** | Linux / Privilege Escalation |

## The command

```bash
sudo -l
```

Lists what the current user may run via `sudo`, **and as whom**. Non-destructive, one command,
no password needed to *ask*.

Run this first on any Linux box. Most beginners spend an hour on kernel exploits before
checking whether the front door was open.

## Reading the output

The line found on Pickle Rick, as `www-data`:

```
(ALL) NOPASSWD: ALL
```

| Fragment | Meaning |
|---|---|
| `(ALL)` | May run as **any user**, root included |
| `NOPASSWD` | No password prompt — the only reason this is usable from a web shell, where there's no TTY to type into |
| `ALL` | **Any command.** Not a whitelist of binaries |

That is complete, unrestricted, passwordless root for an unprivileged service account. No
exploit required — just prefix commands with `sudo`.

## Why `NOPASSWD` specifically matters

From a web shell you have **no interactive terminal**. A normal `sudo` entry would prompt for
a password and hang or fail. `NOPASSWD` removes the only thing standing between a web
compromise and root.

## Why this isn't just a CTF-ism

`NOPASSWD: ALL` on a service account appears in real environments constantly. The usual
origin: a developer needed one command during setup, granted blanket sudo as a shortcut,
never walked it back.

## DFIR angle

- **`/etc/sudoers` and `/etc/sudoers.d/` are evidence.** An over-permissive entry explains how
  an attacker went web-shell → root with *no exploit artifact to find*.
- **This escalation is nearly invisible.** No crash, no dropped binary, no kernel exploit
  signature. Just legitimate `sudo` calls by an account entitled to make them. Malware hunting
  misses it entirely.
- **The detection that works is behavioural:** `www-data` invoking `sudo` **at all** is
  anomalous. Web service accounts have no legitimate reason to escalate. That's a rule worth
  writing.

## Not learned yet

- [ ] Restricted sudo entries — escalating when only *specific* binaries are allowed (GTFOBins)
- [ ] SUID/SGID binary enumeration (`find / -perm -4000`)
- [ ] Capabilities-based escalation (`getcap`)
- [ ] Cron job and writable-script escalation
- [ ] Reading `/etc/sudoers` safely and what the syntax fields actually are
- [ ] What the sudo logs look like from the defender's side

**Seen in:** [THM — Pickle Rick](../../challenges/THM/pickle-rick/README.md)
