# CTF Toolkit — Use Cases & Cheatsheet
Host: Kali (kernel 7.1.5), 22 CPU, 15 GiB RAM, Docker + VirtualBox. Written 2026-10-06.  
Docs home: `~/Cryovault/writeups/` (symlink `~/Cryovault` → `~/CTF/Cryovault`).

---

## 0. STATUS — read this first

### Installed & verified
`pwntools` `ROPGadget` `capstone` `unicorn` `pycryptodome` `cryptography` `scapy` `pillow`
`z3` `gmpy2` `primefac` `libnum` `sympy`  ← all inside `~/ctf-venv`
`gdb`+`pwndbg` `one_gadget` `vol`(volatility3) `gobuster` `ffuf` `sqlmap` `burpsuite`
`nmap` `wireshark`(GUI) `binwalk` `foremost` `exiftool` `steghide` `zsteg`
`strace` `ltrace` `nc` `socat` `openssl` `7z` `hexdump` `jq` `pdftotext` `convert` `gcc`

### STILL MISSING — step 2 did not run
```bash
echo 'wireshark-common wireshark-common/install-setuid boolean true' | sudo debconf-set-selections
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  john hashcat tshark radare2 ghidra qemu-user-static binfmt-support \
  fcrackzip pdfcrack stegseek vim-common tesseract-ocr
```
Without these you have **no password cracking, no CLI pcap tool, no decompiler, no OCR**.

### Always start here
```bash
source ~/ctf-venv/bin/activate     # pwntools, z3, crypto libs live here
```

---

## 1. TRIAGE — every challenge starts here

| Tool | Use case |
|---|---|
| `file` | What am I even looking at? Always first. |
| `strings` | Flags hide in plaintext more often than you'd believe. |
| `xxd` | Read/patch raw bytes. Fix broken magic headers. |
| `binwalk` | Find files embedded inside other files. |
| `exiftool` | Metadata — author, GPS, comments. Flags live in comments. |

```bash
file chal                          # identify type
strings -n 8 chal | less           # printable runs, min length 8
strings -el chal                   # 16-bit little-endian (Windows/UTF-16)
xxd chal | head -5                 # inspect magic bytes
xxd -r patched.hex > fixed.bin     # hex back to binary
binwalk chal                       # list embedded files
binwalk -e --run-as=root chal      # extract them
exiftool image.png                 # all metadata
```

**Broken-header fix** (common misc challenge): PNG must start `89 50 4E 47`, JPG `FF D8 FF`,
ZIP `50 4B 03 04`, PDF `25 50 44 46`, ELF `7F 45 4C 46`, GZIP `1F 8B`.
```bash
xxd file.bad | head -2             # see what's wrong
printf '\x89PNG\r\n\x1a\n' | cat - <(tail -c +9 file.bad) > fixed.png
```

---

## 2. WEB — Wave 1

| Tool | Where you'd use it |
|---|---|
| `ffuf` | Fastest dir/file/param/vhost fuzzer. Your default. |
| `gobuster` | Same job, different engine. Use when ffuf's output is noisy. |
| `sqlmap` | Automate SQL injection once you've found an injectable param. |
| `burpsuite` | GUI proxy — intercept, replay, tamper. For logic bugs ffuf can't see. |
| `curl` | Manual request crafting. Faster than Burp for one-off tests. |

```bash
# directory brute force
ffuf -u http://TARGET/FUZZ -w /opt/SecLists/Discovery/Web-Content/raft-medium-directories.txt
ffuf -u http://TARGET/FUZZ -w WORDLIST -e .php,.txt,.bak,.zip   # with extensions
ffuf -u http://TARGET/FUZZ -w WORDLIST -mc 200,301,403 -fs 1234 # filter by size

# parameter + vhost discovery
ffuf -u 'http://TARGET/page?FUZZ=test' -w /opt/SecLists/Discovery/Web-Content/burp-parameter-names.txt -fs 0
ffuf -u http://TARGET -H 'Host: FUZZ.target.com' -w /opt/SecLists/Discovery/DNS/subdomains-top1million-5000.txt

gobuster dir -u http://TARGET -w WORDLIST -x php,txt -t 50

# sqli
sqlmap -u 'http://TARGET/?id=1' --batch --dbs
sqlmap -u 'http://TARGET/?id=1' --batch -D dbname --tables
sqlmap -u 'http://TARGET/?id=1' --batch -D dbname -T users --dump
sqlmap -r request.txt --batch --dump-all     # request.txt saved from Burp

# curl essentials
curl -i http://TARGET                        # include headers
curl -s http://TARGET | grep -oE 'flag\{[^}]*\}'
curl -X POST -d 'user=admin&pass=x' http://TARGET/login
curl -b 'session=abc' -H 'X-Forwarded-For: 127.0.0.1' http://TARGET
curl -s http://TARGET/page | python3 -m html.parser   # or pipe to grep
```

