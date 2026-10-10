"""Recover phantom's flag body by running the VM's instruction trace backwards.

Every operand the VM derives (i, j, rot, k32, the group shifts) comes from the
register file, never from the input, so the trace is identical for every input.
The 36-byte transform is therefore a fixed composition of invertible byte
operations: record the trace once with a dummy input, then walk it in reverse
starting from the expected output."""
import re, sys
sys.path.insert(0, '/home/shadow_e15/.claude/jobs/2e16e2cb/tmp')
from vm import VM, rol8, ror8, M8

inv256 = lambda m: pow(m | 1, -1, 256)

def back(D, S, Sinv, perm, op, a, b, c, imm, i, j, rot, k32, R1):
    """Given the state AFTER one instruction, return the state before it."""
    k = k32 & M8
    if op <= 0x06: return D                                   # register / control only
    if   op == 0x07: D[i] ^= k
    elif op == 0x08: D[i] = (D[i] - k) & M8
    elif op == 0x09: D[i] = ror8(D[i], rot)
    elif op == 0x0a: D[i] = (Sinv[D[i] ^ b] - k) & M8
    elif op == 0x0b: D[i], D[j] = D[j], D[i]
    elif op == 0x0c: D[i] = D[i] ^ k ^ rol8(D[j], rot)        # j != i, so D[j] is intact
    elif op == 0x0d: D[i] = (D[i] - (k ^ rol8(D[j], rot))) & M8
    elif op == 0x0e: D[i] = (D[i] * inv256(k)) & M8
    elif op == 0x0f:
        p = perm[a & 3]; D = [D[p[t]] for t in range(36)]
    elif op == 0x10:
        old = [0]*36
        old[18:36] = D[0:18]                                  # upper half passed through
        mul = b | 1
        for t in range(18):
            v  = ((imm >> ((8*t) & 0x18)) + 0x1d*t) & M8
            v ^= S[(old[18+t] + k32 + t) & M8]
            v ^= rol8(old[(18+t) + (5 if t < 13 else -13)], rot)
            v ^= (old[(18+t) + (11 if t < 7 else -7)] * mul) & M8
            old[t] = D[18+t] ^ v
        D = old
    elif op == 0x11:
        out, D = D, [0]*36
        for g in range(6):
            s = (R1 + c + g) % 6
            for m in range(6): D[6*g + m] = out[6*g + (s + m) % 6]
    elif op == 0x12:
        for t in range(36):
            D[t] = (((ror8(D[t], rot) - b - 7*t) & M8) * inv256((k + 2*t) & M8)) & M8
    elif op == 0x13: D = D[::-1]
    elif op == 0x14:
        for t in range(18):
            D[2*t]   = Sinv[D[2*t]]   ^ ((k + 0x16*t) & M8)
            D[2*t+1] = Sinv[D[2*t+1]] ^ ((k + 0x16*t + 0xb) & M8)
    elif op == 0x15:
        new = list(D)
        carry, t = new[0], 0
        while True:
            carry = rol8(carry, rot)
            D[1+t] = (new[1+t] - ((((k32 + 1 + t) & M8) ^ carry))) & M8
            if t == 34: break
            carry = new[2+t]
            D[2+t] = (carry - ((((k32 + 2 + t) & M8) ^ rol8(new[1+t], rot)))) & M8
            t += 2
    else: raise RuntimeError(f'no inverse for op {op:#x}')
    return D

def solve(bc, ks, tgt):
    vm = VM(bc, ks, tgt)
    assert sorted(vm.S) == list(range(256)), 'S is not a permutation'
    Sinv = [0]*256
    for v, s in enumerate(vm.S): Sinv[s] = v

    trace = []
    vm.run(b'\x00'*36, trace=trace)
    cut = next(n for n, st in enumerate(trace) if st[1] == 0x16)   # state at the compare
    D = list(vm.target)
    for pc, op, a, b, c, imm, i, j, rot, k32, R1, _ in reversed(trace[:cut]):
        D = back(D, vm.S, Sinv, vm.perm, op, a, b, c, imm, i, j, rot, k32, R1)
    return bytes(D)

if __name__ == '__main__':
    t = open('/home/shadow_e15/.claude/jobs/2e16e2cb/tmp/tables.txt').read()
    g = lambda n: bytes.fromhex(re.search(rf'^{n}:([0-9a-f]+)$', t, re.M).group(1))
    for pre in ('CALL2', 'CALL1'):
        bc, ks, tgt = g(pre+'_BC'), g(pre+'_KS'), g(pre+'_TGT')
        try:
            body = solve(bc, ks, tgt)
        except Exception as e:
            print(f'{pre}: solve failed: {e!r}'); continue
        D, ok = VM(bc, ks, tgt).run(body)
        print(f'{pre}: body = {body!r}')
        print(f'       hex  = {body.hex()}')
        print(f'       forward-check: accepted={ok}')
        print(f'       charset ok = {all(chr(x) in "abcdefghijklmnopqrstuvwxyz0123456789_" for x in body)}')
