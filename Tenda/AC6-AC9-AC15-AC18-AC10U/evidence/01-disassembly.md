# Disassembly

Tenda AC9 V1.0 V15.03.05.19 (6318), `bin/httpd`, ARM 32-bit, uClibc.
`formWifiWpsOOB` is at `0x9b674`, size 776.

The binary is ET_EXEC with the first LOAD segment at `vaddr 0x8000` = file offset 0, so
runtime addresses equal link-time addresses.

## Parameter read

```
09b6ac  ldr  r0, [fp, #-296]      ; wp
09b6b0  ldr  r3, [pc, #656]       ; "index"
09b6b4  add  r3, r4, r3
09b6b8  mov  r1, r3
09b6bc  mov  r2, #0               ; default = NULL
09b6c0  bl   0x9e0b8              ; websGetVar(wp, "index", NULL)
09b6c4  str  r0, [fp, #-16]
```

`0x9e0b8` calls `0x2b9d4`, which calls the lookup at `0x1fb3c`. These wrappers take
(wp, name, default) and return the default when the parameter is absent, like GoAhead's
`websGetVar`. The name string resolves to `index`; the base arithmetic for that resolution
is in `03-strtol-crosscheck.md`.

## Use

```
09b71c  ldr  r0, [fp, #-16]       ; index
09b720  bl   atoi@plt             ; crash site
09b724  mov  r3, r0
09b728  ldr  r2, [fp, #-20]
09b72c  str  r2, [sp]
09b730  mov  r0, r5
...
09b744  bl   printf@plt
```

The pointer is loaded into `r0` once and passed straight to `atoi`. Nothing compares it
against zero first.

## Check

```
09b748  ldr  r3, [fp, #-16]
09b74c  cmp  r3, #0               ; the NULL check
09b750  bne  0x9b7b4
09b754  ...
09b770  bl   printf@plt
```

The check is 44 bytes after the `atoi` call, so it never runs before the dereference.

Reconstructed source:

```c
index = websGetVar(wp, "index", NULL);
...
idx = atoi(index);
printf(...);
...
if (index == NULL) { printf(...); }
```

## Neighbouring handlers

`formWifiWpsStart` reads a parameter with the same name and checks it before use:

```
09a374  bl   0x9e0b8              ; websGetVar(wp, "index", NULL)
09a378  str  r0, [fp, #-24]
...
09a3e0  ldr  r3, [fp, #-24]
09a3e4  cmp  r3, #0
09a3e8  bne  0x9a410
09a3ec  ...                       ; NULL branch
09a410  ldr  r0, [fp, #-24]
09a414  bl   atoi@plt
```

`formWifiStatus` (`0x99f28`) has the same shape.

## sprintf in the same function

The function writes the `index` value into a stack buffer with `sprintf`, at two sites.
The buffer is at `[fp-28]` and the saved frame pointer is at `[fp]`, so 28 bytes are
available before the frame is corrupted.

```
; sprintf(buf, "%s;%s", index, "0")
09b85c  ldr  r3, [pc, #252]       ; "%s;%s"
09b860  add  r3, r4, r3
09b864  sub  r2, fp, #28           ; buf
09b868  mov  r0, r2
09b86c  mov  r1, r3
09b870  ldr  r2, [fp, #-16]        ; index
09b874  ldr  r3, [pc, #212]       ; "0"
09b878  add  r3, r4, r3
09b87c  bl   sprintf@plt

; sprintf(buf, "%s;%s", index, "1")
09b908  ldr  r3, [pc, #80]        ; "%s;%s"
09b90c  add  r3, r4, r3
09b910  sub  r2, fp, #28           ; buf
09b914  mov  r0, r2
09b918  mov  r1, r3
09b91c  ldr  r2, [fp, #-16]        ; index
09b920  ldr  r3, [pc, #64]        ; "1"
09b924  add  r3, r4, r3
09b928  bl   sprintf@plt
```

Neither call bounds the length, so an `index` value of 22 bytes or more overwrites the
saved frame pointer (`len(index) + 3` bytes are written). This is the defect covered by the
existing CVEs, and it needs a long value, which is the opposite of the condition for the
NULL dereference.

A third `sprintf` in the function builds a debug message from two constants and does not
involve `index`:

```
09b77c  sub  r2, fp, #28
09b784  mov  r1, r3                ; "%s;%s"
09b788  ...                        ; "0"
09b790  mov  r2, r3
09b794  ...                        ; "0"
09b79c  bl   sprintf@plt
```

## Commands

```
arm-linux-gnueabi-readelf -sW httpd | grep -w formWifiWpsOOB
arm-linux-gnueabi-objdump -d --no-show-raw-insn \
    --start-address=0x9b674 --stop-address=0x9b97c httpd
```
