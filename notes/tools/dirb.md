# dirb

| | |
|---|---|
| **Status** | 🟡 Partly understood — core flag learned on Pickle Rick, most of the tool still unknown |
| **First hit** | TryHackMe — Authentication Anywhere |
| **Also used** | TryHackMe — Pickle Rick |
| **Category** | Web / Reconnaissance |

## What I know so far

`dirb` is a **web content / directory brute-forcer**. It throws candidate paths at a web server
and reports which ones respond, revealing pages and endpoints that aren't linked anywhere on
the site.

## What it actually gave me

Ran it against the target and got back a list of paths. Nearly all of it was noise. The one
useful hit:

| Path | Response | What I concluded |
|---|---|---|
| `/db` | Not authorised (403) | Endpoint exists, I'm just not permitted **as this identity** |

That 403 was the actual value of the whole scan — a confirmed, named, access-controlled
endpoint to come back to after changing identity.

## The one real lesson

Dirb's output is **a list of doors, not a list of answers.** The tool tells you what exists.
Deciding which of those doors matters, and what a given response code means, is entirely manual.

## 🔑 `-X` — extensions (learned on Pickle Rick)

**The default wordlist tests bare words with no file extension.** It requests `/login`,
`/admin`, `/portal` — never `/login.php`.

On Pickle Rick this made the first scan look like a dead end: it returned `index.html`,
`robots.txt`, `/assets/`, and a 403 — and **no login page at all**, even though `login.php` and
`portal.php` were sitting right there.

```bash
dirb http://TARGET/ -X .php,.html
```

`-X` appends each extension to every word in the list. Same wordlist, roughly 3× the requests,
and now it asks for filenames that can actually exist.

**The habit:** match the extension list to the target's stack. Apache serving `.html` and
needing server-side auth → the interesting files are `.php`. A scan without extensions on a PHP
box is asking for filenames that cannot exist.

## Reading response codes

| Code | Meaning | Worth chasing? |
|---|---|---|
| 200 | Exists and served | Yes |
| 403 | Exists, access denied **for this identity** | Yes — confirmed target, not a wall |
| 404 | Not there | No |

Also seen: `DIRECTORY IS LISTABLE` — directory browsing is enabled, open it in a browser rather
than scanning it.

`/server-status` returning 403 confirms **Apache** with `mod_status`, normally restricted to
localhost.

## Not learned yet

- [ ] Which wordlist it used by default, and how to pick a better one
- [x] Its flags — `-X` for extensions ✅ (recursion, status-code filtering, threads still unknown)
- [ ] How to filter out the noise so real hits aren't buried
- [ ] How it differs from **gobuster** and **feroxbuster**, and when to reach for each
- [x] What the common response codes imply (200 / 403 / 404) ✅ — 301 / 401 still unclear
- [ ] Whether dirb is still the right default in 2026 or a legacy habit

## Successor note (2026-10)

The last checkbox is now answered: **dirb is a legacy habit.** This host has `ffuf` and
`gobuster`, both faster and with real filtering. The dirb `-X .php,.html` lesson maps directly:

```bash
ffuf -u http://TARGET/FUZZ -w WORDLIST -e .php,.html   # -e is dirb's -X
gobuster dir -u http://TARGET -w WORDLIST -x php,html  # -x is dirb's -X
```

ffuf also fixes the noise problem dirb couldn't: `-fs <size>` filters by response size, `-mc`
by status code. See [the cheatsheet](../../reference/CHEATSHEET.md).
