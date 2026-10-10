#!/usr/bin/env python3
"""phantom: prove what the gate at 0xb220 actually demands.

The gate is NOT `A[0] AND A[1]`. It derives two table indices from a fixed
rol/xor chain; the chain evaluates to r14 = 0x54231e21, so the indices are
(r14+9)&0xf = 10 and (r14+10)&0xf = 11.

Both programs are bijections over the 36-byte body (every opcode is
invertible -- the two multiply opcodes force an odd multiplier, verified in
the real handlers at 0xa7e2 and 0xabe6), and op 0x16 is a full 36-byte
equality (`sete` on the OR of all 36 byte differences, 0xb0c7). So each
program accepts exactly one body, and the gate ANDs two different ones.

Run with --verify to check both verdicts against the real binary via gdb.
"""
import subprocess
import sys

M32 = 0xffffffff
ROL = lambda v, c: (((v << (c & 31)) | ((v & M32) >> (32 - (c & 31)))) & M32) if c & 31 else v & M32

# the chain at 0xb22b..0xb2be: rol(imm,3) then six (sub, xor, rol) rounds
CHAIN = [(0xfc4286ce, 4), (0xd9271e3b, 5), (0x8d5518d9, 6),
         (0xb578a89b, 7), (0x72da0360, 8), (0x351626cc, 9)]


def gate_indices():
    x = ROL(0xf1a8039c, 3)
    for xor_const, rot in CHAIN:
        x = ROL(((x - 0x61c88647) & M32) ^ xor_const, rot)
    return (x + 9) & 0xf, (x + 10) & 0xf, x


# the two bodies, recovered by inverting each program's trace from its target
BODIES = {
    10: 'gr347_by73c0d3_w0rk_bu7_7h1s_1s_f4k3',
    11: 'gr347_by73c0d3_w0rk_4nd_7h1s_1s_f4k3',
}

GDB = r'''
import gdb
gdb.execute('set confirm off'); gdb.execute('set pagination off')
gdb.execute('file {binary}')
gdb.execute('starti < {infile}')
out = gdb.execute('info proc mappings', to_string=True)
base = int([l for l in out.splitlines() if {name!r} in l][0].split()[0], 16)
gdb.execute('break *%#x' % (base + 0xb2d0))   # idx0 in eax, idx1 in r14d
gdb.execute('break *%#x' % (base + 0xb2f3))   # result0 in eax
gdb.execute('break *%#x' % (base + 0xb30b))   # result1 in eax
gdb.execute('continue')
i0 = int(gdb.parse_and_eval('$eax')) & 0xf
i1 = int(gdb.parse_and_eval('$r14d')) & 0xf
gdb.execute('continue'); r0 = int(gdb.parse_and_eval('$eax')) & 0xff
gdb.execute('continue'); r1 = int(gdb.parse_and_eval('$eax')) & 0xff
print('RESULT idx0=%d idx1=%d result0=%d result1=%d' % (i0, i1, r0, r1))
'''


def verify(binary='phantom'):
    for idx, body in sorted(BODIES.items()):
        with open('/tmp/phantom_in.txt', 'w') as f:
            f.write('isfcr{%s}\n' % body)
        with open('/tmp/phantom_gdb.py', 'w') as f:
            f.write(GDB.format(binary=binary, infile='/tmp/phantom_in.txt',
                               name=__import__('os').path.basename(binary)))
        p = subprocess.run(['gdb', '-q', '-batch', '-x', '/tmp/phantom_gdb.py'],
                           capture_output=True, text=True)
        line = next((l for l in p.stdout.splitlines() if l.startswith('RESULT')), '(no result)')
        print(f'  body accepted by program {idx}: {line}')


if __name__ == '__main__':
    i0, i1, r14 = gate_indices()
    print(f'rol/xor chain -> r14 = {r14:#010x}')
    print(f'gate runs VM program A[{i0}] AND A[{i1}]   (NOT A[0] and A[1])')
    for idx, body in sorted(BODIES.items()):
        print(f'  A[{idx}] accepts exactly: isfcr{{{body}}}')
    print('\nThe two bodies differ at offsets 20-22 ("bu7" vs "4nd"), so the AND')
    print('is unsatisfiable: no input can make 0xb220 return 1.')
    if '--verify' in sys.argv:
        print('\nverifying against the real binary:')
        verify(sys.argv[sys.argv.index('--verify') + 1]
               if len(sys.argv) > sys.argv.index('--verify') + 1 else 'phantom')
