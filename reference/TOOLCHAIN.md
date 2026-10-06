# CTF Toolchain — What Each Tool Is, and When To Reach For It

A general guide to the tools worth having for jeopardy-style CTFs: what each one actually does,
which problem it solves, and which to prefer when two overlap.

This is the orientation layer — *which* tool and *why*. For the commands themselves see
[CHEATSHEET.md](CHEATSHEET.md). Written against Kali/Debian; package names may differ elsewhere.

```bash
# the broad strokes, on Kali or Debian
sudo apt install -y john hashcat tshark radare2 ghidra gobuster ffuf sqlmap burpsuite \
  nmap binwalk foremost exiftool steghide stegseek fcrackzip pdfcrack tesseract-ocr \
  gdb ltrace strace socat netcat-openbsd jq p7zip-full imagemagick poppler-utils

# the Python side belongs in a venv, not system site-packages
python3 -m venv ~/ctf-venv && source ~/ctf-venv/bin/activate
pip install pwntools ROPGadget capstone unicorn pycryptodome z3-solver gmpy2 \
  primefac libnum sympy scapy pillow requests

pipx install volatility3                       # memory forensics
sudo gem install zsteg one_gadget              # PNG stego, libc one-shot gadgets
git clone https://github.com/pwndbg/pwndbg ~/pwndbg && ~/pwndbg/setup.sh
git clone https://github.com/danielmiessler/SecLists /opt/SecLists
```

**Activate the venv first, every session.** pwntools and z3 live there, not in system Python.
Forgetting is the most common five-minute waste.

---

## 1. Triage — identify an unknown file

Run these before deciding what kind of challenge you have. Two minutes here saves an hour of
attacking the wrong thing.

**`file`** — reads the first bytes and names the format. Tells you architecture, whether an ELF
is stripped, whether something claiming to be a PNG actually is one. *Always first.*

**`strings`** — prints runs of printable characters out of a binary. Flags sit in plaintext far
more often than they should. `-el` catches UTF-16 (Windows) text that plain `strings` misses.

**`xxd`** — hex dump, and critically the reverse (`-r`), so you can edit bytes and write them
back. The standard use is repairing a deliberately corrupted file header. If the `xxd` package
is unavailable or broken, **busybox implements it** — `busybox xxd` supports `-r -p -g -c -l -s`,
and a symlink named `xxd` pointing at busybox behaves as the real thing, since busybox dispatches
on `argv[0]`.

**`binwalk`** — scans a file for *other files embedded inside it*. A PNG with a ZIP appended
after the image data is a stock misc challenge; binwalk finds and extracts it.

**`exiftool`** — image and document metadata: author, GPS, timestamps, and the comment fields
where flags like to hide.

**`foremost`** — carves files out of a raw blob by signature alone, ignoring filesystem
structure. For disk images and anything partially corrupted.

## 2. Web exploitation

**`ffuf`** — fast fuzzer. Give it a wordlist and a URL with `FUZZ` as a placeholder; it
substitutes and reports what responds. Finds unlinked directories, files, parameters and virtual
hosts. *The default for web recon.* Its filtering — `-fs` by response size, `-mc` by status code
— is what makes the output readable, and is why it beats older scanners.

**`gobuster`** — same job, different engine. Worth having for when ffuf's output is awkward on a
particular target.

**`dirb`** — legacy. Its default wordlist tests bare words with no file extension, so it misses
`login.php` entirely unless you pass `-X .php`. Prefer ffuf (`-e .php`) or gobuster (`-x php`).

**`sqlmap`** — automates SQL injection end to end once you have found an injectable parameter:
fingerprints the DBMS, enumerates databases and tables, dumps them. Don't reach for it before you
have evidence of injection; it is loud and slow against things that aren't vulnerable.

**`burpsuite`** — an intercepting proxy. Requests pause so you can read and rewrite them before
they reach the server, exposing headers, cookies and hidden fields the browser hides. Use it for
*logic* bugs you need to see request by request; `curl` and `ffuf` beat it on anything scriptable.

**`curl`** — manual request crafting. Faster than Burp for a single test, and scriptable.

**`nmap`** — port and service scanning. Less central in jeopardy CTFs, where you are usually given
the exact port, but essential the moment you get a network range.

## 3. Cryptography

**`pycryptodome`** — implementations of AES, RSA, DES and friends. For *using* primitives when you
need to decrypt something or reproduce a scheme.

**`sympy` / `gmpy2` / `primefac`** — number theory. Factoring a small RSA modulus, integer roots,
modular inverses, arbitrary-precision arithmetic. `gmpy2.iroot` is the one for the "e=3, no
padding" cube-root attack.

