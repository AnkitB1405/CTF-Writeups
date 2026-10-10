# phantom

| | |
|---|---|
| **Event** | Cryovault 2026 (hackathon) |
| **Category** | rev |
| **Status** | 🔴 Fully reversed — the gate is unsatisfiable, proven against the live binary |
| **Flag** | no input can satisfy this binary (see below) |

## Challenge

> The source code is missing. All you have is the executable and a prompt for a flag.
> Follow the program's logic and reconstruct the input it expects.
>
> Files: `phantom` (Linux x86-64 executable)
> Flag format: `isfcr{...}`

## TL;DR

`phantom` is a static-pie stripped x86-64 ELF that reads a flag and prints ACCESS
GRANTED / DENIED. The gate is a bytecode VM. The VM is fully reversed and every
verifier in the binary inverted. The gate runs **two different** VM programs over the
same body and **ANDs** their verdicts; the two programs accept two *different* strings,
so `0xb220` can never return 1. Every one of the 257 embedded flag candidates is a
self-labelled taunt. The binary is a validator, not a flag printer, so there is no
input to recover — this needs raising with the organizers.

## The gate — corrected

`main` (0x9930) requires: length exactly 43, prefix `isfcr{`, `}` at offset 42, the
36-byte body drawn from `[a-z0-9_]`, then `0xb220(body)` must return non-zero.

`0xb220` derives two indices into the VM-program table at `0xb8190` from a fixed
rol/xor chain (`0x9bb0` is just `rol(edi, esi)`, so the chain is a compile-time
constant), then ANDs the two verdicts:

```
r14  = 0x54231e21                  # the rol/xor chain, no input dependence
idx0 = (r14 +  9) & 0xf = 10
idx1 = (r14 + 10) & 0xf = 11
return A[10](body) & A[11](body)   # 0xb30b: and al, bpl
```

**An earlier pass of this writeup claimed the gate used `A[0]` and `A[1]`. That was
wrong.** The first VM invocations you see when tracing are the 16 *decoy wrappers*
called from `0xc170` (which run programs 0, 1, 2, …), not the gate; the gate's own two
calls are the 18th and 19th. Breaking at the real call sites (`0xb2ee`, `0xb306`) shows
`rdi = 0x8bd80` and `0x8c250`, i.e. table entries **10 and 11**. Reproduce with
[`gate.py`](gate.py):

```console
$ ./gate.py --verify ./phantom
rol/xor chain -> r14 = 0x54231e21
gate runs VM program A[10] AND A[11]   (NOT A[0] and A[1])
  A[10] accepts exactly: isfcr{gr347_by73c0d3_w0rk_bu7_7h1s_1s_f4k3}
  A[11] accepts exactly: isfcr{gr347_by73c0d3_w0rk_4nd_7h1s_1s_f4k3}
verifying against the real binary:
  body accepted by program 10: RESULT idx0=10 idx1=11 result0=1 result1=0
  body accepted by program 11: RESULT idx0=10 idx1=11 result0=0 result1=1
```

The two bodies differ only at offsets 20–22 (`bu7` vs `4nd`). Each program accepts
*exactly one* body because:

- every opcode is invertible — the two multiply opcodes force an odd multiplier
  (`or r8b,0x1; mul r8b` at `0xa7e2`, same pattern in the vectorised `0x12` handler),
  so the 36-byte transform is a bijection;
- control flow and every derived operand come from the register file, which no opcode
  ever loads from the data buffer, so the trace is identical for every input (one
  `0x16` compare and one `0x17` halt per run, 766 steps, a 13-iteration loop);
- `op 0x16` is a full 36-byte equality — `0xb0c7` ORs all 36 byte differences and
  `sete`s the verdict (the compiler scatters the target across `rsp+0xa0`, xmm
  registers and `rsp+0x4`, but it is the single 36-byte buffer at `rsp+0x170`).

Two distinct unique-preimage predicates ANDed together. **ACCESS GRANTED is
unreachable.** That is measured, not inferred: `result0`/`result1` above come from the
real process.

## Also worth knowing: the binary builds a flag at runtime

Decoy wrapper `0xb500` uses the VM as a *transform* rather than a checker — the halt
handler writes the 36-byte result to the optional 4th argument (`0xb1c6`, when
`rcx != 0`). It assembles a flag in place and memcmps it against your input:

```
[rsp]      = "isfcr{"
[rsp+0x30] = '0' x 36                       # the constant at 0x842a0, twice, + "0000"
A[0]       : transform -> [rsp+6]           # program 0, 130 instrs, the generator
[rsp+0x2a] = '}'
memcmp(user_input, [rsp], 43)
```

It produces `isfcr{gr347_by73c0d3_w0rk_bu7_7h1s_1s_f4k3}` — the same taunt `A[10]`
wants, and the only program whose forward transform of the constant is even printable.
Its verdict is XORed into the dead accumulator at `0xbc9a4` like every other wrapper.

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

## Decoys, in full — 257 candidates, all taunts

- **230** plaintext `isfcr{...}` strings in the table at `0xb8210` (`0x730/8` entries).
  Only **8** even have a 36-char in-charset body, i.e. could pass `main`'s own checks —
  all 8 are taunts. The 231st plaintext `isfcr{` in the file is the bare prefix at
  `0x8439b`, not a flag.
