# CTF Workspace Notes (assistant's persistent log)

Event: **Cryovault** — national-level CTF hackathon, ~2026-10-10. Docs live in `~/Cryovault/writeups/`.
Details still TBD — ask user: name, format (jeopardy/AD), categories, team size, scoring, internet/rules.

## Host (verified 2026-10-05)
- Kali Linux, kernel 7.1.5, Intel Core Ultra 7 155H, 22 CPUs, 15 GiB RAM, 40 GB free on /, VT-x on.
- Docker 29.8.2 (user in `docker` group; images: nginx:alpine). Docker Desktop also installed.
- VirtualBox 7.2.16, existing VM `Seed-Ubuntu20.04`.
- Tailscale in use. Host-specific addresses kept in `writeups/LOCAL.md` (gitignored).

## CTF toolchain — INSTALLED
**Python venv `~/ctf-venv`** (activate: `source ~/ctf-venv/bin/activate`):
pwntools 4.15.0, ROPGadget 7.7, capstone 6.0.0a11, unicorn 2.1.2, pycryptodome 3.24.0,
cryptography 50.0.2, scapy 2.8.0, requests, pillow.
→ `pwn checksec <bin>` replaces standalone checksec. `pwn cyclic`, `pwn template` also available.

**System python3** (separate from venv): scapy, pycryptodomex, sympy, numpy, capstone, python-magic, requests.

**Binaries**: gdb + **pwndbg** (~/pwndbg, wired into ~/.gdbinit, loads 199 cmds — verified),
gcc, gobuster, ffuf, sqlmap, burpsuite, nmap, wireshark (GUI), binwalk, foremost, exiftool,
steghide, zsteg (gem), strace, ltrace, nc, socat, openssl, 7z, zip/unzip, hexdump, jq,
pdftotext, imagemagick (convert), go, cargo, node, java, tmux, git, curl, wget.

**Wordlists**: /opt/SecLists (5.4 GB).

**pipx (OSINT)**: ghunt, maigret, sherlock-project, socid-extractor, user-scanner, headroom-ai.

## GAPS (not installed as of 2026-10-05)
Priority for the 4 announced waves (web+crypto / net-forensics+rev / binexp / ?):
1. `john` (jumbo) + `hashcat` — password cracking; zip2john/ssh2john etc. **high value, likely needed**
2. `tshark` — CLI pcap analysis (only wireshark GUI present; tshark is a separate pkg) **high**
3. `ghidra` + `radare2` — static RE / decompiler for Wave 2 rev **high**
4. `volatility3` — memory forensics
5. `qemu-user-static` + `binfmt-support` — run ARM/MIPS challenge binaries (also makes Docker multi-arch work)
6. `one_gadget` (gem) — pwn ret2libc
7. `z3-solver`, `gmpy2`, `primefac`, `libnum`, `sympy` in ~/ctf-venv — crypto/rev solving
8. `fcrackzip`, `pdfcrack`, `stegseek` — archive/stego brute force
9. `xxd` (vim-common), `tesseract-ocr` — hex editing, OCR for stego/misc
10. Optional: `sagemath` (heavy, ~2 GB; only if hard crypto), `apktool`+`jadx` (Android), `RsaCtfTool`

## VM vs Docker — decision
Host is already Kali, so Docker covers almost everything:
- untrusted binaries → `docker run --rm -it --cap-add=SYS_PTRACE ubuntu:22.04`
- pwn: match challenge libc by picking the right ubuntu tag (20.04/22.04/24.04)
- web: run the challenge's own docker-compose
VM only needed for: kernel/driver exploits (or use qemu), real malware (snapshot rollback),
Windows/odd-arch, big disk/memory forensics isolation.
→ Verdict: **skip the VM**; install qemu-user-static instead. Revisit if a kernel/Windows chal appears.

## Per-challenge convention
`~/CTF/<event>/<category>/<challenge>/` + `notes.md` (what was tried, flag, short writeup).

## Past work in ~/CTF
CNS (pcaps), HTB (rev_spookypass), L8/Hackathon-26, pico (picoCTF), Cryovault, trial.
`Layer8 sudo$rm CTF brochure.pdf` = April 2026 Layer8 event (past, not the upcoming one).
