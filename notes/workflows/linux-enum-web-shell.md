# Linux Enumeration from a Web Shell

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | TryHackMe — Pickle Rick |
| **Category** | Linux / Post-Exploitation |

## The three questions to ask first

Before wandering a filesystem, establish who and what you are:

| Command | Answers |
|---|---|
| `whoami` | Which account the web server runs as — usually `www-data` |
| `sudo -l` | What you may run as another user without a password → see [sudo Misconfiguration](../concepts/sudo-privesc.md) |
| `ls -la /home/` | Which human users exist |

Every later decision depends on these. "Look around the filesystem" without them is wandering.

## The stateless-shell problem

Each submission through a web command panel spawns a **fresh process**. State does not carry over.

So `cd /home` followed by `ls` in a separate request lists the **web root**, not `/home` — the
directory change died with the previous process.

Two workarounds:

| Approach | Example |
|---|---|
| Absolute paths always | `ls -la /home/rick/` |
| Chain within one request | `cd /home/rick && ls -la` |

The second works because both commands run inside the *same* shell invocation.

## Useful flags

| Flag | Effect |
|---|---|
| `-a` | Show dotfiles. A leading `.` hides a file from plain `ls` — cheap place to stash something |
| `-l` | Long format: permissions, owner, size |
| `-R` | Recurse into subdirectories |

So `ls -laR /home/` dumps the entire tree under `/home` in one request.

## Escalated enumeration

Once `sudo -l` shows you can escalate, re-run enumeration **as root** — directories that were
closed become readable:

```bash
sudo ls -laR /home/
sudo ls -la /root/
```

**Ordering matters:** the privilege wrapper goes **first**.

```bash
sudo tac /root/somefile     # ✅
tac sudo /root/somefile     # ❌
```

Any filter bypass still applies on top — `sudo tac`, not `sudo cat`, if `cat` is denylisted.
Escalating privileges does not bypass a web-app input filter; those are two separate layers.

## Searching by name

```bash
find / -name "*ingredient*" 2>/dev/null
```

`2>/dev/null` matters. Without it, `find` floods the output with permission-denied errors from
every directory the account can't enter. That redirect sends **stderr** to the void, leaving
only real hits.

Narrower and usually better:

```bash
find /home /root /opt /tmp -type f 2>/dev/null
```

## Where a planted file actually lives

| Location | Access as `www-data` |
|---|---|
| Web root (`/var/www/html`) | ✅ |
| `/home/<user>/` | Usually readable |
| `/root/` | ❌ Blocked — needs privilege |

## Filenames with spaces

`head second ingredients` parses as two arguments and fails with a confusing "no such file."
Quote it:

```bash
tac "/home/rick/second ingredients"
tac /home/rick/second\ ingredients
```

Quotes are easier to get right than escapes.

## Not learned yet

- [ ] Upgrading a web shell to an interactive reverse shell (fixes the stateless problem entirely)
- [ ] Automated enumeration scripts (LinPEAS, LinEnum) and what they check
- [ ] Reading `/etc/passwd` to enumerate users properly
- [ ] Locating credentials in config files, history files, and environment variables
- [ ] What all this enumeration looks like in logs from the defender's side

**Seen in:** [THM — Pickle Rick](../../challenges/THM/pickle-rick/README.md)