**`z3`** — an SMT solver. You describe constraints ("a 20-byte printable string that produces
*this* output through *these* operations") and it finds a satisfying input. The right tool when a
binary validates input through a transformation you can transcribe but not invert by hand.

**`libnum`** — convenience helpers: int↔bytes, CRT, continued fractions (for Wiener's attack).

**`openssl`** — the CLI for standard formats: inspecting certificates and keys, and
encrypt/decrypt where the scheme is a standard one.

## 4. Network forensics

**`tshark`** — Wireshark's command-line form: same capture engine and dissectors, no GUI. Being
scriptable is the whole point — filter, extract single fields, loop over many files. Start with
`-z io,phs` to see which protocols a capture even contains, then `--export-objects` to carve out
transferred files and grep them.

**`wireshark`** — the GUI. Better for *exploring* an unfamiliar capture when you don't yet know
what you're looking for. Switch to tshark once you do.

**`scapy`** — build, send and parse packets in Python. For crafting traffic, and for pulling data
out of a pcap programmatically when a display filter isn't expressive enough — reassembling a
file smuggled through ICMP payloads, for instance.

## 5. Disk and memory forensics

**`volatility3`** (`vol`) — memory dump analysis. Lists the processes that were running, their
command lines, open files, and can dump password hashes. `windows.cmdline` is often where the
flag is, because whatever was typed is still in memory.

**`binwalk` / `foremost`** — as in triage, but these are the primary tools on a disk image.

**`strings` on the raw image** — crude and frequently sufficient. Try it before anything else.

## 6. Steganography

**`zsteg`** — tests PNG/BMP least-significant-bit encodings. `-a` tries every combination. First
thing to run on a suspicious PNG.

**`steghide`** — embeds and extracts data in JPG/BMP/WAV behind a passphrase. Try an empty
passphrase first; challenges often leave it blank.

**`stegseek`** — brute-forces a steghide passphrase at millions of guesses per second. The
follow-up when `steghide` says the password is wrong.

**`tesseract`** — OCR. Pulls text out of an image, for flags only ever rendered as pixels.

**`convert`** (ImageMagick) — image manipulation. Splitting colour planes and stretching contrast
reveals text hidden in one channel or in near-identical shades.

Audio stego usually means looking at the spectrogram — flags get drawn into it. Audacity or
`sox` will show you.

## 7. Password and archive cracking

**`john`** (John the Ripper, jumbo) — CPU cracker whose real value is the `*2john` family:
`zip2john`, `ssh2john`, `pdf2john`, `rar2john`, `office2john`, `keepass2john`. These convert an
encrypted *file* into a crackable hash string. Any "here is a password-protected archive"
challenge starts here.

> **Gotcha:** john needs a *seekable* wordlist. `--wordlist=<(printf ...)` fails with
> `ftell: Illegal seek`. Pass a real file.

**`hashcat`** — GPU cracker, far faster than john on raw hashes, so it is the better choice for
bare hash strings and large keyspaces. Needs the right `-m` mode number; `--identify` guesses it.

> **Gotchas:** hashcat needs NVRTC present to compile its kernels — on NVIDIA that means the
> driver **and** `libnvrtc12`; with the driver alone it detects the GPU and then fails with
> `Failed to initialize NVIDIA RTC library`. Also, `best64.rule` is **john's** file; hashcat
> ships `best66.rule`, which is small enough to miss `password` → `Password1`. Prefer
> `rockyou-30000.rule`. John's `.rule` files are **not** hashcat-compatible — it silently skips
> what it cannot parse and reports `Exhausted` having cracked nothing, which looks exactly like
> "the password wasn't in my list."

**`fcrackzip`** — quick ZIP brute force without the zip2john step. Convenient for small jobs.

**`pdfcrack`** — the same for PDF passwords.

Wordlist: `rockyou.txt`, in SecLists under `Passwords/Leaked-Databases/`. It ships compressed —
extract it once up front. The `rockyou-NN.txt` files are length-capped subsets, useful as a
faster first pass.

## 8. Reverse engineering

**`ghidra`** — the NSA's decompiler. Turns machine code back into readable C-like pseudocode.
*The primary RE tool*: you read logic instead of assembly. On Kali the launcher is **`ghidra`**,
not `ghidraRun`; there is also a headless mode
(`/usr/share/ghidra/support/analyzeHeadless`) for scripted analysis. First launch is slow — do it
once before you need it.

**`radare2`** — disassembler and binary editor. Faster than Ghidra for a quick look, finding a
string, or patching bytes in place. Complements it rather than replacing it.

**`gdb` + `pwndbg`** — dynamic analysis: run the program and inspect it as it executes. pwndbg is
a plugin that makes gdb usable for exploitation, with readable stack and register views, `vmmap`,
`checksec` and cyclic-pattern offset finding. The highest-value move is breaking on the
comparison and reading both arguments.

**`ltrace`** — logs library calls with their arguments. Frequently reveals
`strcmp(input, "password")` outright, with no reversing at all. **Try it before opening a
disassembler.**

**`strace`** — logs system calls. Shows which files a program opens and reads, which is how you
learn the flag comes from `flag.txt` in the working directory.

**`nm` / `objdump`** (binutils) — list symbols; disassemble. `nm -D` showing the imported libc
functions is the highest-information five seconds available: `strtoul` in the imports proves
input is parsed as a number, killing every "it must be a hash digest" theory at once.

Other languages: Python `.pyc` → `uncompyle6` / `decompyle3`. Java `.jar`/`.class` → `jadx` or
`cfr`. Android `.apk` → `apktool d` then `jadx`. Go and Rust binaries are large — go straight to
strings and the symbol table.

## 9. Binary exploitation

**`pwntools`** — the exploit-writing library. Process and remote I/O, struct packing, ELF symbol
lookup, ROP chain construction, shellcode, format-string payloads. Also a CLI: `pwn checksec`
(protections — no separate `checksec` needed), `pwn cyclic` (offset patterns), `pwn template`
(generates an exploit skeleton; use it).

**`ROPgadget`** — finds usable instruction sequences ("gadgets") ending in `ret`, which you chain
to execute code when the stack is non-executable.

**`one_gadget`** — finds a single address inside libc that spawns a shell by itself, turning a
ret2libc exploit into a one-address write when its register constraints are satisfiable.

**`capstone` / `unicorn`** — a disassembly engine and a CPU emulator, as libraries. For decoding
or *running* instructions programmatically rather than in a debugger.

**`gcc`** — compile your own test cases. Reproducing a vulnerable pattern locally is often faster
than reasoning about the original.

**`qemu-user`** — runs a non-x86 (ARM, MIPS) challenge binary on an x86 host, and with
`binfmt-support` makes `docker --platform` work for other architectures. Note that on Debian 13
`qemu-user-static` is a *transitional stub* — if `/usr/bin/qemu-*-static` are dangling symlinks,
install `qemu-user` instead.

## 10. Sandboxing with Docker

Run untrusted binaries without risking the host, and **match the challenge's libc** by choosing
the Ubuntu tag it was built against:

| Tag | glibc |
|---|---|
| `ubuntu:20.04` | 2.31 |
| `ubuntu:22.04` | 2.35 |
| `ubuntu:24.04` | 2.39 |

Libc mismatches silently break heap and ret2libc exploits, so this matters more than it sounds.
Add `--cap-add=SYS_PTRACE` to debug inside a container, and `--network none` for genuinely
untrusted samples. Pull the images *before* the event — bandwidth on the day is not guaranteed.

> **Gotcha:** if Docker Desktop was ever installed, `~/.docker/config.json` may set
> `credsStore: desktop`. Without that helper on PATH, **every** `docker pull` fails with
> `error getting credentials`. Remove the `credsStore` key if `auths` is empty.

## 11. OSINT

**`sherlock`** / **`maigret`** — check a username across hundreds of sites.
**`ghunt`** — enumerate what a Google account exposes.
**`socid-extractor`** — pull identifiers out of profile pages.

## 12. Shell utilities worth naming

`jq` JSON querying · `7z` / `zip` / `unzip` archives · `hexdump` / `od` hex views when xxd is
absent · `pdftotext` text out of PDFs · `socat` a more capable netcat · `nc` raw TCP, the usual
way to reach a challenge service · `tmux` keep sessions alive and split panes · `radiff2` binary
diffing.

---

## Choosing between overlapping tools

| Situation | Reach for | Not |
|---|---|---|
| Web content discovery | `ffuf` | `dirb` (no extensions by default) |
| Reading a binary's logic | `ghidra` (decompiles to C) | `radare2` (fine for a quick look or a patch) |
| "What does this binary compare my input against?" | `ltrace` first, then `gdb`/pwndbg | jumping straight to a disassembler |
| Scripted pcap work | `tshark` | the Wireshark GUI (use it to explore first) |
| Encrypted archive / SSH key / PDF | `john` + the matching `*2john` | `hashcat` (wrong tool for file formats) |
| A bare hash string | `hashcat` (GPU) | `john` (works, just slower) |
| Testing one request by hand | `curl` | Burp (slower for a single shot) |

---

## Workflow

**On any unknown file:** `file` → `strings | grep -i flag` → `exiftool` → `binwalk` → the
category-specific tool. The lazy check finds the flag more often than it has any right to.

**During a timed event:** one directory per challenge with notes as you go; write the flag down
the moment you get it; if a challenge stalls for twenty minutes, switch and come back.