**Manual checks worth 30 seconds each:** `/robots.txt`, `/.git/`, `/.env`, page source comments,
cookies (decode base64/JWT), `?file=../../../etc/passwd`, `admin'--` in login.

---

## 3. CRYPTO — Wave 1

All in `~/ctf-venv`. `openssl` for standard formats, Python for everything else.

| Library | Use case |
|---|---|
| `pycryptodome` | AES/RSA/DES implementation work. |
| `sympy` / `gmpy2` / `primefac` | Factoring, modular math, big integers. |
| `z3` | Constraint solver — "find input where output == X". Also cracks custom ciphers. |
| `libnum` | Quick int↔bytes, CRT, continued fractions. |

```bash
# classical / encoding
echo 'text' | base64 -d
echo 'text' | tr 'A-Za-z' 'N-ZA-Mn-za-m'       # ROT13
echo 'hex' | xxd -r -p                          # hex to bytes
python3 -c "print(bytes.fromhex('41424344'))"

# openssl
openssl enc -d -aes-256-cbc -in file.enc -out file -k PASSWORD
openssl rsa -in key.pem -text -noout            # inspect RSA key
openssl x509 -in cert.pem -text -noout          # inspect certificate
openssl s_client -connect host:443              # grab a cert
```

**RSA — the four cases you'll actually see:**
```python
from Crypto.Util.number import long_to_bytes, inverse
from sympy import factorint, isprime
import primefac

# 1. small n -> just factor it
p, q = list(factorint(n))
d = inverse(e, (p-1)*(q-1)); print(long_to_bytes(pow(c, d, n)))

# 2. e=3 and m^3 < n -> cube root, no key needed
import gmpy2; print(long_to_bytes(gmpy2.iroot(c, 3)[0]))

# 3. shared prime between two moduli
from math import gcd; p = gcd(n1, n2)

# 4. Wiener (d too small) -> continued fractions
# pip install owiener  (or use libnum's CF helpers)
```

**z3 for "reverse this check":**
```python
from z3 import *
s = Solver(); flag = [BitVec(f'c{i}', 8) for i in range(20)]
for c in flag: s.add(c >= 0x20, c <= 0x7e)          # printable
s.add(flag[0] == ord('f'))                           # known prefix
# s.add(<transcribe the binary's check here>)
if s.check() == sat:
    print(''.join(chr(s.model()[c].as_long()) for c in flag))
```

**XOR — repeating key:**
```python
from pwn import xor
print(xor(ct, b'key'))                               # pwntools does cycling
# unknown single-byte key: brute all 256
for k in range(256):
    out = bytes(b ^ k for b in ct)
    if b'flag' in out: print(k, out)
```

---

## 4. NETWORK FORENSICS — Wave 2

| Tool | Use case |
|---|---|
| `tshark` | Scriptable pcap analysis. Grep-able, loop-able. Your workhorse. |
| `wireshark` | GUI. Use for *exploring* an unfamiliar pcap, then switch to tshark. |
| `scapy` | Craft/replay packets, or parse a pcap programmatically. |

```bash
tshark -r cap.pcap                              # dump everything
tshark -r cap.pcap -q -z io,phs                 # protocol hierarchy — START HERE
tshark -r cap.pcap -q -z conv,tcp               # conversations
tshark -r cap.pcap -Y 'http.request'            # display filter
tshark -r cap.pcap -Y 'http.request.method=="POST"' -T fields -e http.file_data
tshark -r cap.pcap -T fields -e ip.src -e ip.dst -e tcp.port
tshark -r cap.pcap --export-objects http,./carved    # CARVE FILES — then grep ./carved
tshark -r cap.pcap --export-objects smb,./carved
tshark -r cap.pcap -z follow,tcp,ascii,0        # follow stream index 0
tshark -r cap.pcap -Y 'dns' -T fields -e dns.qry.name | sort -u   # DNS exfil
tshark -r cap.pcap -Y 'icmp' -T fields -e data  # ICMP tunnelling
```

