#!/usr/bin/env python3
"""picoCTF heartbleed — recover the secret from .rodata and hash it with djb2.

Two independent paths to the same secret:
  1. runtime leak via the buffer over-read (offset 60, 12 bytes)
  2. static: .rodata bytes XOR 0xAA
They agree, which is how we know it is right.
"""

OBF = bytes([0xC3, 0xFF, 0xC8, 0xC2, 0x92, 0x9B, 0x8B, 0xC0, 0x80, 0xC2, 0xC4, 0x8B])
XOR_KEY = 0xAA           # the -86 sitting at offset 72 of the leak
LEAKED = "iUbh81!j*hn!"  # what the over-read returned at offset 60
MASK64 = 0xFFFFFFFFFFFFFFFF


def make_secret(obf: bytes = OBF, key: int = XOR_KEY) -> str:
    """Reimplementation of the binary's make_secret()."""
    return "".join(chr(b ^ key) for b in obf)


def djb2(s: str) -> int:
    """The binary's hash() — fingerprinted by the constant 5381 and shl 5 + add.

    The mask is NOT optional: C computes this in an unsigned long, which wraps at
    2**64. Python ints are arbitrary precision, so without the mask a 12-char input
    gives 8980355282403002096610 instead of the real answer.
    """
    h = 5381
    for c in s:
        h = (h * 33 + ord(c)) & MASK64
    return h


def demo() -> None:
    secret = make_secret()
    assert secret == LEAKED, f"static {secret!r} != runtime leak {LEAKED!r}"
    assert djb2(secret) == 15237662580160011234, djb2(secret)
    assert djb2("") == 5381
    # unmasked arithmetic overflows at this length — the bug worth keeping a test for
    unmasked = 5381
    for c in secret:
        unmasked = unmasked * 33 + ord(c)
    assert unmasked != djb2(secret) and unmasked & MASK64 == djb2(secret)
    print(f"secret: {secret}")
    print(f"answer: {djb2(secret)}")
    print("submit -> Password: hi / Length: 100 / Hash: " + str(djb2(secret)))


if __name__ == "__main__":
    demo()
