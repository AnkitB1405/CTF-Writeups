# Static Binary Analysis — First-Pass Workflow

| | |
|---|---|
| **Status** | 🟢 Understood by doing |
| **First hit** | picoCTF — heartbleed (candy-mountain) |
| **Category** | Reverse Engineering |

## The rule

**If a binary is offered, take it and read it before guessing at behaviour.**

Static analysis answered in under a minute what ninety minutes of black-box interaction could not.

## The workflow

| # | Command | What it tells you |
|---|---|---|
| 1 | `file binary` | Architecture, PIE, **stripped or not** |
| 2 | `nm binary` | Function names — only if not stripped |
| 3 | `nm -D binary` | Imported libc calls → what the program *does* |
| 4 | `strings -n 4 binary` | Prompts, filenames, error messages |
| 5 | `objdump -d -M intel binary` | The actual logic |
| 6 | `objdump -s -j .rodata binary` | Hardcoded constants and obfuscated data |

Steps 1–3 take thirty seconds and often decide the challenge.

## Step 1 — `not stripped` is the phrase to look for

```
ELF 64-bit LSB pie executable, x86-64, ..., not stripped
```

**Not stripped** = the symbol table survived = function names are readable. A stripped binary
gives you `sub_1309` instead of `hash`, and the work gets much harder.

## Step 3 — imports reveal intent

The single highest-value observation came from one line:

```
U strtoul@GLIBC_2.2.5
```

`strtoul` = **string to unsigned long**. The program parses input as a **number**.

That alone killed every hex-digest theory — md5, sha1 and sha256 were never going to work,
because the input *type* was wrong, not the value. Knowable before reading a single instruction.

Other tells:

| Import | Implies |
|---|---|
| `strtoul` / `atoi` | Numeric input parsing |
| `fgets` | Line-based reads — **keeps the trailing newline** |
| `fopen` + a filename in `strings` | Flag read from a file at runtime |
| `calloc` | Zero-filled allocation → explains zeros in a leak |
| No `crypt` / `EVP` / `SHA` | **No standard crypto.** Any "hash" is custom |
| `strcmp` / `strncmp` / `memcmp` | Comparison is a **library call** → one breakpoint leaks both sides |
| `strcspn` | Idiomatic newline strip: `buf[strcspn(buf,"\n")] = 0` |
| `isalpha` / `isdigit` / `tolower` | Input is being **filtered or transformed** before comparison |
| No comparison import at all | Compare is inline — find the `cmp`/`test` + conditional jump in `disas` |

## Reading C++ mangled names

A `_Z`-prefixed symbol is Itanium C++ mangling. It encodes the **signature**, not just the
name — so `nm` alone gives you argument types before you disassemble anything.

Format: `_Z` + name length + name + parameter codes.

| Symbol | Demangled |
|---|---|
| `_Z15decode_passwordPc` | `decode_password(char*)` |
| `_Z8sanitizePKcPc` | `sanitize(const char*, char*)` |
| `_Z13auth_sequencev` | `auth_sequence()` |
| `_Z8type_outPKcj` | `type_out(const char*, unsigned int)` |

Parameter codes: `v` = void, `c` = char, `i` = int, `j` = unsigned int, `Pc` = `char*`,
`PKc` = `const char*`.

```bash
nm binary | c++filt
```

**A function named `decode_password(char*)` is itself the finding:** the password is not a
stored string, it is **computed at runtime** into a caller-supplied buffer. That is why
`strings` never shows it.

## Compiler flags leak too

The `GCC:` / `GNU C++` line in `strings` records how it was built:

```
GNU C++17 13.3.0 -g -O0 -fstack-protector-strong -fcf-protection
```

| Flag | Means |
|---|---|
| `-g` | **Debug symbols present** — the debugger gets source lines and local variable names |
| `-O0` | No optimisation — assembly maps cleanly onto source, easy to read |
| `-fstack-protector-strong` | Stack canaries — overflow attacks will need a leak first |

A `.c` / `.cpp` path in `strings` (e.g. `/home/user/bypassme.c`) confirms debug info was
compiled in.

## Recognising djb2

```asm
mov QWORD PTR [rbp-0x8],0x1505   ; 5381
shl rax,0x5                      ; hash << 5  = hash * 32
add rdx,rax                      ; + hash     = hash * 33
add rax,rdx                      ; + c
```

```python
h = 5381
for c in s:
    h = (h * 33 + ord(c)) & 0xFFFFFFFFFFFFFFFF   # C wraps at 2**64 — Python does not
```

The mask is not optional when reimplementing djb2 from a C binary. Omit it and Python's
arbitrary-precision integers diverge from the binary's `unsigned long` the moment the value
exceeds 2⁶⁴ — around 12 characters of input.

**Fingerprints: the constant `5381`, and a `shl 5` + `add` pair (×33).** Worth memorising —
djb2 is everywhere.

General pattern: `shl n` followed by `add` of the original = multiply by `2ⁿ + 1`.

## XOR obfuscation

```asm
lea rdx,[rip+0xc89]    # obf_bytes
xor eax,0xffffffaa     # XOR 0xAA
```

A constant string XORed with a single byte so it does not appear in `strings`. Recover it from
`.rodata`:

```python
print(''.join(chr(b ^ 0xAA) for b in obf))
```

**Single-byte XOR is trivially reversible** and defeats nothing but a casual `strings` grep.

## Verifying against a known value

The deobfuscated `.rodata` produced `iUbh81!j*hn!` — byte-identical to the runtime memory leak.

**Two independent methods agreeing is how you know you are right.** Cross-check static findings
against observed behaviour whenever both are available.

## Local vs remote

`strings` showed `flag.txt`, opened from the **working directory**. Running the binary locally
reads whatever `flag.txt` happens to be sitting there — not the challenge flag.

**Develop the exploit locally, run it remotely.**

## Not learned yet

- [ ] Ghidra / IDA — decompiling to C instead of reading assembly
- [x] `gdb` / `lldb` — dynamic analysis, breakpoints, memory inspection ✅ → [LLDB — Breaking on the Comparison](lldb-breaking-on-comparison.md)
- [ ] Reading stripped binaries with no symbols
- [ ] Recognising other hashes from their constants (FNV, CRC32, MurmurHash)
- [ ] `ltrace` / `strace` — watching library and syscalls live
- [ ] `checksec` — binary protections and what each one blocks

**Seen in:** [picoCTF — heartbleed](../../challenges/picoCTF/heartbleed/README.md)