**The standard pcap workflow:**
```bash
tshark -r cap.pcap -q -z io,phs                 # 1. what protocols exist?
tshark -r cap.pcap --export-objects http,./out  # 2. carve transferred files
grep -rao 'flag{[^}]*}' ./out                   # 3. grep the carvings
strings cap.pcap | grep -i flag                 # 4. lazy fallback, works often
```

**scapy:**
```python
from scapy.all import *
pkts = rdpcap('cap.pcap')
for p in pkts:
    if p.haslayer(Raw): print(p[Raw].load)
# exfil over ICMP payload
print(b''.join(p[Raw].load for p in pkts if ICMP in p and Raw in p))
```

---

## 5. DISK & MEMORY FORENSICS

| Tool | Use case |
|---|---|
| `foremost` | Carve files from a raw disk image by signature. |
| `binwalk` | Same idea, better on firmware. |
| `vol` (volatility3) | Memory dump analysis — processes, cmdlines, hashes. |
| `strings` | Brute-force first pass on any image. Never skip it. |

```bash
foremost -i disk.dd -o out/                     # carve by signature
binwalk -e firmware.bin
mount -o ro,loop disk.dd /mnt                   # if a real filesystem
strings -n 10 disk.dd | grep -i flag            # fastest first try

# volatility3
vol -f mem.raw windows.info                     # identify the image
vol -f mem.raw windows.pslist                   # running processes
vol -f mem.raw windows.cmdline                  # command lines — often the flag
vol -f mem.raw windows.filescan | grep -i flag
vol -f mem.raw windows.hashdump                 # NTLM hashes -> hashcat
vol -f mem.raw windows.dumpfiles --pid 1234
vol -f mem.raw linux.bash                       # bash history (linux)
```

---

## 6. STEGANOGRAPHY

| Tool | Use case |
|---|---|
| `zsteg` | PNG/BMP LSB. First thing to run on a PNG. |
| `steghide` | JPG/BMP/WAV with a passphrase. |
| `stegseek` | Cracks steghide passphrases at ~millions/sec. |
| `exiftool` | Metadata comments. |
| `tesseract` | OCR — read text out of an image. |
| `convert` | ImageMagick — flip planes, adjust levels to reveal hidden text. |

```bash
zsteg -a image.png                              # try ALL LSB combos
zsteg -E 'b1,rgb,lsb,xy' image.png > out.bin    # extract a specific one
steghide info file.jpg
steghide extract -sf file.jpg -p ''             # empty password first
stegseek file.jpg /opt/SecLists/Passwords/Leaked-Databases/rockyou.txt
exiftool -all image.png
tesseract image.png stdout                      # OCR
convert image.png -separate channel_%d.png      # split RGB planes
convert image.png -auto-level -contrast-stretch 0 out.png

# audio stego -> look at the spectrogram in Audacity, flags get drawn in it
# PNG that won't open: check the IHDR dimensions, they're often corrupted on purpose
```

---

## 7. PASSWORD CRACKING

| Tool | Use case |
|---|---|
| `john` | Anything with a `*2john` converter: zip, rar, pdf, ssh, keepass, office. |
| `hashcat` | Raw hashes, GPU-fast. Better for md5/sha/NTLM at volume. |
| `fcrackzip` | Quick zip brute force without the john dance. |
| `pdfcrack` | PDF passwords. |

```bash
# the *2john family turns a file into a crackable hash
zip2john secret.zip > h.txt
ssh2john id_rsa > h.txt
pdf2john file.pdf > h.txt
rar2john a.rar > h.txt
office2john doc.docx > h.txt
keepass2john db.kdbx > h.txt

john h.txt --wordlist=/opt/SecLists/Passwords/Leaked-Databases/rockyou.txt
john h.txt --show                               # show cracked results
john h.txt --format=raw-md5 --wordlist=W
john h.txt --incremental                        # pure brute force, last resort

# rules — catch Password1, P@ssword, password2024
john h.txt --wordlist=W --rules=Jumbo

hashcat -m 0 hash.txt rockyou.txt               # 0=MD5 100=SHA1 1400=SHA256
hashcat -m 1000 ntlm.txt rockyou.txt            # 1000=NTLM 1800=sha512crypt
hashcat -m 0 -a 3 hash.txt '?l?l?l?l?d?d'       # mask: 4 lower + 2 digits
hashcat --identify hash.txt                     # what mode is this?
hashcat -m 0 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule

fcrackzip -u -D -p rockyou.txt secret.zip       # -u verifies, -D dictionary
pdfcrack -f file.pdf -w rockyou.txt
```
**Wordlist note:** rockyou ships compressed. Extract it once:
`sudo tar -xzf /opt/SecLists/Passwords/Leaked-Databases/rockyou.txt.tar.gz -C /opt/SecLists/Passwords/Leaked-Databases/`
The `rockyou-NN.txt` files already present are truncated-by-length subsets (NN = max password length) —
`rockyou-15.txt` is a fast first pass, full `rockyou.txt` when that misses.

