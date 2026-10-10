"""Black-box oracle for phantom's VM transform.
Pokes 36 arbitrary bytes into the VM's input buffer (bypassing main's charset
filter) and reads back T(input) and the expected target."""
import subprocess, re, sys
W = '/home/shadow_e15/.claude/jobs/2e16e2cb/tmp'

GDB_HEAD = """set confirm off
set pagination off
set height 0
starti < {W}/in.txt
set $bb = $pc - 0x9840
break *($bb + 0x9bf0)
continue
"""

def build(poke, which=1):
    s = GDB_HEAD.format(W=W)
    for _ in range(which - 1):           # skip to the Nth VM call
        s += "continue\n"
    for i, v in enumerate(poke):
        s += f"set *(unsigned char*)($rdx+{i}) = {v}\n"
    s += f"""delete 1
break *($bb + 0xafd2)
continue
printf "T:"
set $i = 0
while $i < 36
  printf "%02x", *(unsigned char*)($rsp+0x140+$i)
  set $i = $i + 1
end
printf "\\nG:"
set $i = 0
while $i < 36
  printf "%02x", *(unsigned char*)($rsp+0x170+$i)
  set $i = $i + 1
end
printf "\\n"
kill
quit
"""
    return s

def T(poke, which=1):
    assert len(poke) == 36
    open(f'{W}/in.txt', 'w').write('isfcr{' + 'a' * 36 + '}\n')
    open(f'{W}/poke.gdb', 'w').write(build(poke, which))
    out = subprocess.run(['gdb', '-q', '-nx', '-batch', '-x', f'{W}/poke.gdb', './phantom'],
                         cwd=f'{W}/run', capture_output=True, text=True, timeout=180).stdout
    t = re.search(r'^T:([0-9a-f]{72})$', out, re.M)
    g = re.search(r'^G:([0-9a-f]{72})$', out, re.M)
    if not (t and g):
        sys.exit('oracle failed:\n' + out[-3000:])
    return bytes.fromhex(t.group(1)), bytes.fromhex(g.group(1))

if __name__ == '__main__':
    import os
    z = bytes(36)
    Tz, G = T(z)
    print('G      =', G.hex())
    print('T(0)   =', Tz.hex())
    x = bytes(range(1, 37))
    y = bytes([(i * 7 + 3) & 0xff for i in range(36)])
    Tx, _ = T(x); Ty, _ = T(y)
    Txy, _ = T(bytes(a ^ b for a, b in zip(x, y)))
    lhs = bytes(a ^ b for a, b in zip(Txy, Tz))
    rhs = bytes(a ^ b ^ c ^ d for a, b, c, d in zip(Tx, Tz, Ty, Tz))
    print('T(x)   =', Tx.hex())
    print('T(y)   =', Ty.hex())
    print('T(x^y) =', Txy.hex())
    print('GF(2)-affine?', 'YES' if lhs == rhs else 'no')
