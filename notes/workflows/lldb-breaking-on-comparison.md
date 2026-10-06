# LLDB — Breaking on the Comparison

| | |
|---|---|
| **Status** | 🟡 Learned the method, verify by doing |
| **First hit** | CyLab Academy — bypassme.bin |
| **Category** | Reverse Engineering / Dynamic Analysis |

## The core idea

Static analysis tells you what a program *can* do. A debugger lets you **watch it do it** — and
the single highest-value moment is the instant it compares your input against the real answer.

You do not guess the password. You **break on the comparison and read both arguments.**

## The workflow

```bash
lldb ./binary
br set -n strcmp      # break on the comparison function
run
```

Enter any input at the prompt. When it breaks:

```
x/s $rdi      # first argument
x/s $rsi      # second argument
```

One holds your (post-sanitization) input, the other holds the real value. That is the leak.

## Argument registers — x86-64 System V

| Arg # | Register |
|---|---|
| 1 | `rdi` |
| 2 | `rsi` |
| 3 | `rdx` |
| 4 | `rcx` |
| 5 | `r8` |
| 6 | `r9` |
| return | `rax` |

On ARM64 the same positions are `x0`–`x5`, return in `x0`.

## Useful commands

| Command | Does |
|---|---|
| `br set -n <func>` | Break on a named function |
| `br set -a <addr>` | Break on an address (for inline compares) |
| `br list` / `br del <n>` | Manage breakpoints |
| `x/s $reg` | Read as a C string |
| `x/32xb $reg` | 32 raw bytes — for non-printable data |
| `register read` | All registers |
| `disas -f` | Disassemble current frame |
| `disas -n <func>` | Disassemble a named function |
| `bt` | Backtrace — how you got here |
| `finish` | Run to end of frame, result lands in `rax` |
| `c` / `n` / `s` | Continue / step over / step into |

## When there is no comparison function to break on

If `nm -D` shows no `strcmp`/`memcmp`, the compare is **inline**. Disassemble and look for a
`cmp` or `test` followed by a conditional jump (`je`, `jne`, `jz`), then break on that address
with `br set -a`.

## Sanitization changes the target

If the program transforms input before comparing (`isalpha`, `tolower`, `strcspn` in the
imports), then `$rdi` at the breakpoint holds the **post-sanitization** form, not what you typed.

That is useful, not annoying: comparing what you typed against what arrives at `strcmp`
**reverse-engineers the transform for free.**

> The value you need to type is not necessarily the stored password — it is whatever string
> *survives sanitization and lands on* the stored password. Finding the stored string is only
> half the job.

Some binaries hand you this for nothing by echoing `Sanitized Input:[%s]` back — then the
transform can be mapped from outside the debugger entirely, by probing.

## Leak, do not patch

You *can* flip a conditional jump and fall into the success branch. Often it works.

But if the flag is **decrypted using** the password rather than merely gated behind it,
patching lands you in the win branch holding garbage. Leaking the password and running the
binary normally is cleaner and survives that case.

## Not learned yet

- [ ] Verify this workflow end-to-end on a real binary
- [ ] Watchpoints — breaking when a *variable* changes rather than on a function
- [ ] Scripting LLDB with Python for repeated runs
- [ ] Same workflow in `gdb` / pwndbg syntax
- [ ] `ltrace` — seeing library calls with arguments and no breakpoints at all
- [ ] Attaching to an already-running process

## gdb / pwndbg equivalents

This host has pwndbg, not lldb. Translation for the same workflow:

| LLDB | gdb + pwndbg |
|---|---|
| `br set -n strcmp` | `b strcmp` |
| `br set -a 0x401234` | `b *0x401234` |
| `x/s $rdi` | `x/s $rdi` (same) |
| `x/32xb $rdi` | `x/32xb $rdi` (same) |
| `register read` | `info registers` / `regs` |
| `disas -f` | `disassemble` / `pdisas` |
| `bt` | `bt` (same) |
