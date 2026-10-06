# Toolchain

What is installed on this box, **what each tool actually is, and when you reach for it.**

This is the orientation layer: *which* tool and *why*. For the commands themselves, see
[CHEATSHEET.md](CHEATSHEET.md). Verification status and known quirks are at the bottom.

---

## Host

| | |
|---|---|
| **OS** | Kali Linux, kernel 7.1.5 |
| **CPU / RAM** | Intel Core Ultra 7 155H, 22 threads · 15 GiB |
| **GPU** | NVIDIA RTX 4050 Laptop (driver 550.163.01) — matters only for hashcat |
| **Disk** | 40 GB free on `/` |
| **Virtualisation** | VT-x on · Docker 29.8.2 · VirtualBox 7.2.16 (VM `Seed-Ubuntu20.04`) |
| **Wordlists** | `/opt/SecLists` (5.4 GB) |

Host-specific addresses and accounts are in `reference/LOCAL.md`, which is gitignored.

## Always do this first

```bash
source ~/ctf-venv/bin/activate
```

pwntools, z3 and the crypto libraries live in that venv, not in the system Python. Forgetting
this is the most common five-minute waste.

---

# The tools, by what they are for

## 1. Triage — identify an unknown file

Run these before deciding what kind of challenge you have. Two minutes here saves an hour of
attacking the wrong thing.

**`file`** — reads the first few bytes and names the format. Tells you architecture, whether an
ELF is stripped, whether something claiming to be a PNG actually is one. *Always the first
command.*

**`strings`** — prints runs of printable characters out of a binary file. Flags sit in plaintext
far more often than they should. Use `-el` for UTF-16 (Windows) text, which plain `strings` misses.

**`xxd`** — hex dump, and critically the reverse (`-r`), so you can edit bytes and write them
back. The standard use is repairing a deliberately corrupted file header. On this box it is
busybox's implementation (see quirks).

**`binwalk`** — scans a file for *other files embedded inside it*. A PNG with a ZIP hidden after
the image data is a stock misc challenge; binwalk finds and extracts it.

**`exiftool`** — reads image/document metadata: author, GPS, timestamps, and the comment fields
where flags like to hide.

**`foremost`** — carves files out of a raw blob by signature alone, ignoring filesystem
structure. For disk images and anything partially corrupted.

## 2. Web exploitation

**`ffuf`** — fast fuzzer. You give it a wordlist and a URL with `FUZZ` as a placeholder; it
substitutes and reports what responds. Finds unlinked directories, files, parameters and
virtual hosts. *Your default for web recon.* Its filtering (`-fs` by size, `-mc` by status code)
is what makes results readable.

**`gobuster`** — same job, different engine. Worth having when ffuf's output is awkward for a
particular target.

**`sqlmap`** — automates SQL injection end to end once you have found an injectable parameter:
detects the DBMS, enumerates databases and tables, dumps them. Don't reach for it until you have
evidence of injection; it is loud and slow against things that aren't vulnerable.

**`burpsuite`** — an intercepting proxy. Requests pause so you can read and rewrite them before
they reach the server, which exposes headers, cookies and hidden fields the browser hides. Use
it for *logic* bugs you need to see request by request; `curl` and `ffuf` beat it on anything
scriptable. See [notes/tools/burp-suite.md](../notes/tools/burp-suite.md).

**`curl`** — manual request crafting. Faster than Burp for a single test, and scriptable.

**`nmap`** — port and service scanning. Less central in jeopardy CTFs, where you are usually
given the exact port, but essential the moment you get a network range.

## 3. Cryptography

All in `~/ctf-venv`.

**`pycryptodome`** — implementations of AES, RSA, DES and the rest. For *using* crypto
primitives when you need to decrypt something or reproduce a scheme.

**`sympy` / `gmpy2` / `primefac`** — number theory. Factoring a small RSA modulus, integer roots,
modular inverses, arbitrary-precision arithmetic. `gmpy2.iroot` is the one you'll use for the
"e=3, no padding" cube-root attack.

