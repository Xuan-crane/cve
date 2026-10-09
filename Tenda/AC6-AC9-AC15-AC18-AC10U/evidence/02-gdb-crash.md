# Debugger capture

The firmware's `httpd` was started under QEMU's gdb stub and `gdb-multiarch` attached to it.
Two captures are recorded, one from a POST request and one from a GET request.

## POST without `index`

```
Program received signal SIGSEGV, Segmentation fault.
0x3fdedafc in ?? ()

r0    0x0
r1    0x0
r2    0x3fe0a4e8
r3    0x1
r12   0x3fe05704
sp    0x408008c8
lr    0x3fded8fc
pc    0x3fdedafc

---- faulting instruction ----
   0x3fdedaf4:  b     0x3fdedafc
   0x3fdedaf8:  add   r6, r6, #1
=> 0x3fdedafc:  ldrb  r3, [r6]
   0x3fdedb00:  ldr   r12, [r2]
   0x3fdedb04:  lsl   r1, r3, #1
   0x3fdedb08:  ldrh  r7, [r12, r1]

---- the pointer being dereferenced ----
p/x $r6
$1 = 0x0

x/4xb $r6
Cannot access memory at address 0x0
```

Where `r6` comes from:

```
0x3fdedaec:  mov  r6, r0        ; scan pointer := first argument
0x3fdedaf0:  ldr  r2, [sp, #48]
0x3fdedaf4:  b    0x3fdedafc
0x3fdedaf8:  add  r6, r6, #1
0x3fdedafc:  ldrb r3, [r6]      ; fault
```

`r0` was 0, the value was copied into the scan register unchanged, and the loop read from
address 0.

## GET without parameters

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

Same program counter, same registers, same instruction as the POST case.

## Which `atoi` call is it

`atoi` and `strtol` are used from many places, so crashing inside them does not by itself
say which caller is responsible. The caller was read off the guest stack.

400 words from `$sp` at the crash contain:

```
0x40800908:  0x000ef29c  0x00000001  0x40800f04  0x0009b724
```

`0x9b724` is the instruction after `bl atoi` in `formWifiWpsOOB`:

```
09b720  bl   atoi@plt
09b724  mov  r3, r0
```

The binary is ET_EXEC with LOAD at `vaddr 0x8000`, so this is a runtime code address with
no relocation applied. The frame holding it sits between two stack addresses
(`0x40800f04`, `0x40800918`), in the normal saved-LR position. The capture was repeated and
the same value appeared.

## Commands

The session is in `../gdb-session.txt` at the root of this entry:

```
gdb-multiarch -q -x gdb-session.txt
```

It needs the httpd binary (for symbols) and the QEMU gdb stub address, both of which are
set at the top of that file. Start the target with `qemu-arm -g 1234 -L ./ bin/httpd`.
