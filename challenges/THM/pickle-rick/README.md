# THM — Pickle Rick

| Field | Value |
|---|---|
| **Event** | TryHackMe |
| **Category** | Web → Linux Privilege Escalation |
| **Date** | 2026-08-30 |
| **Status** | ✅ Solved — all 3 ingredients |
| **Vulnerabilities** | [Denylist Filter Bypass](../../../notes/concepts/denylist-filter-bypass.md) → [sudo Misconfiguration](../../../notes/concepts/sudo-privesc.md) |

## Challenge

A Rick and Morty themed box. Find three ingredients scattered across the host, starting from a
web app with a command panel.

## TL;DR

Credentials in an HTML comment and `robots.txt` → login to a command panel → `cat` was
denylisted but `tac` wasn't → `sudo -l` showed `(ALL) NOPASSWD: ALL` for `www-data`, which is
unrestricted passwordless root, and root access gave up the remaining two ingredients.

## 🔴 The biggest mistake — and it wasn't technical

The landing page contained `*BURRRP*` and `*BURRRRRRRRP*`. **I read those as hints pointing to
Burp Suite** and spent a full detour asking how to use a tool the room never wanted.

They were **belches.** Rick Sanchez's verbal tic. Stage directions for a bodily function.

What I missed: the page was saturated with Rick and Morty references — Morty, the pickle, the
potion, "Listen Morty..." — and I read one word in that context as a security tool, because
Burp was the thing I'd most recently learned about.

**That's confirmation bias.** I had a hypothesis, the evidence looked like it fit, and I never
asked what else `BURRRP` could mean. This is the exact failure mode that makes bad incident
responders: latching onto the first plausible explanation and stopping.

> **Rule going forward:** before acting on a hint, ask *what else could this mean* — and check
> whether the surrounding context supports my reading or contradicts it.

## The chain

| # | Step | How |
|---|---|---|
| 1 | Username `R1ckRul3s` | HTML source comment on the landing page |
| 2 | Password `Wubbalubbadubdub` | [`/robots.txt`](../../../notes/concepts/robots-txt.md) — 17 bytes, nothing else in it |
| 3 | Found `login.php` / `portal.php` | [dirb](../../../notes/tools/dirb.md) **with `-X .php`** — see below |
| 4 | Logged into the Command Panel | Credentials from steps 1–2 |
| 5 | Ingredient 1 | `ls` → filename visible → read with `tac` (`cat` and `head` both filtered) |
| 6 | `whoami` → `www-data` | Unprivileged service account |
| 7 | `sudo -l` → `(ALL) NOPASSWD: ALL` | **Full passwordless root.** Game over |
| 8 | Ingredients 2 & 3 | ✅ Read as root — `sudo ls -laR /home/`, `sudo ls -la /root/`, then `sudo tac <path>` |

## 🔧 The dirb lesson — why the first scan missed the login page

My initial scan returned only `index.html`, `robots.txt`, `/assets/`, and a 403 on
`/server-status`. **No login page at all.**

**Dirb's default wordlist tests bare words with no file extension.** It requested `/login`,
`/admin`, `/portal` — never `/login.php`.

The target ran Apache and served `index.html`. A login form needs server-side processing, so it
was always going to be `.php`. Every candidate path in that first scan was tested in a form that
couldn't exist on the box.

```bash
dirb http://TARGET/ -X .php,.html
```

`-X` appends each extension to every word in the list. Same wordlist, ~3× the requests, and now
it asks for filenames that can actually exist.

## 🔒 The filter lesson

`cat` was blocked. So was `head`. **`tac` worked.**

Someone deliberately sat down and listed read commands — and still lost, because Unix has a
dozen ways to print a file. Effort doesn't save a denylist; completeness was never achievable.

→ Full note: [Denylist Filter Bypass](../../../notes/concepts/denylist-filter-bypass.md)

## ⬆️ The privilege escalation

`(ALL) NOPASSWD: ALL` for `www-data`. No exploit, no kernel bug, no binary abuse — one
misconfigured line in `/etc/sudoers`.

The DFIR half: this escalation leaves **no malware artifact**. Just legitimate `sudo` calls by
an account entitled to make them. Detection has to be behavioural — a web service account
invoking `sudo` at all is the anomaly.

→ Full note: [Privilege Escalation — sudo Misconfiguration](../../../notes/concepts/sudo-privesc.md)

## Finishing it as root

With `(ALL) NOPASSWD: ALL` confirmed, the remaining two ingredients were a matter of
re-running enumeration with the privilege wrapper in front:

```bash
sudo ls -laR /home/          # every user's home tree, dotfiles included
sudo ls -la /root/           # normally closed to www-data — the point of escalating
sudo tac "<path to file>"    # sudo FIRST, and tac because cat is still filtered
```

Two things that matter here and bite people:

- **Absolute paths.** `cd` does not persist between submissions — each one is a fresh process.
- **The privilege wrapper goes first.** `sudo tac file`, never `tac sudo file`. And escalating
  does not bypass the web app's input filter: those are separate layers, so it stays `sudo tac`,
  not `sudo cat`.

See [Linux Enumeration from a Web Shell](../../../notes/workflows/linux-enum-web-shell.md).

## Takeaways

1. **Check the context before trusting a keyword match.** The `BURRRP` misread is the most
   valuable thing in this room.
2. **`robots.txt` before any scan.** One request, sometimes ends recon outright.
3. **Match your wordlist to the target's stack.** No extensions = no `.php` files found.
4. **`sudo -l` early, always.** One non-destructive command that frequently ends the engagement.
5. **A blocked command name is not a blocked capability.** Spell it differently.
