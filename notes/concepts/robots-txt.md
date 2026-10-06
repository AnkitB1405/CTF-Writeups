# robots.txt

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | TryHackMe — Pickle Rick |
| **Category** | Web / Reconnaissance |

## What it is

A plain-text file at the web root (`/robots.txt`) that **asks** crawlers not to index certain
paths.

It is **advisory only**. Nothing enforces it. It is publicly readable by anyone, by design —
it has to be, or crawlers couldn't read it either.

## Why it's a recon target on every engagement

It is a **curated list of paths someone considered sensitive enough to mention.** The site
owner did the filtering work and published the results.

Asking crawlers to ignore something is not the same as hiding it. It's closer to a signpost
reading "nothing interesting down here."

## What it held on Pickle Rick

17 bytes. One string: `Wubbalubbadubdub` — the login password, in plaintext, in a public file.

The size in the dirb output (`SIZE:17`) was itself informative: 16 characters plus a newline
meant the file contained **nothing else**. It existed purely to hand over that string.

## Habit to keep

Check `/robots.txt` **before** running a directory scan. It's one request, it's free, and it
sometimes ends the recon phase outright.

## Not learned yet

- [ ] Other free-intel files worth hand-checking (`sitemap.xml`, `.git/`, `security.txt`, `.env`, `crossdomain.xml`)
- [ ] What a *correct* robots.txt looks like and how to keep secrets out of it
- [ ] Whether search engines have already archived a path listed here

**Seen in:** [THM — Pickle Rick](../../challenges/THM/pickle-rick/README.md)