---

## 8. REVERSE ENGINEERING — Wave 2–3

| Tool | Use case |
|---|---|
| `ghidra` | Decompiles to readable C. Your primary RE tool. |
| `radare2` | Fast look, byte patching, binary diffing. |
| `gdb`+`pwndbg` | Dynamic — watch it run, inspect memory at a breakpoint. |
| `ltrace` | Library calls. Catches `strcmp(input, "password")` instantly. |
| `strace` | Syscalls. Shows what files it opens. |

```bash
# before anything else
file chal; checksec chal         # (pwn checksec chal — pwntools provides it)
strings chal | grep -iE 'flag|pass|key'
ltrace ./chal                    # often reveals the comparison outright
strace -f ./chal 2>&1 | grep -E 'open|read'

# ghidra: ghidraRun -> new project -> import -> double-click -> auto-analyze
#   then navigate to main in the Symbol Tree, read the Decompile pane.
#   rename variables as you understand them (L key) — makes the C readable fast.

# radare2
r2 -A chal                       # open + analyze
  aaa                            # deeper analysis
  afl                            # list functions
  s main; pdf                    # seek to main, disassemble function
  pdc                            # pseudo-decompile
  iz                             # strings in data section
  / flag                         # search for "flag"
  VV                             # visual graph mode
  q                              # quit
r2 -w chal                       # WRITE mode for patching
  s 0x401234; wa jmp 0x401250    # assemble a patch at an address
  wx 9090                        # write raw bytes (NOP NOP)

# gdb + pwndbg
gdb ./chal
  b main / b *0x401234           # breakpoint
  r / c / ni / si                # run, continue, next, step
  x/20gx $rsp                    # examine 20 giant hex at rsp
  x/s 0x404040                   # examine as string
  telescope $rsp 20              # pwndbg: smart stack view
  vmmap                          # memory map
  checksec                       # protections
  cyclic 100 / cyclic -l 0x6161  # pwndbg: offset finding
```

**Other languages:** Python `.pyc` → `pip install uncompyle6` or `decompyle3`.
Go/Rust binaries are huge — go straight to strings and the symbol table.
Java `.jar`/`.class` → `jadx` or `cfr`. Android `.apk` → `apktool d` then `jadx`.

---

## 9. BINARY EXPLOITATION — Wave 3

| Tool | Use case |
|---|---|
| `pwntools` | Write the exploit. Process/remote I/O, packing, ROP, shellcode. |
| `ROPgadget` | Find gadgets for a ROP chain. |
| `one_gadget` | Find a one-shot `execve("/bin/sh")` inside libc. |
| `qemu-user-static` | Run an ARM/MIPS challenge binary on x86. |
| `pwn checksec` | Which protections are on — decides your whole approach. |

```bash
pwn checksec ./chal              # NX? PIE? Canary? RELRO?
ROPgadget --binary chal --ropchain
ROPgadget --binary chal --only 'pop|ret'
one_gadget /lib/x86_64-linux-gnu/libc.so.6
pwn cyclic 200                   # pattern to find the offset
pwn cyclic -l 0x6161616c         # look up offset from crash value
pwn template ./chal              # GENERATE AN EXPLOIT SKELETON — use this
```

**Exploit skeleton:**
```python
from pwn import *
context.binary = e = ELF('./chal')          # sets arch/bits automatically
context.log_level = 'debug'                 # see everything on the wire

# io = process('./chal')
# io = gdb.debug('./chal', 'b *main+40\nc')  # launch under gdb
io = remote('host', 1337)

io.recvuntil(b'name: ')
payload  = b'A' * 72                        # offset from cyclic
payload += p64(e.sym['win'])                # or a ROP chain
io.sendline(payload)
io.interactive()                            # drop to the shell
```

