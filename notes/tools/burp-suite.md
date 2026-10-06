# Burp Suite

| | |
|---|---|
| **Status** | 🟡 Explained to me, **never actually used**. Not learned until I run it. |
| **Category** | Web / Tooling |

> ⚠️ This page breaks the log's own rule slightly — it records an explanation, not something I
> did. It stays 🟡 until I've run Burp against a real target.

## The mental model

Burp is a **man-in-the-middle proxy pointed at yourself.**

```
Normal:     Browser ───────────► Server
With Burp:  Browser ─► BURP ─► Server
                       ▲ you sit here
```

Every request pauses where you can read, edit, replay, or drop it.

**Why it matters:** the browser hides headers, cookies, and hidden fields, and enforces
client-side rules (`maxlength`, dropdowns, disabled buttons) that the *server* may not enforce
at all. Burp shows the raw request and lets you send anything.

Client-side restrictions are suggestions. Burp is how you find out whether the server agrees.

## The tabs that matter

| Tab | Purpose | Usage |
|---|---|---|
| **Proxy → HTTP history** | Log of everything that passed through | Home base |
| **Repeater** | Edit one request, re-send unlimited times | The workhorse — ~80% of manual testing |
| **Proxy → Intercept** | Freeze requests mid-flight to edit before sending | Only when modifying in the browser flow |
| **Decoder** | base64 / URL / hex encode-decode | Cookies and tokens are often base64 |
| **Intruder** | Automate many request variations | ⚠️ Rate-limited to near-uselessness in Community edition |

## Setup — avoid the classic time sink

Use **Burp's built-in browser**: Proxy tab → Intercept → **Open Browser**. Pre-configured, no
CA certificate hassle.

The Firefox route (proxy to `127.0.0.1:8080` + import Burp's CA cert) is where people lose an
hour to certificate warnings.

## The workflow

1. **Turn Intercept OFF** — leaving it on makes every page hang forever. It isn't broken; it's
   waiting.
2. Browse the target normally to populate the log
3. Proxy → HTTP history → find the interesting request
4. Right-click → **Send to Repeater** (`Ctrl+R`)
5. Edit the raw request → Send → read response → change one thing → repeat

Step 5 is the entire skill. Everything before it is plumbing.

## Connection to what I already know

The [IDOR](../concepts/idor.md) win on Authentication Anywhere was hand-editing a URL. **Burp
is that same move, industrialised** — Repeater instead of the address bar, ten seconds per
attempt instead of a page reload.

Same bug class, better instrument.

## Not learned yet

- [ ] **Actually running it against a target** — everything above is theory
- [ ] Reading a raw HTTP request fluently
- [ ] Scoping (stopping Burp logging every unrelated request)
- [ ] When Intercept beats Repeater
- [ ] Match & replace rules
- [ ] Whether Community edition is enough or Pro is needed for real work

## Note (2026-10)

Burp is installed on this host (`burpsuite`). For CTF speed, `curl` and `ffuf` beat Burp on
anything scriptable — reach for Burp when the bug is in *logic* you need to see request by
request, not in a parameter you can fuzz.
