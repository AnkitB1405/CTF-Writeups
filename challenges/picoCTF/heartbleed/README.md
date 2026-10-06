# picoCTF — heartbleed

| Field | Value |
|---|---|
| **Event** | picoCTF — picoGym |
| **Category** | Binary Exploitation / Reverse Engineering |
| **Date** | 2026-09-12 |
| **Status** | ✅ Solved |
| **Vulnerabilities** | [Heartbleed — Buffer Over-Read](../../../notes/concepts/heartbleed-buffer-over-read.md) → [Static Binary Analysis](../../../notes/workflows/static-binary-analysis.md) |

## Challenge

A service asks for a password and, separately, how many bytes long it is. The two prompts are
never cross-checked. A binary (`system.out`) is provided.

## TL;DR

Declare a length far larger than the data written → the service returns 90 bytes of adjacent
struct memory, including a secret at offset 60. Then read the binary: `strtoul` proves the
answer is parsed as a **number**, and `hash()` is djb2. Feed the leaked secret through djb2 and
submit the integer.

## Structure

Two stages, sequential — neither one finishes it alone.

| Stage | What was needed | How it went |
|---|---|---|
| 1. Leak the secret | Buffer over-read | ✅ Solved unaided |
| 2. Turn the secret into the answer | Read the binary | ❌ ~90 min of black-box guessing first |

The secret is built at runtime by `make_secret()`, so it is not printed anywhere — stage 1 is
unavoidable. The hash function and the input type only exist in the code — stage 2 is
unavoidable.

## Stage 1 — the over-read

Two independent prompts, never cross-checked:

```
Please set a password:        -> 3 bytes written
How many bytes in length?     -> 100 declared
```

Memory came back as decimal ASCII:

```
offset  0 - 2    104 105 10        "hi\n"      <- mine
offset  3 - 59   zeros             57 bytes
offset 60 - 71   105 85 98 ...     the secret  <- iUbh81!j*hn!
offset 72        -86               0xAA
offset 73 - 89   zeros
```

Running it twice with different password lengths showed the secret **stayed at offset 60** — a
fixed field, not stack drift. Requesting 100 returned exactly 90 every time — the read is
clamped to the struct size, so 90 bytes was everything.

## Stage 2 — the dead ends

| Submitted | Result |
|---|---|
| Raw string `iUbh81!j*hn!` | Assertion fires immediately |
| Decimal bytes | Hangs — consumed as numbers, waiting for more |
| md5 / sha1 / sha256 | Never going to work |

The hint asked *"how does a hashing algorithm work?"* and it was read as *"which standard
digest?"* It meant **the mechanism**. That misreading cost the most time.

## Stage 3 — reading the binary

```bash
file system.out     # not stripped -> symbols survive
nm system.out       # hash, make_secret, main
nm -D system.out    # strtoul, atoi, fgets
```

`strtoul` settled it in one line: **input is parsed as a number**, so no hex digest could ever
match.

**`make_secret()`** — twelve bytes in `.rodata`, each XORed with `0xAA` at runtime:

```
c3 ff c8 c2 92 9b 8b c0 80 c2 c4 8b   XOR 0xAA  ->  iUbh81!j*hn!
```

Matched the runtime leak exactly — two independent methods agreeing.

**`hash()`** — djb2, identified by the constant `0x1505` (5381) and `shl 5` + `add` (×33).

**The comparison** — `strtoul(..., base 10)` against `make_secret()`'s return value.

## The answer

See [`solve.py`](solve.py).

```python
h = 5381
for c in "iUbh81!j*hn!":
    h = (h * 33 + ord(c)) & 0xFFFFFFFFFFFFFFFF   # C wraps at 2**64 — Python does not
# 15237662580160011234
```

> **Correction (2026-10-06):** the original note omitted the `& 0xFFFFFFFFFFFFFFFF`. Python
> integers are arbitrary precision, so unmasked this yields `8980355282403002096610` — the
> wrong answer. C computes djb2 in an `unsigned long`, which wraps. Caught by the assert in
> `solve.py`.

```
Password: hi
Length:   100
Hash:     15237662580160011234
```

## The 0xAA miss

The `-86` at offset 72 was written off as a padding/boundary marker. It was the **XOR key**. The
answer's key was sitting in the leaked dump the whole time.

**A byte that looks like filler may be a constant the program actually uses.**

## Local vs remote

Running `./system.out` locally printed a flag from a previous challenge — `strings` showed the
binary opens `flag.txt` from its **working directory**. Develop locally, run remotely.

## Takeaways

1. **Take the binary when one is offered.** Steps that took 30 seconds statically replaced 90
   minutes of guessing.
2. **"Hash" does not mean md5/sha.** It means any function mapping input to a fixed-size value.
   Custom ones are common.
3. **Check the imports before reading assembly.** `strtoul` alone eliminated every wrong theory.
4. **Negative bytes are signed readings.** Add 256.
5. **Failure modes are data.** Instant assert = parsed and rejected. Hang = still consuming
   input, wrong format.
6. **Cross-verify.** `.rodata` matching the runtime leak is how you know the value is right.
