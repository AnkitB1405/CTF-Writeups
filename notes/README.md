# Notes

Concept, workflow and tool notes — the knowledge base behind the
[challenge writeups](../challenges/).

**Rule for these pages:** nothing gets written here that I haven't hit in a real challenge. No
pre-loaded theory, no copy-pasted cheatsheets. If an entry looks thin, that's accurate — it
means I've used the thing but haven't understood it yet.

## Status legend

| Marker | Meaning |
|---|---|
| 🟢 | Understood by doing — I could explain it and find it again unaided |
| 🟡 | Used it, but don't understand it yet — treat the page as a stub |

## Concepts & vulnerabilities

| Term | What it is, in one line | Status | Note |
|---|---|---|---|
| **IDOR** | The app verifies you're logged in but never checks whether you're allowed to see *this particular record* — so you log in as anyone and request someone else's data | 🟢 | [idor.md](concepts/idor.md) |
| **Denylist bypass** | A filter that lists forbidden inputs always loses: the defender must think of every bad input, the attacker needs one that wasn't listed | 🟢 | [denylist-filter-bypass.md](concepts/denylist-filter-bypass.md) |
| **sudo privesc** | `sudo -l` reveals what you may run as another user; `(ALL) NOPASSWD: ALL` on a service account is unrestricted passwordless root | 🟢 | [sudo-privesc.md](concepts/sudo-privesc.md) |
| **robots.txt** | A public, unenforced file asking crawlers to skip paths — which makes it a curated list of what someone considered sensitive | 🟢 | [robots-txt.md](concepts/robots-txt.md) |
| **Heartbleed** | The program trusts an attacker-supplied length instead of measuring the data, and hands back whatever memory sat next to the input | 🟢 | [heartbleed-buffer-over-read.md](concepts/heartbleed-buffer-over-read.md) |

## Workflows

| Topic | What it covers | Status | Note |
|---|---|---|---|
| **Static binary analysis** | Reading a binary instead of guessing at its behaviour — `file`, `nm`, `strings`, `objdump` as a 30-second first pass | 🟢 | [static-binary-analysis.md](workflows/static-binary-analysis.md) |
| **Web-shell enumeration** | Establishing who you are and what you can reach on a box where every command runs in a fresh, stateless process | 🟢 | [linux-enum-web-shell.md](workflows/linux-enum-web-shell.md) |
| **LLDB / gdb on the compare** | Break on the comparison function and read both arguments — leak the password instead of guessing it | 🟡 | [lldb-breaking-on-comparison.md](workflows/lldb-breaking-on-comparison.md) |

## Tools

| Tool | What it does, in one line | Status | Note |
|---|---|---|---|
| **dirb** | Brute-forces web paths to reveal pages and endpoints that aren't linked anywhere on the site | 🟡 | [dirb.md](tools/dirb.md) |
| **Burp Suite** | A man-in-the-middle proxy pointed at yourself — pause, read, edit and replay every request the browser sends | 🟡 | [burp-suite.md](tools/burp-suite.md) |

For the full command reference across every category, see
[reference/CHEATSHEET.md](../reference/CHEATSHEET.md).
