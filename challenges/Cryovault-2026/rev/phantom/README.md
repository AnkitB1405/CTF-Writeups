# phantom

| | |
|---|---|
| **Event** | Cryovault 2026 |
| **Category** | rev |
| **Status** | 🔴 Reversed completely — binary contains no real flag |
| **Flag** | not in this binary (see below) |

## TL;DR

`phantom` is a static-pie stripped x86-64 ELF that reads a flag and prints ACCESS
GRANTED / DENIED. The gate is a bytecode VM. I fully reversed the VM, inverted the
transform and recovered the accepted input for **every** verifier in the binary.
All 258 of them are taunts, and **the gate is mathematically unsatisfiable** — so
ACCESS GRANTED is unreachable. The real flag is not in the file.

## The gate

`main` (0x9930) requires: length exactly 43, prefix `isfcr{`, `}` at offset 42, the
36-byte body drawn from `[a-z0-9_]`, then `0xb220(body)` must return 1.

`0xb220` derives two table indices from a fixed rol/xor chain (always 0 and 1),
runs VM program `A[0]` then `A[1]` over the same body, and returns
**`result0 AND result1`**.

Each VM program is a composition of invertible byte operations, so each accepts
exactly one 36-byte string:

- `A[0]` → `gr347_by73c0d3_w0rk_bu7_7h1s_1s_f4k3`
- `A[1]` → `n1c3_vm_3mul470r_f4k3_fl4g_7ry_4g41n`

Two different strings ANDed together. Unsatisfiable. Verified against the real
binary: feed either one and it still prints ACCESS DENIED.

## The VM

Program header (476 bytes) then n×8 bytes of encrypted bytecode:

| offset | meaning |
|---|---|
| 0x00, 0x04 | magic `0xd16a7b93`, `0x4e82c5f1` |
| 0x08 | total size, must equal `0x1dc + 8*n_instr` |
| 0x0c | instruction count (1..256) |
| 0x0e, 0x0f | 36 (input length), 24 (opcode count) |
| 0x14 | seed for the keystream and the S-box shuffle |
| 0x1c | checksum over derived dispatcher values |
| 0x28 | 36-byte encrypted expected output |
| 0x4c | 400 bytes of key material → 256-byte S-box + 4×36-byte permutations |

An instruction is `{u8 op, u8 a, u8 b, u8 c, u32 imm}`. The dispatcher at 0xa5e5
derives the real operands — and crucially **none of them depend on the input**:

```
i    = (R0 + 3*R1 + a) % 36          # 64-bit before the mod: masking to 32 shifts it by -4
j    = (R0 + 3*R1 + b) % 36          # bumped by 1 if it collides with i
rot  = ((R1 + c) % 7) + 1
k32  = 17*R0 + R1 + R2 + imm
```

That is the whole break. Control flow and every operand are input-independent, so
the 36-byte transform is a **fixed** composition of invertible byte operations:
record the trace once with any dummy input, then walk it backwards from the
expected output. No brute force, no solver.

24 opcodes: register/stack/branch (0x00–0x06), per-byte xor/add/rotate/odd-multiply
/S-box (0x07–0x0a, 0x0e, 0x12), byte swap and two-operand mixes (0x0b–0x0d),
position permutation (0x0f), a 36-byte mixing round (0x10), per-group-of-6
rotation (0x11), full reverse (0x13), paired S-box (0x14), CBC-style chain (0x15),
compare (0x16), halt (0x17).

## Decoys, in full

- **231** plaintext `isfcr{...}` strings in `.rodata` — tested every one, all denied
- **11** obfuscated blobs decoded by the helper at `0xb3e0` (rol/xor stream keyed by
  a 4-byte seed) — all taunts
- **16** VM programs in the table at `0xb8190` — inverted all 16, all taunts
- **16** wrapper "verifiers" at `0xb320`..`0xc0b0`, called from `0xc170` before the
  real check, whose results are XORed into a global at `0xbc9a4` that nothing reads

Full list: [all-decoys.txt](all-decoys.txt).

## Files

- `vm.py` — the VM emulator. Validated byte-exact against the real binary on 5
  inputs for both live programs.
- `solve.py` — records the trace and walks it backwards from the target.
- `oracle.py` — gdb harness that pokes arbitrary bytes past `main`'s charset filter
  and reads the VM's transform output. This is what proved the emulator correct.

## Method notes worth keeping

**Try the cheap thing first.** Before reversing anything I fed all 231 stored
strings to the binary (3 seconds). Worth it even though it missed.

**A validated emulator beats a confident one.** The oracle harness breaks at the
VM entry, overwrites the input buffer *after* `main`'s charset check, and dumps the
transform result at the compare instruction. Diffing that against my emulator
step-by-step found two real bugs:

1. op 0x15's loop re-enters at `0xab57`, which means the carry is rotated **once per
   iteration**, not just before the first one.
2. `i` and `j` are computed in 64-bit registers. Masking `R0 + 3*R1` to 32 bits
   shifts every index by -4 per wrap, and `3*R1` wraps twice for large `R1`.

Both only show up after step 15 — a single end-to-end output check would have
caught #1 but not necessarily #2.

**Patch the argument, not the binary.** To dump the other 14 unused VM programs I
broke at the VM entry and overwrote `rdi`/`rsi` with another table entry. No
patching, no rebuild.

## Still needed

The flag is not in this file. The taunts point outward —
`n0p3_7h1s_w4s_n07_7h3_l1v3_74rg37`, `wr0ng_fl4g_7h3_s3rv3r_1s_n07_c0nfus3d`,
`n0p3_7h3_4nsw3r_1s_3ls3wh3r3` — so either there is a remote service for this
challenge or the handout is paired with something else. Need the challenge text.