**Protection → technique:**
| Seen | Do |
|---|---|
| No canary, NX off | Shellcode on the stack |
| No canary, NX on | ret2win, ret2libc, or ROP |
| Canary on | Leak the canary first (format string / partial overwrite) |
| PIE on | Leak a code address to rebase everything |
| Full RELRO | No GOT overwrite — use ROP |

**Format string:** `%p %p %p` to leak the stack, `%7$s` to read an arg, `%n` to write.
`fmtstr_payload(offset, {addr: value})` in pwntools builds it for you.

**Non-x86 binary:**
```bash
file chal                                    # "ARM aarch64"
qemu-aarch64-static ./chal                   # run it directly
qemu-aarch64-static -g 1234 ./chal           # then gdb-multiarch, target remote :1234
docker run --rm -it --platform linux/arm64 -v "$PWD:/w" -w /w ubuntu:22.04 ./chal
```

---

## 10. DOCKER — your sandbox

```bash
# run an untrusted binary, with ptrace so gdb works inside
docker run --rm -it --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
  -v "$PWD:/w" -w /w ubuntu:22.04 bash

# match the challenge's libc — check which Ubuntu it was built on
docker run --rm -it -v "$PWD:/w" -w /w ubuntu:20.04 ./chal    # glibc 2.31
docker run --rm -it -v "$PWD:/w" -w /w ubuntu:22.04 ./chal    # glibc 2.35
docker run --rm -it -v "$PWD:/w" -w /w ubuntu:24.04 ./chal    # glibc 2.39

# a web challenge that ships its own compose file
docker compose up -d && docker compose logs -f

# no network at all (truly untrusted sample)
docker run --rm -it --network none -v "$PWD:/w" -w /w ubuntu:22.04 bash

# pull these BEFORE the event — you may have no bandwidth on the day
docker pull ubuntu:20.04; docker pull ubuntu:22.04; docker pull ubuntu:24.04
```

---

## 11. TERMINAL SCRIPTING — the glue

### Flag hunting
```bash
grep -rao 'flag{[^}]*}' .                   # recursive, binary-safe, only the match
grep -raoiE '(flag|ctf|pes|layer8)\{[^}]{4,}\}' .
grep -rail flag . | head                     # which FILES mention it
strings -a file | grep -iE 'flag|key|secret'

# a reusable function — put this in ~/.zshrc
flag() { grep -raoiE '[a-z0-9_]{2,10}\{[^}]{3,60}\}' "${1:-.}" 2>/dev/null | sort -u; }
```

### Loops
```bash
for f in *.pcap; do echo "== $f"; tshark -r "$f" -q -z io,phs; done
for i in $(seq 1 100); do curl -s "http://t/?id=$i" | grep -o 'flag{.*}'; done
for k in {0..255}; do python3 -c "
import sys; k=$k
d=bytes(b^k for b in open('ct.bin','rb').read())
if b'flag' in d: print(k, d)"; done

# while-read over a list (handles spaces correctly)
while IFS= read -r line; do echo "trying $line"; done < wordlist.txt

# C-style
for ((i=0; i<10; i++)); do echo $i; done
```

### Parallelism — matters when you're racing
```bash
# xargs: -P parallel jobs, -n args per job, -I placeholder
cat urls.txt | xargs -P 20 -I{} curl -s -o /dev/null -w '%{http_code} {}\n' {}
ls *.bin | xargs -P 8 -I{} binwalk -e {}
seq 1 1000 | xargs -P 50 -I{} sh -c 'curl -s "http://t/?id={}" | grep -q flag && echo {}'

# background jobs + wait
for h in host1 host2 host3; do nmap -p- "$h" > "$h.txt" & done; wait
```

### Pipes & redirection
```bash
cmd 2>&1 | less                  # merge stderr into stdout
cmd > out.txt 2> err.txt         # split them
cmd &> all.txt                   # both to one file
cmd | tee out.txt                # see it AND save it
cmd < input.txt                  # stdin from file
diff <(cmd1) <(cmd2)             # process substitution — compare two outputs
cmd <<< "literal string"         # here-string as stdin
```

