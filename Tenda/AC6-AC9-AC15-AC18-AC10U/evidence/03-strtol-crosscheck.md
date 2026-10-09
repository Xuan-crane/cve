# Evidence 03 — Cross-check Against the Firmware's Own libc

**Claim to verify:** the crash site is `atoi()` → `strtol()` in the vendor's C library
`libuClibc`, and not some other null-pointer path.

`atoi` and `strtol` are shared routines: *any* call to `atoi(NULL)` in the process would
crash at the same program counter. Confirming the routine identity is therefore necessary
(and is complemented by the caller identification in `02-gdb-crash.md`).

---

## 1. Library symbols

```console
$ arm-linux-gnueabi-readelf -sW libc.so.0 | grep -iE ' atoi$| strtol$| strtoul$'
   510: 000558c4     8 FUNC    GLOBAL DEFAULT    7 strtoul
   744: 000558bc     8 FUNC    GLOBAL DEFAULT    7 strtol
  1843: 000558b0    12 FUNC    GLOBAL DEFAULT    7 atoi
```

## 2. `atoi` is a thin wrapper over `strtol`

```asm
000558b0 <__GI_atoi>:
   558b0:  mov  r1, #0
   558b4:  mov  r2, #10
   558b8:  b    strtol            ; tail call, base 10

000558bc <__GI_strtol>:
   558bc:  mov  r3, #1
   558c0:  b    _stdlib_strto_l   ; internal implementation

000558cc <_stdlib_strto_l>:
   558cc:  push {r0, r1, r2, r4, r5, r6, r7, lr}
   ...
   558f8:  bl   _stdlib_strto_l_l
```

## 3. The instruction sequence at the crash exists in `strtol`

Scanning the disassembly of `strtol` / `_stdlib_strto_l_l` for the sequence observed in the
debugger (`mov r6,r0` … `add r6,r6,#1` … `ldrb r3,[r6]` … `ldrh r7,[r12,r1]` … `ands r7,r7,#32`):

```asm
   55aec:  mov   r6, r0            ; scan pointer := argument
   55af8:  add   r6, r6, #1        ; advance
   55afc:  ldrb  r3, [r6]          ; <-- byte load
   55b00:  ldr   r12, [r2]
   55b04:  lsl   r1, r3, #1
   55b08:  ldrh  r7, [r12, r1]     ; 16-bit character-class table lookup
   55b0c:  ands  r7, r7, #32
```

## 4. Address arithmetic

| Item | Value |
|---|---|
| Crash program counter | `0x3fdedafc` |
| Matching instruction offset inside `strtol` | `0x55afc` |
| Implied library load base | `0x3fdedafc - 0x55afc = 0x3fd98a00` |
| Low 12 bits of the crash PC | `0xafc` |
| Low 12 bits of `strtol+0x240` | `0xafc` |

The bytes of the faulting instruction in the on-disk library are `e5 d6 30 00`
(`ldrb r3, [r6]` with `r3=12, r6=6, imm=0`), matching the instruction reported by the
debugger.

---

## Conclusion

The crash occurs inside the vendor's `strtol` implementation, reached from `atoi()`,
because the argument pointer is `NULL`. Combined with:

- the fault address being exactly `0x0` (`02-gdb-crash.md`),
- and the saved return address on the stack pointing into `formWifiWpsOOB`,

…the causal chain is complete:

```
formWifiWpsOOB:  atoi( websGetVar(wp, "index", NULL) )
      ->  atoi(NULL)
      ->  strtol(NULL)
      ->  _stdlib_strto_l_l  :  ldrb r3, [0x0]
      ->  SIGSEGV
```
