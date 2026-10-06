<div align="center">

# 🚩 CTF Writeups

**Notes and writeups from my Capture The Flag work.**

Concepts I've actually hit in a challenge, workflows that paid off, and the dead ends that
cost me the most time.

![Platform](https://img.shields.io/badge/platform-Kali_Linux-557C94?logo=kalilinux&logoColor=white)
![Focus](https://img.shields.io/badge/focus-web_·_crypto_·_forensics_·_rev_·_pwn-blue)
![Writeups](https://img.shields.io/badge/writeups-3-green)
![Notes](https://img.shields.io/badge/notes-10-orange)

</div>

---

## What this is

A working notebook, not a tutorial series. Two kinds of page live here:

- **[Notes](notes/)** — one page per concept, workflow or tool. Written the first time I hit the
  thing in a real challenge, and marked 🟢 or 🟡 depending on whether I actually understand it yet.
- **[Challenges](challenges/)** — one page per box or challenge, recording what I tried, what
  failed, and why.

**The rule for the notes:** nothing goes in that I haven't hit in a real challenge. No
pre-loaded theory, no copy-pasted cheatsheets. If a page looks thin, that's accurate — it means
I've used the thing but haven't understood it yet. Every note ends with an honest
**"Not learned yet"** checklist.

**The rule for the writeups:** the failed path matters more than the flag. A clean solution
teaches nothing six months later; the reason I spent 90 minutes on the wrong theory does.

---

## Repository layout

```
.
├── notes/                    the knowledge base
│   ├── concepts/             vulnerability classes — IDOR, denylist bypass, privesc, Heartbleed
│   ├── workflows/            repeatable methods — static analysis, web-shell enum, debugger use
│   └── tools/                per-tool notes — dirb, Burp
│
├── challenges/               per-challenge writeups
│   ├── Cryovault-2026/       the hackathon · web crypto forensics rev pwn osint misc
│   ├── THM/                  TryHackMe
│   ├── picoCTF/
│   ├── HTB/
│   └── other/
│
├── reference/
│   ├── CHEATSHEET.md         full command reference, every category
│   └── TOOLCHAIN.md          my environment and what's installed
│
├── TEMPLATE.md               the standard writeup format
└── bin/newchal               scaffolds a new challenge directory
```

---

## Start here

| If you want… | Go to |
|---|---|
| The command reference | [reference/CHEATSHEET.md](reference/CHEATSHEET.md) |
| A vulnerability explained | [notes/](notes/) |
| A worked challenge | [challenges/](challenges/) |
| The biggest lesson in the repo | [Pickle Rick — confirmation bias](challenges/THM/pickle-rick/README.md#-the-biggest-mistake--and-it-wasnt-technical) |

---

## Writeups

| Challenge | Platform | Category | Vulnerability | Status |
|---|---|---|---|---|
| [Authentication Anywhere](challenges/THM/authentication-anywhere/README.md) | TryHackMe | Web | IDOR | ✅ |
| [Pickle Rick](challenges/THM/pickle-rick/README.md) | TryHackMe | Web → Linux | Denylist bypass → sudo privesc | 🟡 1/3 |
| [heartbleed](challenges/picoCTF/heartbleed/README.md) | picoCTF | Pwn / RE | Buffer over-read → RE | ✅ |

## Notes

**Concepts** ·
[IDOR](notes/concepts/idor.md) 🟢 ·
[Denylist bypass](notes/concepts/denylist-filter-bypass.md) 🟢 ·
[sudo privesc](notes/concepts/sudo-privesc.md) 🟢 ·
[robots.txt](notes/concepts/robots-txt.md) 🟢 ·
[Heartbleed](notes/concepts/heartbleed-buffer-over-read.md) 🟢

**Workflows** ·
[Static binary analysis](notes/workflows/static-binary-analysis.md) 🟢 ·
[Web-shell enumeration](notes/workflows/linux-enum-web-shell.md) 🟢 ·
[Debugger on the compare](notes/workflows/lldb-breaking-on-comparison.md) 🟡

**Tools** ·
[dirb](notes/tools/dirb.md) 🟡 ·
[Burp Suite](notes/tools/burp-suite.md) 🟡

🟢 understood by doing · 🟡 used it, don't understand it yet

---

## Conventions

Kept deliberately boring so the repo stays searchable a year from now.

- **Every writeup is a `README.md`** inside its own challenge directory, so GitHub renders it
  when you click the folder.
- **Copy [`TEMPLATE.md`](TEMPLATE.md)** rather than freehanding the structure.
- **TL;DR first, written last.** It's the part I actually reread.
- **Solve scripts stay separate and runnable** (`solve.py`), referenced from the writeup rather
  than pasted inline where they go stale.
- **Unsolved challenges still get a page.** `Status: unsolved` plus the reasoning beats no file.
- **Challenge binaries and pcaps are gitignored** — large, and often not mine to redistribute.
  The writeup and the solve are the artifacts worth keeping.

### Adding a challenge

```bash
./bin/newchal Cryovault-2026/pwn stack-smash
```

Creates the directory, copies the template with the title filled in, and stubs an executable
`solve.py`.

---

<div align="center">
<sub>Flags are redacted or omitted where a platform asks for that. Nothing here is a working
exploit against anything but a deliberately vulnerable practice target.</sub>
</div>
