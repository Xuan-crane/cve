# Evidence 01 — Disassembly of `formWifiWpsOOB`

Target: Tenda AC9 v1.0, firmware `V15.03.05.19 (6318)`, file `bin/httpd`
Architecture: ARM 32-bit little-endian, EABI5, dynamically linked against uClibc
Binary: ET_EXEC, first `LOAD` segment at `vaddr 0x8000` = file offset `0`
⇒ **runtime addresses equal link-time addresses** (no relocation needed when reading
addresses off the stack or out of the code).

Symbol table gives `formWifiWpsOOB` at `0x9b674`, size `776` bytes.

---

## 1. Parameter acquisition

```asm
; --- wp comes from the caller's stack slot ---
09b6ac  ldr  r0, [fp, #-296]      ; r0 = wp  (request context)
09b6b0  ldr  r3, [pc, #656]       ; literal -> offset of the string "index"
09b6b4  add  r3, r4, r3           ; r3 = r4 + offset = &"index"
09b6b8  mov  r1, r3               ; r1 = "index"
09b6bc  mov  r2, #0               ; r2 = NULL   <-- default value is NULL
09b6c0  bl   0x9e0b8              ; getVar(wp, "index", NULL)
09b6c4  str  r0, [fp, #-16]       ; store the returned pointer
```

The callee `0x9e0b8` is (`mov r2,#0; bl 0x2b9d4` inside) a thin wrapper over the core
getter `0x2b9d4`, which in turn calls the real lookup at `0x1fb3c`. Semantics are those
of GoAhead's `websGetVar(wp, name, default)`: **the default is returned when the
parameter is absent**, so with a `NULL` default the function returns `NULL`.

The string at the computed address was resolved and confirmed to be `index`
(see `03-strtol-crosscheck.md` for the base arithmetic validation).

---

## 2. The dereference — no guard of any kind

```asm
09b70c  str  r3, [fp, #-20]       ; (unrelated: message type 5 or 24)
09b710  ldr  r3, [pc, #572]
09b714  add  r3, r4, r3
09b718  mov  r5, r3               ; r5 = format string for the later debug printf

09b71c  ldr  r0, [fp, #-16]       ; r0 = index  (may be NULL)
09b720  bl   atoi@plt             ; >>> CRASH SITE <<<
09b724  mov  r3, r0               ; result is used immediately below
09b728  ldr  r2, [fp, #-20]
09b72c  str  r2, [sp]
09b730  mov  r0, r5
09b734  ldr  r2, [pc, #540]
09b738  add  r2, r4, r2
09b73c  mov  r1, r2
09b740  movw r2, #4130
09b744  bl   printf@plt           ; the atoi() result is consumed here
```

Between `09b6c4` (pointer stored) and `09b720` (`atoi`), the pointer is loaded into a
register **once** — at `09b71c` — and passed directly to `atoi`. No comparison against
zero, no conditional branch, nothing.

---

## 3. The guard — present, but 44 bytes too late

```asm
09b748  ldr  r3, [fp, #-16]       ; re-load index
09b74c  cmp  r3, #0               ; >>> NULL check <<<
09b750  bne  0x9b7b4              ; if (index != NULL) goto use
09b754  ldr  r3, [pc, #512]
09b758  add  r3, r4, r3
09b75c  mov  r0, r3
09b760  ldr  r3, [pc, #496]
09b764  add  r3, r4, r3
09b768  mov  r1, r3
09b76c  movw r2, #4133
09b770  bl   printf@plt           ; error path: prints a diagnostic
```

Distance from the `atoi` call (`09b720`) to this check (`09b74c`) is `0x2c` = **44 bytes**.

Reconstructed source:

```c
index = websGetVar(wp, "index", NULL);
...
idx = atoi(index);                 /* crashes here when index == NULL */
printf(...);                       /* result consumed */
...
if (index == NULL) {               /* the guard exists -- just too late */
    printf(...);
}
```

---

## 4. Sibling functions with the same parameter name are written correctly

`formWifiWpsStart` at `0x9a308` reads a parameter also named `index`
(resolved from its own string literal) with the same `NULL` default:

```asm
; formWifiWpsStart -- getVar
09a374  bl  0x9e0b8              ; getVar(wp, "index", NULL)
09a378  str r0, [fp, #-24]       ; store pointer

; ... and the correct guard:
09a3e0  ldr r3, [fp, #-24]
09a3e4  cmp r3, #0               ; check FIRST
09a3e8  bne 0x9a410
09a3ec  ...                      ; NULL branch: diagnostic printf
09a410  ldr r0, [fp, #-24]
09a414  bl  atoi@plt             ; reached only on the non-NULL path
```

`formWifiStatus` (`0x99f28`) shows the identical correct shape.

**Conclusion:** the same developer guarded the same parameter in two sibling handlers and
omitted the guard here. This is an implementation error, not a deliberate design choice —
and it also gives the exact fix (`see docs/fix.md`).

---

## 5. The other defect in the same function (for contrast)

`formWifiWpsOOB` also contains the well-known stack buffer overflow:

```asm
09b85c ... 09b87c   sprintf(buf[24], "%s;%s", index, "1")
```

`buf` lives at `[fp-28]` and is 24 bytes, so writing `len(index) + 3` bytes corrupts the
saved frame pointer once `len(index) >= 22`. Triggering it requires **a long value**;
triggering the NULL dereference requires **no value at all**. The two conditions cannot
both hold, which is why these are treated as independent defects.

---

## Reproduction of this analysis

```bash
arm-linux-gnueabi-readelf -sW httpd | grep -w formWifiWpsOOB
arm-linux-gnueabi-objdump -d --no-show-raw-insn \
    --start-address=0x9b674 --stop-address=0x9b97c httpd
```

The helper address `0x9e0b8` was confirmed by scanning every `bl` in the function and
matching the string literal resolved for the `r1` argument.
