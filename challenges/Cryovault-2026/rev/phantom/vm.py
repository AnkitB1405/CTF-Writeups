"""Emulator for phantom's bytecode VM, recovered from the handlers at 0xa6f8..0xb1c6.

Per-instruction derived operands (computed by the dispatcher at 0xa5e5):
  i    = (R0 + 3*R1 + a) % 36              operand index
  j    = (R0 + 3*R1 + b) % 36, bumped by 1 if it collides with i
  rot  = ((R1 + c) % 7) + 1                rotate amount, always 1..7
  k32  = 17*R0 + R1 + R2 + imm             per-instruction key
"""
M8, M32 = 0xff, 0xffffffff
rol8  = lambda v, n: ((v << (n & 7)) | (v >> (8 - (n & 7)))) & M8 if n & 7 else v & M8
ror8  = lambda v, n: rol8(v, 8 - (n & 7)) if n & 7 else v & M8
rol32 = lambda v, n: ((v << (n & 31)) | (v >> (32 - (n & 31)))) & M32 if n & 31 else v & M32

class VM:
    def __init__(self, bytecode, ks, target):
        self.code = [tuple(bytecode[o:o+4]) + (int.from_bytes(bytecode[o+4:o+8], 'little'),)
                     for o in range(0, len(bytecode), 8)]
        self.S = list(ks[:256])                                   # substitution table
        self.perm = [list(ks[256 + 36*p: 256 + 36*(p+1)]) for p in range(4)]
        self.target = list(target)

    def run(self, data, trace=None):
        D, R, stk, pc = list(data), [0]*8, [], 0
        verdict = did_cmp = False
        steps = 0
        while pc < len(self.code):
            steps += 1
            if steps > 2000: raise RuntimeError('step limit')
            op, a, b, c, imm = self.code[pc]
            # 64-bit: lea (%r15,%r15,2),%r9 / add %r14,%r9 never truncates to 32,
            # and 3*R1 can carry past 2**32 — masking here shifts every index by -4
            base = R[0] + 3*R[1]
            i = (base + a) % 36
            j = (base + b) % 36
            if j == i: j = (j + 1) % 36
            rot = ((R[1] + c) % 7) + 1
            k32 = (17*R[0] + R[1] + R[2] + imm) & M32
            k = k32 & M8
            pc += 1
            r = a & 7
            if trace is not None: trace.append((pc-1, op, a, b, c, imm, i, j, rot, k32, R[1], bytes(D)))

            if   op == 0x00: R[r] = imm
            elif op == 0x01: R[r] = (R[r] + imm) & M32
            elif op == 0x02: R[r] ^= imm
            elif op == 0x03: R[r] = rol32(R[r], c)
            elif op == 0x04: stk.append(R[r])
            elif op == 0x05: R[r] = stk.pop()
            elif op == 0x06:
                if R[r] != 0: pc = imm
            elif op == 0x07: D[i] ^= k
            elif op == 0x08: D[i] = (D[i] + k) & M8
            elif op == 0x09: D[i] = rol8(D[i], rot)
            elif op == 0x0a: D[i] = self.S[(k + D[i]) & M8] ^ b
            elif op == 0x0b: D[i], D[j] = D[j], D[i]
            elif op == 0x0c: D[i] = D[i] ^ k ^ rol8(D[j], rot)
            elif op == 0x0d: D[i] = (D[i] + (k ^ rol8(D[j], rot))) & M8
            elif op == 0x0e: D[i] = (D[i] * (k | 1)) & M8
            elif op == 0x0f:
                p, out = self.perm[a & 3], [0]*36
                for t in range(36): out[p[t]] = D[t]
                D = out
            elif op == 0x10:
                out = D[18:36] + [0]*18
                mul = b | 1
                for t in range(18):
                    v  = ((imm >> ((8*t) & 0x18)) + 0x1d*t) & M8
                    v ^= self.S[(D[18+t] + k32 + t) & M8]
                    v ^= rol8(D[(18+t) + (5 if t < 13 else -13)], rot)
                    v ^= (D[(18+t) + (11 if t < 7 else -7)] * mul) & M8
                    v ^= D[t]
                    out[18+t] = v & M8
                D = out
            elif op == 0x11:
                out = list(D)
                for g in range(6):
                    s = (R[1] + c + g) % 6
                    for m in range(6): out[6*g + (s + m) % 6] = D[6*g + m]
                D = out
            elif op == 0x12:
                for t in range(36):
                    D[t] = rol8((D[t] * (((k + 2*t) & M8) | 1) + b + 7*t) & M8, rot)
            elif op == 0x13: D = D[::-1]
            elif op == 0x14:
                for t in range(18):
                    D[2*t]   = self.S[((k + 0x16*t) & M8) ^ D[2*t]]
                    D[2*t+1] = self.S[((k + 0x16*t + 0xb) & M8) ^ D[2*t+1]]
            elif op == 0x15:
                # the loop re-enters at 0xab57, so the carry is rotated once per
                # iteration, not just at the start
                carry, t = D[0], 0
                while True:
                    carry = rol8(carry, rot)
                    v = ((((k32 + 1 + t) & M8) ^ carry) + D[1+t]) & M8
                    D[1+t] = v
                    if t == 34: break
                    carry = ((((k32 + 2 + t) & M8) ^ rol8(v, rot)) + D[2+t]) & M8
                    D[2+t] = carry
                    t += 2
            elif op == 0x16:
                did_cmp = True
                verdict = (D == self.target)
            elif op == 0x17:
                return D, (verdict and did_cmp)
            else: raise RuntimeError(f'unknown op {op:#x}')
        return D, False
