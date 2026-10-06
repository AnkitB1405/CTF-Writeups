# IDOR — Insecure Direct Object Reference

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | TryHackMe — Authentication Anywhere |
| **Category** | Web / Access Control |

## One-line version

The app checks *whether you are logged in*, but forgets to check *whether you are allowed to
see this specific record* — so you log in as anyone and then just ask for someone else's data.

## The core idea

There are two separate checks a web app is supposed to do:

| Check | Question it asks | IDOR apps do this? |
|---|---|---|
| Authentication | Are you a valid user? | ✅ Yes |
| Authorisation | Are you allowed to access **this object**? | ❌ No — this is the bug |

The server sees a valid session, sees a request for object `id=1`, and hands it over without
ever asking "does this session own object 1?"

## The mistake I made first

I tried to **crack the admin password**. Completely the wrong direction.

IDOR has nothing to do with credentials. Any valid login is enough — in that room,
`guest`/`guest`. Once you're authenticated at all, the bug does the rest. If I catch myself
reaching for a password attack on a box hinting at IDOR, I've misread the challenge.

## Where the identifier hides

After logging in, hunt for the value that identifies *you*. Four places, in the order worth checking:

| # | Location | How to check | Looks like |
|---|---|---|---|
| 1 | **URL parameter** | Read the address bar | `?id=2`, `?user_id=3` |
| 2 | **Cookie** | DevTools → Application → Cookies | `user=guest`, `id=2` |
| 3 | **Hidden form field** | Ctrl+U on the logged-in page | `<input type="hidden" name="uid" value="2">` |
| 4 | **POST body / API call** | DevTools → Network tab, click around | `{"userId": 2}` |

In Authentication Anywhere it was **#1, the URL parameter**.

## Exploitation workflow

1. Log in with *any* working credentials.
2. Open DevTools → Network tab **before** navigating, so nothing is missed.
3. Locate the identifier tied to your session.
4. Change it. Try `1`, `0`, and your own ID ±1.
5. If it lives in a cookie, edit it in place (Application → Cookies → double-click value → refresh).
6. Re-request endpoints that previously refused you — they may have refused you *as that user*,
   not absolutely.

## What a 403 actually told me

`/db` returned *not authorised*. I read that as a dead end. It isn't:

- **403** = the resource **exists**, I'm just not permitted as this identity.
- **404** = not there.

A 403 is a confirmed target, not a wall. Worth re-hitting after any identity change.

## Not learned yet

- [ ] How to defend against IDOR properly (server-side ownership checks, indirect reference maps)
- [ ] Blind IDOR (no response body, side-effects only)
- [ ] IDOR on UUID / non-sequential identifiers
- [ ] IDOR in write operations (PUT/DELETE), not just reads
- [ ] Mass assignment — the related but distinct bug

**Seen in:** [THM — Authentication Anywhere](../../challenges/THM/authentication-anywhere/README.md)