- **11** obfuscated blobs decoded by the helper at `0xb3e0` (rol/xor stream keyed by a
  4-byte seed, tables at `0xb8940`/`0x8da60`) — the table ends after exactly 11 entries,
  and their lengths are 39–49, so most could never pass the length check anyway.
- **16** VM programs in the table at `0xb8190` — all 16 inverted, all taunts. Note the
  bodies the *gate* demands (`A[10]`, `A[11]`) are **not** in the 230-string table; they
  exist only as VM preimages.
- **16** wrapper "verifiers" at `0xb320`..`0xc0b0`, called from `0xc170` before the real
  check, whose verdicts are XORed into a global at `0xbc9a4`.

Full list: [all-decoys.txt](all-decoys.txt).

Things ruled out while looking for a real flag:

| Checked | Result |
|---|---|
| `0xbc9a4` accumulator | every read is inside the wrapper chain itself; nothing outside `0xb3xx`–`0xc3xx` reads it, `main` and `0xb220` never touch it |
| other global writes in custom code | only `0xbc9a4` and `0xbc9a0` (the latter is the standard atexit guard in the fini path) |
| unreachable code | nothing custom past `0xc3bd`; `0xc3c0`+ is glibc's fini walker and cpuid cacheinfo |
| constructors | `.init_array` holds stock glibc entries only |
| encoded flag prefixes | no `isfcr{` under any single-byte XOR/ADD, caesar, reversal or base64 alignment |
| unreferenced `.rodata` | the only large unreferenced runs are glibc's own tables and strings |
| header gaps in the 476-byte VM program header | offsets `0x10/0x14/0x18/0x1c/0x24` are all read by the setup; `0x20` is a constant tag (`e59c713a`) shared by all 16 |
| other sections | `.tdata`, `.data`, `rodata.cst32`, `.comment` are stock |
| external input | `strace` shows only the stdin read; no file, no env var, no network |
| cross-combinations | `T10^-1(tgt11)`, `T11^-1(tgt10)`, `tgt10^tgt11`, `T10(B)`, `T11(A)`, `T_i^-1('0'*36)` — none in charset |
| acrostics / orderings | first and last characters of the 230 bodies spell nothing |

## Conclusion

The binary never prints a flag — it only validates one, and its gate is a contradiction.
So "the input it expects" does not exist. Either the challenge is a deliberate no-flag
troll (the title *PHANTOM FLAGS* and 257 taunts support that reading), or the generator
picked the two gate programs independently and shipped a bug. Worth asking the
organizers which; nothing further is recoverable from the file.

If a single answer has to be submitted, the best-supported candidate is the body that
the gate's *exclusive* program accepts — `A[10]` is referenced by nothing but the gate,
while `A[11]` is reused by decoy wrapper `0xbce0`, and `A[10]`'s body is also what
program 0 accepts and what the runtime builder assembles:

```
isfcr{gr347_by73c0d3_w0rk_bu7_7h1s_1s_f4k3}
```

It is still a taunt, and it still prints ACCESS DENIED.

## Files

- `vm.py` — the VM emulator. **The S-box is the shuffled table the VM builds in its
  frame at `+0xae0`, not the key-material copy at `+0x9e0`;** using the wrong one makes
  op `0x14` diverge at the very first paired-S-box instruction and every inversion comes
  out as garbage.
- `solve.py` — records the trace and walks it backwards from the target.
- `gate.py` — derives the gate's real indices, states what each demands, and verifies
  both verdicts against the live process.
- `oracle.py` — gdb harness that pokes bytes past `main`'s charset filter.

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

**Trace the real call site, not the first call.** The decoy wrappers run the VM 17
times before the gate does. Dumping "the first two VM calls" gets you programs 0 and 1
and a confidently wrong answer. Break at the call sites inside the function you care
about (`0xb2ee`, `0xb306`).

**Recompute constant chains instead of eyeballing them.** `r14 = 0x54231e21` has low
nibble 1, which makes `(r14+9)&0xf` / `(r14+10)&0xf` look like "0 and 1" if you squint.
Six lines of Python, or one gdb breakpoint, gives 10 and 11.

**Locate decrypted structures by their invariants.** The S-box is the 256-byte run that
is a permutation of 0..255; the four position permutations are the 36-byte runs that
permute 0..35; the bytecode is the 752-byte run whose every 8th byte is a valid opcode.
That found the whole frame layout without reading the setup code — but two tables in
that frame are permutations of 0..255, and only one is the live S-box. Validate
step-by-step against the process rather than picking the first match.

**A GCM-style "which buffer is the target" question is answered by the compiler, not the
source.** `op 0x16`'s target looked like three unrelated operands (`rsp+0xa0`, xmm regs,
`rsp+0x4`) until a byte-level diff showed all three are slices of one 36-byte buffer.

**An "unsatisfiable" verdict needs a measurement, not a model.** The previous pass
reached the right conclusion from the wrong premises. Feeding each candidate back in and
reading `result0`/`result1` out of the live process is what makes the claim stand up.