### Text wrangling
```bash
cut -d: -f1 /etc/passwd          # field 1, colon-delimited
awk '{print $2}' file            # column 2
awk -F: '$3>1000 {print $1}' /etc/passwd    # filter then print
sed -n '10,20p' file             # lines 10-20
sed 's/old/new/g' file           # substitute
sort -u / sort -n / sort -k2     # unique / numeric / by column 2
uniq -c | sort -rn               # frequency count, descending — great for crypto
tr -d '\n' / tr 'a-z' 'A-Z'      # delete / translate
rev                              # reverse each line
head -c 100 / tail -c +9         # first 100 bytes / from byte 9 onward
wc -l / wc -c                    # count lines / bytes
paste -sd+ | bc                  # sum a column of numbers
```

### Network interaction
```bash
nc host 1337                                 # connect to a challenge
nc -lvnp 4444                                # listen for a reverse shell
echo 'payload' | nc host 1337                # one-shot send
printf 'A%.0s' {1..100} | nc host 1337       # send 100 A's
python3 -c "print('A'*100)" | nc host 1337   # build then pipe

socat - TCP:host:1337                        # nc alternative, better with TTYs
socat TCP-LISTEN:4444,reuseaddr,fork EXEC:/bin/bash

# keep stdin open after sending (needed for interactive challenges)
cat <(echo payload) - | nc host 1337
# but really: use pwntools remote() for anything interactive
```

### Encoding one-liners
```bash
echo -n 'text' | base64                      # encode
echo 'dGV4dA==' | base64 -d                  # decode
echo -n 'text' | xxd -p                       # to hex
echo '74657874' | xxd -r -p                   # from hex
echo -n 'text' | md5sum / sha256sum
echo 'text' | tr 'A-Za-z' 'N-ZA-Mn-za-m'      # ROT13
python3 -c "import urllib.parse as u; print(u.unquote('%41%42'))"
python3 -c "print(int('ff',16), hex(255), bin(5))"
```

### Useful zsh/bash bits
```bash
!!                               # last command
sudo !!                          # rerun it with sudo
$(!!)                            # use its output
!$                               # last arg of previous command
Ctrl-R                           # search history
cd -                             # previous directory
mkdir -p a/b/c && cd $_          # $_ = last arg
{a,b,c}.txt                      # brace expansion -> a.txt b.txt c.txt
**/*.png                         # recursive glob
ls | wc -l                       # count files
du -sh * | sort -rh | head       # biggest things here
```

### A triage script worth keeping
```bash
cat > ~/bin/triage <<'EOS'
#!/usr/bin/env bash
# triage <file> — first pass on any CTF artifact
f="$1"; [ -f "$f" ] || { echo "usage: triage <file>"; exit 1; }
echo "=== file ==="  ; file "$f"
echo "=== size ==="  ; du -h "$f"
echo "=== magic ===" ; xxd "$f" | head -3
echo "=== flags ===" ; grep -aoiE '[a-z0-9_]{2,10}\{[^}]{3,60}\}' "$f" | sort -u | head
echo "=== strings ==="; strings -n 8 "$f" | head -40
echo "=== meta ==="  ; exiftool "$f" 2>/dev/null | head -20
echo "=== embedded ==="; binwalk "$f" 2>/dev/null | head -20
case "$(file -b "$f")" in
  *ELF*) echo "=== checksec ==="; pwn checksec "$f" 2>/dev/null ;;
  *PNG*) echo "=== zsteg ==="; zsteg -a "$f" 2>/dev/null | head -20 ;;
  *pcap*) echo "=== protocols ==="; tshark -r "$f" -q -z io,phs 2>/dev/null ;;
esac
EOS
chmod +x ~/bin/triage
```
Then `triage mystery.bin` on anything new. (`mkdir -p ~/bin` first; add to PATH if needed.)

---

## 12. WORKFLOW REMINDERS

**Order of operations on any file:** `file` → `strings | grep flag` → `exiftool` → `binwalk`
→ category-specific tool. The lazy check finds the flag more often than it has any right to.

**Before the event:**
```bash
source ~/ctf-venv/bin/activate                # muscle memory
docker pull ubuntu:20.04 ubuntu:22.04         # no bandwidth on the day
sudo tar -xzf /opt/SecLists/Passwords/Leaked-Databases/rockyou.txt.tar.gz \
  -C /opt/SecLists/Passwords/Leaked-Databases/   # ships as tar.gz, extract ONCE before the event
ghidraRun                                     # first launch is slow, do it now
```

**During:** one directory per challenge, `notes.md` in each, write the flag down the moment
you get it. Four waves means time pressure — if a challenge stalls for 20 minutes, switch
and come back.
