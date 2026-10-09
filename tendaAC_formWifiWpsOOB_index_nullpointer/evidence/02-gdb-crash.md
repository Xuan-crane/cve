# Evidence 02 — Debugger Capture

Two independent captures are recorded here. Both were obtained by launching the firmware's
`httpd` under QEMU's gdb stub and attaching `gdb-multiarch`:

```bash
# inside the emulation container
setsid qemu-arm -g 1234 -L ./ bin/httpd &

# on the host
gdb-multiarch -q -batch -x cmds.txt       # cmds.txt: target remote <host>:1234 ; continue
```

The QEMU stub reports the guest signal and the guest register state, so the faulting
instruction and the fault address are observed directly — not inferred.

---

## Capture A — POST without `index`

```
Program received signal SIGSEGV, Segmentation fault.
0x3fdedafc in ?? ()

r0             0x0                 0
r1             0x0                 0
r2             0x3fe0a4e8          1071686888
r3             0x1                 1
r12            0x3fe05704          1071666948
sp             0x408008c8          0x408008c8
lr             0x3fded8fc          1071569148
pc             0x3fdedafc          0x3fdedafc
cpsr           0x20000010          536870928

---- faulting instruction ----
   0x3fdedaf4:  b     0x3fdedafc
   0x3fdedaf8:  add   r6, r6, #1
=> 0x3fdedafc:  ldrb  r3, [r6]          ; <-- reads byte at [r6]
   0x3fdedb00:  ldr   r12, [r2]
   0x3fdedb04:  lsl   r1, r3, #1
   0x3fdedb08:  ldrh  r7, [r12, r1]

---- the pointer being dereferenced ----
p/x $r6
$1 = 0x0

x/4xb $r6
Cannot access memory at address 0x0     ; address 0 is unmapped
```

Reading the prologue of this function shows where `r6` came from:

```asm
0x3fdedae8:  mov  r10, r3
0x3fdedaec:  mov  r6, r0        ; scan pointer := first function argument
0x3fdedaf0:  ldr  r2, [sp, #48]
0x3fdedaf4:  b    0x3fdedafc
0x3fdedaf8:  add  r6, r6, #1    ; advance one character
0x3fdedafc:  ldrb r3, [r6]      ; fault
```

**The fault address is exactly `0x0`.** `r0` held `0`, the pointer was copied into the
scan register untouched, and the loop read from it.

---

## Capture B — GET without parameters (same fault)

```
GET /goform/WifiWpsOOB HTTP/1.1
Cookie: password=x

Program received signal SIGSEGV, Segmentation fault.
0x3fdedafc in ?? ()

r0 = 0x0   r6 = 0x0   pc = 0x3fdedafc

   0x3fdedaf8:  add   r6, r6, #1
=> 0x3fdedafc:  ldrb  r3, [r6]
   0x3fdedb00:  ldr   r12, [r2]
   0x3fdedb04:  lsl   r1, r3, #1
```

Identical program counter, identical register state, identical instruction. The GET and
POST paths reach the same defect.

---

## Caller identification

A shared library routine (`atoi`/`strtol`) is used by many call sites, so crashing inside
it does **not** by itself prove which caller is at fault. The caller was therefore
identified from the guest stack.

Dumping 400 words from `$sp` at the crash:

```
0x40800908:  0x000ef29c  0x00000001  0x40800f04  0x0009b724
                                                  ^^^^^^^^^^
```

`0x9b724` is the instruction immediately after `bl atoi` in `formWifiWpsOOB`:

```asm
09b720  bl   atoi@plt
09b724  mov  r3, r0          ; <-- saved return address found on the stack
```

Since the binary is `ET_EXEC` with `LOAD` at `vaddr 0x8000` / offset 0, this value is a
runtime code address with no relocation applied — it is not a coincidence of the dump.
The stack frame containing it sits between two stack-pointer values
(`0x40800f04` and `0x40800918`), i.e. in the normal saved-LR position.

The capture was repeated and the same value appeared again.

→ **The crashing call is `atoi(index)` inside `formWifiWpsOOB`.**

---

## Raw capture commands

```bash
# terminal 1 - guest with gdb stub
qemu-arm -g 1234 -L ./ bin/httpd

# terminal 2 - host debugger
cat > cmds.txt <<'EOF'
set architecture arm
set pagination off
set confirm off
target remote 127.0.0.1:1234
continue
printf "r0=0x%x r6=0x%x pc=0x%x\n", $r0, $r6, $pc
x/8i $pc-16
p/x $r6
x/4xb $r6
x/400xw $sp
quit
EOF

gdb-multiarch -q -batch -x cmds.txt
```
