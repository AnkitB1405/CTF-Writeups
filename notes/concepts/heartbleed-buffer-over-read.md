# Heartbleed — Buffer Over-Read

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | picoCTF — heartbleed (candy-mountain) |
| **Category** | Memory Safety |

## Full form

**CVE-2014-0160** — the OpenSSL heartbeat over-read. "Heartbleed" is the nickname.

## One-line version

The server trusted an attacker-supplied **length** instead of measuring the actual data, and
echoed back whatever memory happened to sit next to the input.

## The mechanism

TLS has a heartbeat: send a message plus a claim about its length, and the server echoes it back.

```
Send: "bird" + length 4     -> returns "bird"
Send: "bird" + length 500   -> returns "bird" + 496 bytes of adjacent memory
```

That adjacent memory held session cookies, private keys, passwords — whatever the process had
recently touched.

## Over-read vs overflow

| Aspect | Buffer **over-read** | Buffer **overflow** |
|---|---|---|
| Direction | Reading past the end | Writing past the end |
| Damage | Information disclosure | Memory corruption, often code execution |
| Crash | Usually silent | Often crashes |

Heartbleed is an over-read. **Nothing is corrupted** — which is exactly why it was so hard to
detect.

## Root cause

A trust boundary failure: an attacker-controlled length was used to size a read operation
**without validating it against the real buffer size**. The fix is one comparison.

## How it looked in the challenge

```
Please set a password:        <- data
How many bytes in length?     <- length, INDEPENDENT of the data
```

Wrote 3 bytes, declared 100, got back 90 bytes of struct — including a secret at offset 60
that was never mine to read.

## Reading a leaked dump

**Decimal ASCII.** Output arrives as numbers, not text. `105 85 98 104` becomes `iUbh`.

```bash
python3 -c "print(''.join(chr(int(x)) for x in input().split() if 32<=int(x)<127))"
```

**Negative bytes.** A byte holds 0–255, but C can read it signed (−128 to +127).

| Reading | Value |
|---|---|
| Unsigned | 170 = 0xAA |
| Signed | −86 |

Any negative number in a byte dump: **add 256**. It is not corrupted data, it is a signed
reading of the same byte.

> I dismissed that `-86` as a padding marker. It was the **XOR key** used to build the secret.
> A byte that looks like filler may be a constant the program actually uses.

## Probing technique

1. Write a **short** input — the smaller your data, the more of the leak is someone else's
2. Declare a much larger length
3. **Vary your input length across runs.** If the target stays at the same offset, it is a
   fixed field, not stack drift
4. **Watch for a cap.** Requesting 100 and receiving 90 every time means the read is clamped to
   the struct size — you already have everything

## Why it was catastrophic in the real world

It left **no logs**. A heartbeat request is normal traffic. The over-read happened inside
OpenSSL: no crash, no error, no application-level record. Servers bled memory for two years
and afterwards could not tell whether they had been hit, let alone what leaked.

Detection had to move to the network layer — inspecting heartbeat requests for length
mismatches — because the host had nothing to say.

## Not learned yet

- [ ] The actual OpenSSL patch and what the check looks like
- [ ] Writing a Heartbleed detection rule (Snort/Suricata/Zeek)
- [ ] Other over-read classes: off-by-one, `strncpy` without termination, format strings
- [ ] Why the memory was not zeroed — OpenSSL's custom allocator and freelist reuse
- [ ] Reading a real packet capture of a heartbeat exchange

**Seen in:** [picoCTF — heartbleed](../../challenges/picoCTF/heartbleed/README.md)
