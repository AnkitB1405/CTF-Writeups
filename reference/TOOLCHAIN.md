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

## Verification pass 2026-10-06
Everything from the install list is present and functionally tested (not just `command -v`):
john cracked a real zip, stegseek recovered a real passphrase, tesseract OCR'd real text,
ghidra completed a headless import+analyze, tshark parsed a generated pcap, one_gadget found
5 gadgets, radare2 analyzed a binary, vol lists 162 plugins, pwndbg loads.

Outstanding fix — hashcat only:
```bash
sudo apt install libnvrtc12
```
hashcat detects the RTX 4050 but dies on `Failed to initialize NVIDIA RTC library`; NVRTC is
absent and there is no CPU fallback device. Use `john` meanwhile.

`xxd`: the apt package does not work here. busybox implements xxd (with `-r`/`-p`), so
`~/bin/xxd -> /usr/bin/busybox` provides it — busybox dispatches on `argv[0]`, so it works in
scripts too. `~/bin` added to PATH in `~/.zshrc` (backup `.zshrc.bak-2026-10-06`).

ARM/MIPS emulation: **deliberately not installed.** `qemu-user-static` here is a transitional
stub whose `/usr/bin/qemu-*-static` symlinks dangle; not needed for this CTF. If ever required:
`sudo apt install qemu-user`.

Fixed during the pass: `~/.docker/config.json` had `credsStore: desktop` with no such helper on
the system, so **every `docker pull` failed**. Key removed (`auths` was empty); pulls verified
working. Backup: `~/.docker/config.json.bak-2026-10-06`.

Ghidra's launcher on Kali is **`ghidra`**, not `ghidraRun`. Headless:
`/usr/share/ghidra/support/analyzeHeadless <projdir> <projname> -import <binary>`.


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
