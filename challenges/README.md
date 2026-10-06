# Challenges

Per-challenge writeups. The point of these is **the failed path, not the flag** — the dead ends
are what stop me repeating them.

| Challenge | Platform | Category | Vulnerability | Status |
|---|---|---|---|---|
| [Authentication Anywhere](THM/authentication-anywhere/README.md) | TryHackMe | Web | IDOR | ✅ |
| [Pickle Rick](THM/pickle-rick/README.md) | TryHackMe | Web → Linux | Denylist bypass → sudo privesc | 🟡 1/3 |
| [heartbleed](picoCTF/heartbleed/README.md) | picoCTF | Pwn / RE | Buffer over-read → RE | ✅ |

## Layout

```
challenges/
  Cryovault-2026/     the hackathon — web/ crypto/ forensics/ rev/ pwn/ osint/ misc/
  THM/                TryHackMe
  picoCTF/
  HTB/
  other/
```

Scaffold a new one with [`bin/newchal`](../bin/newchal):

```bash
./bin/newchal Cryovault-2026/pwn stack-smash
```
