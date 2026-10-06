# Denylist Filter Bypass

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | TryHackMe — Pickle Rick |
| **Category** | Web / Input Filtering |

## The idea

A **denylist** (blocklist) tries to secure an input by enumerating everything that is
*forbidden*. Its opposite, an **allowlist**, enumerates everything *permitted* and rejects
the rest.

Denylists lose. Structurally, not occasionally:

> The defender must think of **every** dangerous input. The attacker needs **one** that
> wasn't listed.

## How it showed up

A web "Command Panel" executed OS commands but refused any input containing `cat`. Later
testing showed `head` was blocked too — so this wasn't a lazy one-word filter, someone sat
down and listed read commands.

It still failed. `tac` went straight through.

| Blocked | Worked |
|---|---|
| `cat` | `tac` |
| `head` | |

**Effort didn't save the denylist.** Completeness was never achievable, because Unix has a
dozen-plus ways to print a file.

## Ways to read a file that aren't `cat`

| Command | Note |
|---|---|
| `tac` | `cat` reversed — prints **last line first**. Fine for one-line files; scrambles multi-line ones |
| `head` / `tail` | First/last N lines |
| `nl` | With line numbers |
| `grep . file` | Matches every non-empty line → prints the file |
| `awk '{print}' file` | Explicit print |
| `sed -n 'p' file` | Same idea |
| `strings` | Printable text only |
| `xxd` / `od -c` | Hex dump |
| `base64 file` | Encode, decode locally — useful when output gets mangled |

## The transferable point (blue team)

This is why **command-name-based detection is worthless**.

A SIEM rule alerting on `cat /etc/shadow` is bypassed by `head`, `nl`, `awk`, or `tac`. The
attacker changed *spelling*, not *behaviour*.

Detection that survives is behavioural:

- A web server process reading sensitive files
- Unexpected process lineage (`apache2` → shell)
- Anomalous file-access patterns

Same lesson as the filter itself: enumerate what's *normal*, not what's *bad*.

## Not learned yet

- [ ] Bypassing filters via quoting/concatenation (`c""at`, `c$@at`, `ca\t`)
- [ ] Encoding-based bypass (base64 → decode → pipe to shell)
- [ ] Wildcard tricks (`/bin/c?t`)
- [ ] What a *correct* allowlist implementation looks like
- [ ] Where real command injection differs from this (here, execution was intended by design)

**Seen in:** [THM — Pickle Rick](../../challenges/THM/pickle-rick/README.md)
