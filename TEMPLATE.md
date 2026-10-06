# <Challenge Name>

| Field | Value |
|---|---|
| **Event** | <Cryovault 2026 / picoCTF / HTB> |
| **Category** | <web / crypto / forensics / rev / pwn / osint / misc> |
| **Points** | <n> |
| **Difficulty** | <easy / medium / hard> |
| **Date** | <YYYY-MM-DD> |
| **Status** | <solved / unsolved / solved-after-event> |
| **Tools** | <ffuf, ghidra, pwntools> |

## Challenge

> Paste the challenge description verbatim here.

**Provided files:** `file1`, `file2`
**Target:** `nc host 1337` / `http://host:8080`

## TL;DR

One or two sentences — the bug and how it was exploited. Write this LAST but put it FIRST;
it's what you'll actually reread six months from now.

## Recon

What you ran first and what it told you. Include the commands, not just conclusions.

```bash
file chal
strings chal | grep -i flag
```

## Analysis

The reasoning that got you to the vulnerability. Show the relevant code or output —
decompiled C, the suspicious request, the broken crypto parameter. This is the section
that teaches you something later, so don't compress it into "then I noticed the bug".

## Exploitation

The working solve, start to finish. Keep the real script in `solve.py` next to this file
and reference it rather than pasting a stale copy.

```python
#!/usr/bin/env python3
from pwn import *
# ...
```

## Flag

```
flag{...}
```

## Takeaways

- The pattern worth recognising faster next time.
- What cost you time, and the thing you'd check earlier.
- Any tool flag or trick you learned.

## References

- <links, writeups, CVEs, papers>
