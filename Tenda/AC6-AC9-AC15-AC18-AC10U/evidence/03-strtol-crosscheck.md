# Cross-check against the firmware's libc

The crash is inside `atoi`/`strtol`, which are shared routines: any `atoi(NULL)` in the
process would fault at the same instruction. The following confirms which routine the
address belongs to.

## Symbols

```
$ arm-linux-gnueabi-readelf -sW libc.so.0 | grep -iE ' atoi$| strtol$| strtoul$'
   510: 000558c4     8 FUNC    GLOBAL DEFAULT    7 strtoul
   744: 000558bc     8 FUNC    GLOBAL DEFAULT    7 strtol
  1843: 000558b0    12 FUNC    GLOBAL DEFAULT    7 atoi
```

## `atoi` is a wrapper over `strtol`

```
000558b0 <__GI_atoi>:
   558b0:  mov  r1, #0
   558b4:  mov  r2, #10
   558b8:  b    strtol

000558bc <__GI_strtol>:
   558bc:  mov  r3, #1
   558c0:  b    _stdlib_strto_l

000558cc <_stdlib_strto_l>:
   558cc:  push {r0, r1, r2, r4, r5, r6, r7, lr}
   ...
   558f8:  bl   _stdlib_strto_l_l
```

## Matching instruction sequence

In `strtol` / `_stdlib_strto_l_l`:

```
   55aec:  mov   r6, r0
   55af8:  add   r6, r6, #1
   55afc:  ldrb  r3, [r6]
   55b00:  ldr   r12, [r2]
   55b04:  lsl   r1, r3, #1
   55b08:  ldrh  r7, [r12, r1]
   55b0c:  ands  r7, r7, #32
```

That is the sequence the debugger reported.

## Address arithmetic

Crash PC `0x3fdedafc` minus the matching offset `0x55afc` gives a load base of
`0x3fd98a00`. The low 12 bits of both are `0xafc`. The instruction bytes in the on-disk
library are `e5 d6 30 00` (`ldrb r3, [r6]`), the same instruction the debugger reported.

## Base arithmetic used to resolve strings

The getter address and the parameter name string are both computed from `r4`, which is set
from a literal in the function prologue. Reads of `.rodata` map to file offsets with the
same `0x8000` delta as the code, which is how the literal was resolved to `index`.

The chain:

```
formWifiWpsOOB:  atoi( websGetVar(wp, "index", NULL) )
      ->  atoi(NULL)
      ->  strtol(NULL)
      ->  _stdlib_strto_l_l : ldrb r3, [0x0]
      ->  SIGSEGV
```
