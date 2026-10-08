# Scripts

Five CTF helpers in [`bin/`](../bin/). Python 3 stdlib only, so they run without the venv
activated — `pcaptri` is the one exception, since it shells out to `tshark`.

Every script carries `--selftest`, which asserts against known-answer vectors. If you change
one, run that first; it is faster than finding out mid-challenge that your tool lies to you.

```bash
for s in decode xorbrute flaggrep binfirst pcaptri; do ~/Cryovault/bin/$s --selftest; done
```

| Script | One line |
|---|---|
| [`decode`](#decode) | Throw a blob at every common encoding, print what comes out readable |
| [`pcaptri`](#pcaptri) | Triage a pcap: protocol mix, talkers, carved files, decoded payloads, flags |
| [`binfirst`](#binfirst) | One-screen static first pass on a binary, with the imports annotated |
| [`xorbrute`](#xorbrute) | Recover XOR data: single byte, short repeating key, or from a crib |
| [`flaggrep`](#flaggrep) | Find flag-shaped strings anywhere, including base64/hex-wrapped |

---

## A design decision shared by all five: two flag regexes

Every script needs to recognise a flag, and the obvious pattern is wrong:

```python
re.compile(rb'[A-Za-z0-9_]{2,12}\{[^}]{3,80}\}')     # too loose
```

The problem shows up the moment you brute-force anything. `rot13` of `flag{hello}` is
`synt{uryyb}`, which still matches. XOR noise throws up `Cl_{bCPeeSoHOseLeHA}`, which also
matches. Run a 256-key search and every single candidate gets marked as a flag — the marker
becomes worthless.

So the scripts keep two:

```python
STRICT = re.compile(rb'(?i)\b(flag|ctf|pico|htb|thm|pes|layer8|cryovault|key|secret)'
                    rb'\{[\x20-\x7e]{3,80}\}')
LOOSE  = re.compile(rb'\b[A-Za-z][A-Za-z0-9_]{1,15}\{[\x20-\x7e]{3,80}\}')
```

`STRICT` requires a recognised prefix and is the only thing that earns a `<<< FLAG` marker.
`LOOSE` still nudges ranking, so a competition using an unfamiliar prefix floats to the top
instead of being invisible. `[\x20-\x7e]` for the body rather than `[^}]` keeps control
characters out. Add a prefix with `flaggrep -p cryovault`, or `-a` to match any `word{...}`.

---

## decode

Takes a blob and tries every common encoding, printing whatever comes out printable.

```bash
decode 'ZmxhZ3toaX0='          # literal argument
decode -f blob.txt             # from a file
cat blob | decode              # from stdin
decode -d 3 'Vm0...'           # recurse up to 3 layers
decode -a 'blob'               # show everything, including non-printable results
```

**Where you'd use it:** any "here is a string" misc or crypto challenge, a suspicious cookie,
a JWT segment, a blob pulled out of a pcap. It is the thing to run before thinking.

### How it works

Each codec is a small function that either returns bytes or raises; `attempts()` runs them all
and yields whatever didn't raise. Being permissive matters more than being correct:

```python
def _b64(s: bytes) -> bytes:
    s = re.sub(rb'[^A-Za-z0-9+/=_-]', b'', s)        # strip newlines, quotes, spaces
    s = s.replace(b'-', b'+').replace(b'_', b'/')     # accept the url-safe alphabet
    s += b'=' * (-len(s) % 4)                          # restore stripped padding
    return base64.b64decode(s, validate=False)
```

Three separate things that break a naive `base64.b64decode`, all common in real challenges:
padding stripped off, the url-safe alphabet, and whitespace from a copy-paste.

**The important structural choice** is splitting codecs into two groups:

```python
NESTABLE = [('base64', _b64), ('base32', _b32), ('hex', _hex), ...]   # recurse into these

def terminals(data, show_all):      # never recursed into
    yield 'reversed', data[::-1]
    ...rot1..rot25
```

Substitution ciphers and reversal are *terminal*. Reversing printable text always yields
printable text, and rotating it always yields something flag-shaped, so recursing into them
produces an exponential pile of garbage. The first version of this script printed 26 fake
flags for one real one.

The second guard is in `walk()`:

```python
hits = [(n, o) for n, o in results if STRICT.search(o)]
if hits:                                   # a flag here: show only these, stop
    for n, o in hits:
        render(n, o, depth, True)
    return True
```

Once a node yields a flag, print it and **stop expanding that node**. Without this, finding
`flag{hello}` immediately produces 25 rotations of it, each still regex-flag-shaped.

`seen` is a set of every intermediate result, which stops the cycle `reversed → reversed` and
any codec pair that round-trips.

---

## pcaptri

Runs the standard pcap triage in one shot and hunts flags through every layer.

```bash
pcaptri cap.pcap
pcaptri cap.pcap -o out/        # carve objects into out/ (default ./carved)
pcaptri cap.pcap --no-carve     # report only
pcaptri cap.pcap -n 20          # more rows per section
```

**Where you'd use it:** the first thing to run on any network-forensics challenge. Needs
`tshark`.

### How it works

A thin wrapper around tshark — the value is the ordering and the flag hunt, not the parsing.

```python
def tshark(args: list[str], pcap: str) -> str:
    r = subprocess.run(['tshark', '-r', pcap] + args, capture_output=True, text=True,
                       errors='replace', timeout=300)
    return r.stdout.rstrip()
```

`errors='replace'` because pcap payloads are not valid UTF-8 and a decode error should not kill
the run. `timeout` because a large capture with a bad filter can hang.

**Protocol hierarchy prints first, deliberately.** A capture that is 90% DNS is a different
problem from one that is 90% HTTP, and that one section tells you which of the others is worth
reading.

The flag hunt runs at four levels, because a flag can hide at any of them:

1. **Carved objects** — `--export-objects http,dir` reconstructs transferred files
2. **Per-packet payloads** — `-e tcp.payload` as hex, converted back to bytes
3. **The raw pcap file** — catches anything the dissectors failed to reassemble
4. **DNS label reassembly** — see below

Everything goes through one function, which also tries base64 at each level:

```python
def flags_in(data: bytes, where: str, found: dict) -> None:
    for m in STRICT.finditer(data):
        found.setdefault(m.group(), set()).add(where)
    for m in re.finditer(rb'[A-Za-z0-9+/]{16,}={0,2}', data):   # any base64-looking run
        ...
```

Results are keyed by flag with a *set* of locations, so the same flag found in the raw bytes,
the payload and a carved file reports once with all three sources — which is also a useful
signal that you have the real thing.

### The DNS exfiltration case

Data smuggled out through DNS goes one label at a time: `ZmxhZ3.evil.com`, `tkbnNf.evil.com`.
No single packet contains anything. The leftmost labels, concatenated **in capture order**,
are the payload:

```python
order = [l.strip() for l in dns.splitlines() if l.strip()]   # capture order, not sorted
labels, seen = [], set()
for n in order:
    first = n.split('.')[0]
    if first not in seen:
        seen.add(first); labels.append(first)
joined = ''.join(labels).encode()
for pad in range(4):                       # length may not be a multiple of 4
    chunk = joined[: len(joined) - pad]
    chunk += b'=' * (-len(chunk) % 4)
    flags_in(base64.b64decode(chunk, validate=False), 'dns labels (base64)', found)
```

Two details that matter. Capture order, not the sorted unique list used for display — sorting
scrambles the payload. And the `pad` loop, because a concatenation of labels rarely lands on a
multiple of 4; trying four truncations costs nothing and one of them is right.

---

## binfirst

Runs the 30-second static checks in one shot and, more usefully, **annotates the imports**.

```bash
binfirst ./chal
binfirst ./chal -s 60      # more strings
binfirst ./chal --raw      # full nm/strings output too
```

**Where you'd use it:** the moment a challenge hands you a binary, before opening Ghidra.

### How it works

The sections are `file`, size and sha256, protections, imports, local functions, interesting
strings, suggested next commands. Every external tool goes through one wrapper that never
raises:

```python
def run(cmd: list[str]) -> str:
    if not shutil.which(cmd[0]):
        return f'[{cmd[0]} not installed]'
    ...
```

A missing tool degrades one section instead of killing the script.

**`checksec` has a fallback** so the script works outside the venv. It prefers
`pwn checksec`, and parses `readelf` if pwntools isn't reachable:

```python
rel = ('Full RELRO' if 'BIND_NOW' in hdr else
       'Partial RELRO' if 'GNU_RELRO' in hdr else 'No RELRO')
```

**The annotated imports are the point of the script.** What a binary *imports* often tells you
more than its disassembly, so each tell maps a symbol to a conclusion:

```python
TELLS = [
    (r'^(strtoul|strtol|atoi|atol|sscanf)$',
     'input parsed as a NUMBER — a hex digest can never match'),
    (r'^(strcmp|strncmp|memcmp)$',
     'comparison is a LIBRARY CALL — break on it, read both args'),
    (r'^gets$', 'gets() — unbounded read, classic stack overflow'),
    ...
]
```

That first one is drawn straight from the
[heartbleed writeup](../challenges/picoCTF/heartbleed/README.md): `strtoul` in the imports
killed every md5/sha theory in one line, after 90 minutes of guessing. The script now says it
for you.

One real-world wrinkle: modern glibc exports `__isoc23_strtoul`, not `strtoul`, so the plain
pattern silently misses it. The prefix is stripped before matching:

```python
return sorted({re.sub(r'^__iso[a-z0-9]+_', '', s.split('@')[0]) for s in syms})
```

C++ symbols get demangled through `c++filt`, since a name like `decode_password(char*)` is
itself the finding — the password is computed at runtime, which is why `strings` never shows it.

The last section prints the commands to run next, with the `gdb -ex "b strcmp"` line appearing
only when a comparison function is actually imported.

---

## xorbrute

Three modes, because exhaustive search is only tractable for very short keys.

```bash
xorbrute -f blob.bin                 # single byte + repeating keys len 2-3
xorbrute -f blob.bin -k 4            # longer keys (slow)
xorbrute -f blob.bin -c 'flag{'      # crib: derive the key from known plaintext
xorbrute -f blob.bin -c 'flag{cri' -L 8   # crib with an assumed key length
echo -n 'deadbeef' | xorbrute --hex  # hex input
```

**Where you'd use it:** any crypto or RE challenge where data looks encrypted but no algorithm
is named. Single-byte XOR is the most common obfuscation in CTFs.

### How it works

**Single byte** is exhaustive — 256 keys, always worth doing, no cleverness needed.

**Repeating keys** brute-force the printable-ASCII keyspace, which is where the ceiling is:

```python
# ponytail: 95**n grows fast — len 3 is ~857k tries and fine, len 4 is ~81M and slow.
# Use a crib instead of raising -k past 4.
```

Length 3 runs in seconds; length 4 is 81 million candidates. That is the honest limit of brute
force, and the reason the third mode exists.

**The crib mode needs no search at all.** XOR is symmetric, so if you know any plaintext
fragment, XORing it against the ciphertext at the right offset *gives you the key*:

```python
frag = xor(data[off:off + len(crib)], crib)      # candidate key material
```

With an assumed key length, the fragment recovered at offset `o` fills key positions
`(o + i) mod keylen`:

```python
key = bytearray(keylen)
for i, b in enumerate(frag):
    key[(off + i) % keylen] = b
```

This has a hard constraint worth understanding: **one alignment only reveals `len(crib)` key
bytes.** A 5-character `flag{` cannot recover an 8-byte key. Rather than returning nothing and
letting you conclude the data isn't XORed, it says so:

```python
raise ValueError(
    f'crib is {len(crib)} bytes but key length {keylen} was assumed — '
    f'need a crib at least {keylen} bytes long, or drop -L')
```

Candidates are ranked by a letter-frequency score plus a large bonus for a `STRICT` flag match,
so the right answer lands first. The score is only for *ordering* — it never filters anything
out, because a flag is not English and would score badly.

---

## flaggrep

Recursive flag hunt that `grep` can't quite do.

```bash
flaggrep                        # current directory
flaggrep /path/to/chal          # a directory or a single file
flaggrep -p cryovault           # add a prefix
flaggrep -e                     # also find base64/hex-WRAPPED flags
flaggrep -u                     # UTF-16 too (Windows binaries)
flaggrep -a                      # any word{...}
```

**Where you'd use it:** after extracting anything — a carved pcap directory, a binwalk dump, a
mounted disk image. Also just run it on the challenge directory before doing real work.

### How it works

`grep -r` covers the easy case. Four things it doesn't:

**1. Encoded flags.** `flag{` stored as base64 is `ZmxhZ3s`, which no grep for "flag" will
find. The first implementation tried to compute what each prefix looks like encoded — wrong,
because base64 output depends on the plaintext's byte alignment, and that bug cost real time.
The working version ignores prefixes entirely and decodes everything that looks encoded:

```python
for m in re.finditer(rb'[A-Za-z0-9+/_-]{16,}={0,2}', data):
    blob = m.group().replace(b'-', b'+').replace(b'_', b'/')
    for off in range(4):                 # the run may not start on a 4-char boundary
        chunk = blob[off:]
        chunk = chunk[:len(chunk) // 4 * 4]
        dec = base64.b64decode(chunk, validate=False)
        out += [('base64', mm.group()) for mm in pat.finditer(dec)]
```

Fewer moving parts than the prefix maths, and it catches prefixes it was never told about.

**2. UTF-16.** Windows binaries store `flag` as `f\x00l\x00a\x00g\x00`. Taking every other
byte makes it searchable:

```python
for variant in (data[::2], data[1::2]):     # both phases, in case of an odd offset
```

**3. Binary safety and size.** Everything opens in binary mode — no encoding errors on a
`.bin`. A size cap stops the script from slurping a 10 GB disk image into RAM, and `.git`,
`node_modules` and `__pycache__` are skipped so a recursive run finishes.

**4. Deduplication.** Results are keyed by flag with a list of locations, so one flag appearing
in forty files is one line plus `(+39 more)`, not forty lines.

---

## Adding to these

Each script's `selftest()` is the contract. If you add a codec to `decode` or a tell to
`binfirst`, add the assertion in the same commit — the bugs these caught during writing (the
base64 alignment error, the `__isoc23_` prefix, the `group(2)` typo, an invalid test vector)
were all found by an assert, not by reading the code.