**`z3`** — an SMT solver. You describe constraints ("a 20-byte printable string that produces
*this* output through *these* operations") and it finds a satisfying input. The right tool when a
binary validates input through a transformation you can transcribe but not invert by hand.

**`libnum`** — convenience helpers: int↔bytes, CRT, continued fractions (for Wiener's attack).

**`openssl`** — the CLI for standard formats. Inspecting certificates and keys, and
encrypt/decrypt where the scheme is a standard one.

## 4. Network forensics

**`tshark`** — Wireshark's command-line form: same capture engine and dissectors, no GUI. Being
scriptable is the whole point — you can filter, extract single fields, and loop over many files.
Start with `-z io,phs` to see which protocols a capture even contains, then
`--export-objects` to carve out transferred files and grep them.

**`wireshark`** — the GUI. Better for *exploring* an unfamiliar capture, where you don't yet
know what you're looking for. Switch to tshark once you do.

**`scapy`** (venv) — build, send and parse packets in Python. For crafting traffic, and for
pulling data out of a pcap programmatically when a display filter isn't expressive enough —
reassembling a file smuggled through ICMP payloads, for instance.

## 5. Disk and memory forensics

**`vol`** (volatility3) — memory dump analysis. Lists the processes that were running, their
command lines, open files, and can dump password hashes. `windows.cmdline` is often where the
flag is, because whatever the attacker typed is still in memory.

**`binwalk` / `foremost`** — as in triage, but these are the primary tools on a disk image.

**`strings` on the raw image** — crude and frequently sufficient. Try it before anything else.

## 6. Steganography

**`zsteg`** — tests PNG/BMP least-significant-bit encodings. `-a` tries every combination. First
thing to run on a suspicious PNG.

**`steghide`** — embeds and extracts data in JPG/BMP/WAV, protected by a passphrase. Try an
empty passphrase first; challenges often leave it blank.

**`stegseek`** — brute-forces a steghide passphrase at millions of guesses per second. When
`steghide` says the password is wrong, this is the follow-up.

**`tesseract`** — OCR. Pulls text out of an image, for flags that are only ever rendered as
pixels.

**`convert`** (ImageMagick) — image manipulation. Splitting colour planes and stretching contrast
reveals text hidden in a single channel or in near-identical shades.

## 7. Password and archive cracking

**`john`** (John the Ripper, jumbo) — CPU cracker whose real value is the `*2john` family:
`zip2john`, `ssh2john`, `pdf2john`, `rar2john`, `office2john`, `keepass2john`. These convert an
encrypted *file* into a hash string that can then be cracked. Any "here is a password-protected
archive" challenge starts here.

**`hashcat`** — GPU cracker. Much faster than john on raw hashes (20.8 GH/s on MD5 here), so it
is the better choice for bare hash strings and for anything needing large keyspaces. Needs the
right `-m` mode number; `--identify` guesses it for you.

**`fcrackzip`** — quick ZIP brute force without the zip2john step. Convenient for small jobs.

**`pdfcrack`** — the same for PDF passwords.

**`stegseek`** — listed above, but it belongs to this family too.

Wordlist: `/opt/SecLists/Passwords/Leaked-Databases/rockyou.txt` — extract the `.tar.gz` once
before the event. The `rockyou-NN.txt` files are length-capped subsets and make a faster first pass.

## 8. Reverse engineering

**`ghidra`** — the NSA's decompiler. Turns machine code back into readable C-like
pseudocode. *The primary RE tool*: you read logic instead of assembly. Launcher is `ghidra`;
there is also a headless mode for scripted analysis. Slow first launch, so do it once before the event.

**`radare2`** — a disassembler and binary editor. Faster than Ghidra for a quick look, searching
for a string, or patching bytes in place. Complements rather than replaces it.

**`gdb` + `pwndbg`** — dynamic analysis: run the program and inspect it as it executes. pwndbg
is a plugin that makes gdb usable for exploitation, with readable stack/register views,
`vmmap`, `checksec` and cyclic-pattern offset finding. The highest-value move is breaking on the
comparison and reading both arguments — see
[notes/workflows/lldb-breaking-on-comparison.md](../notes/workflows/lldb-breaking-on-comparison.md).

**`ltrace`** — logs library calls with their arguments. Frequently reveals
`strcmp(input, "password")` outright, with no reversing at all. Try it before opening a disassembler.

**`strace`** — logs system calls. Shows which files a program opens and what it reads, which is
how you learn the flag comes from `flag.txt` in the working directory.

**`nm` / `objdump`** (binutils) — list symbols; disassemble. `nm -D` showing the imported libc
functions is the single highest-information 5 seconds available: `strtoul` in the imports proves
input is parsed as a number, which kills every "it must be a hash digest" theory at once. See
[notes/workflows/static-binary-analysis.md](../notes/workflows/static-binary-analysis.md).

## 9. Binary exploitation

**`pwntools`** (venv) — the exploit-writing library. Handles process and remote I/O, struct
packing, ELF symbol lookup, ROP chain construction, shellcode and format-string payloads. Also a
CLI: `pwn checksec` (protections), `pwn cyclic` (offset patterns), `pwn template` (generates an
exploit skeleton — use it).

**`ROPgadget`** (venv) — finds usable instruction sequences ("gadgets") ending in `ret`, which
you chain together to execute code when the stack is non-executable.

**`one_gadget`** — finds a single address inside libc that spawns a shell by itself. Turns a
ret2libc exploit into a one-address write when its register constraints are satisfiable.

**`capstone` / `unicorn`** (venv) — a disassembly engine and a CPU emulator, as libraries. For
when you need to decode or *run* instructions programmatically rather than in a debugger.

**`gcc`** — compile your own test cases. Reproducing a vulnerable pattern locally is often
faster than reasoning about the original.

## 10. Sandboxing

**Docker** — run untrusted binaries without risking the host, and match the challenge's libc by
choosing the Ubuntu tag it was built against (20.04 = glibc 2.31, 22.04 = 2.35, 24.04 = 2.39).
Libc version mismatches silently break heap and ret2libc exploits, so this matters more than it
sounds. Add `--cap-add=SYS_PTRACE` to debug inside a container.

**VirtualBox** — held in reserve. See the decision below.

## 11. OSINT (pipx)

**`sherlock`** / **`maigret`** — check a username across hundreds of sites.
**`ghunt`** — enumerate what a Google account exposes.
**`socid-extractor`** — pull identifiers out of profile pages.

Relevant if Cryovault includes an OSINT category; otherwise idle.

## 12. Shell utilities worth naming

`jq` JSON querying · `7z`/`zip`/`unzip` archives · `hexdump`/`od` hex views without xxd ·
`pdftotext` text out of PDFs · `socat` a more capable netcat · `nc` raw TCP, the usual way to
reach a challenge service · `tmux` keep sessions alive and split panes · `radiff2` binary diffing.

---

# Status and quirks

Verified functionally on 2026-10-06 — each tested against a real artifact, not just checked for
on PATH. john cracked a real zip, hashcat cracked MD5/SHA1/SHA256/NTLM on GPU, stegseek
recovered a real passphrase, tesseract OCR'd real text, ghidra completed a headless
import+analyze, tshark parsed a generated pcap, radare2 analyzed a binary, one_gadget found 5
gadgets, vol lists 162 plugins, pwndbg loads 199 commands.

**hashcat** needed `libnvrtc12` — it detected the GPU but could not compile its kernels without
NVRTC, and there was no CPU fallback device. Fixed. Two naming traps: `best64.rule` is *john's*
file, while hashcat ships `best66.rule`, which is small enough to miss `password` → `Password1`
— use **`rockyou-30000.rule`**. And john's `.rule` files are not hashcat-compatible: it silently
skips what it cannot parse and reports `Exhausted` having cracked nothing. The
`nvmlDeviceGetFanSpeed` and `CUDA SDK Toolkit not installed` warnings are cosmetic.

**john** needs a *seekable* wordlist. `--wordlist=<(printf ...)` fails with `ftell: Illegal
seek`; pass a real file.

**`xxd`** — the apt package does not work on this box. busybox implements xxd, including `-r`,
`-p`, `-g`, `-c`, `-l` and `-s`, so it is symlinked in as the real thing at
`/usr/local/bin/xxd -> /usr/bin/busybox` (busybox dispatches on `argv[0]`). `/usr/local/bin` is
on the default PATH for every shell, including non-interactive ones, so this works inside
scripts. A second symlink at `~/bin/xxd` plus `~/bin` on PATH from `~/.zshrc` covers interactive
use (backup: `.zshrc.bak-2026-10-06`).

**Docker could not pull any image.** `~/.docker/config.json` set `credsStore: desktop`, but
`docker-credential-desktop` does not exist on this system, so every pull died with `error
getting credentials`. The key is removed — `auths` was empty, so nothing was lost — and pulls are
verified working. Backup: `~/.docker/config.json.bak-2026-10-06`.

**Ghidra's launcher is `ghidra`**, not `ghidraRun`. Headless:
`/usr/share/ghidra/support/analyzeHeadless <projdir> <projname> -import <binary>`.

**ARM/MIPS emulation is deliberately not installed.** The `/usr/bin/qemu-*-static` symlinks on
this box dangle — `qemu-user-static` is a transitional stub here and apt satisfied it with the
i386 build. Not needed for this CTF. If a non-x86 binary ever appears:
`sudo apt install qemu-user`.

---

# VM vs Docker

The host is already Kali, so Docker covers nearly everything: untrusted binaries, libc matching
for pwn, and running a web challenge's own compose file.

A VM earns its keep only for kernel or driver exploits, real malware where you want snapshot
rollback, Windows or exotic architectures, and large disk/memory images you'd rather keep off
the host.

**Verdict: skip the VM for Cryovault.** Revisit if a kernel or Windows challenge turns up.

---

# Before the event

```bash
source ~/ctf-venv/bin/activate                 # make it muscle memory
docker pull ubuntu:20.04 && docker pull ubuntu:22.04 && docker pull ubuntu:24.04
sudo tar -xzf /opt/SecLists/Passwords/Leaked-Databases/rockyou.txt.tar.gz \
  -C /opt/SecLists/Passwords/Leaked-Databases/
ghidra                                         # first launch is slow; get it over with
```

Conventions for recording work are in the [repo README](../README.md); scaffold a challenge
directory with `bin/newchal`.
