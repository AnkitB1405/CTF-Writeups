# THM — Authentication Anywhere

| Field | Value |
|---|---|
| **Event** | TryHackMe |
| **Category** | Web / Access Control |
| **Date** | 2026-08-30 |
| **Status** | ✅ Solved |
| **Vulnerability** | [IDOR](../../../notes/concepts/idor.md) |

## Challenge

A fake cloud login service — "Authentication Anywhere". The task prompt teased that other
users' profiles contain secrets.

**Objective:** find the flag on your neighbour's logged-in page.
Accessed via the THM AttackBox against the deployed target machine.

## TL;DR

The user identifier sat in a URL parameter with no server-side ownership check. Logged in as
`guest`, changed the ID to the neighbouring user, and the server handed over their page. One
edited URL — no password attack, no exploit code.

## What I tried — and why it failed

| Attempt | Outcome | Why it was wrong |
|---|---|---|
| `dirb` directory scan | Found `/db` → 403 not authorised | Not wrong, but I misread the 403 as a dead end instead of a confirmed target |
| `guest` / `guest` login | ✅ Worked | This was already the win — I didn't realise it |
| Read page source, saw a hint that **admin** was vulnerable | Noted | Correct clue, wrong interpretation |
| Tried to **crack the admin password** | 🔴 Total dead end | Read the hint as "break into admin" instead of "request admin's record" |

## What actually worked

The identifier was sitting in the **URL parameter**. Logged in as `guest`, changed the ID in
the address bar to the neighbouring user, and the server handed over their page without a
single authorisation check.

No password attack. No exploit code. One edited URL.

## Flag

*Not recorded.*

## Takeaways

1. **Read the room's own hints first.** The task page linked "similar content: IDOR". The
   vulnerability class was stated outright and I attacked in a different direction anyway.
2. **"Neighbor" is a technical hint,** not flavour text — it meant the target ID was adjacent
   to mine.
3. **A hint that "admin is vulnerable" is about *which record to request*,** not which password
   to break. Default to the access-control reading before the credential reading.
4. **403 ≠ dead end.** It confirms the resource exists and that access is identity-dependent.
   Revisit it after every identity change.
5. **Open DevTools → Network before navigating,** not after. Otherwise the request carrying the
   identifier is already gone.
