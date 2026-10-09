# Evidence 06 — Per-Model Reproduction (QEMU user-mode emulation)

**Environment disclosure — read this first.** Everything below was reproduced on a
**QEMU user-mode emulation** of the vendor's *unmodified* firmware root filesystems
(`qemu-arm` for the ARM builds, `qemu-mipsel-static` for AC10U) — **not on physical
hardware**. The crashes are genuine process crashes inside the emulated target and the
debugger evidence in `02-gdb-crash.md` was captured from that target, but this is
**emulation, not a physical device**. No physical-device validation is claimed anywhere in
this package.

Every device listed in the main README was driven through the same two-case procedure
against a running instance of the vendor's firmware. Nothing in this file is a static
finding.

## Method

For each model, a device instance is started from the vendor firmware, then:

1. **first contact** — request without a cookie, to collect the server-issued cookie
   (some builds answer `302` and set one);
2. **case A (baseline)** — `POST /goform/WifiWpsOOB` with `index` present; expected
   `HTTP/1.1 200 OK` and the `httpd` process still alive;
3. **case B (trigger)** — same endpoint, body without `index`; expected no HTTP response
   and the `httpd` process gone;
4. **case C (confirmation)** — one more connection; expected refusal.

The two-case design matters: case A proves the service is functioning and the handler is
reachable, so the case-B failure cannot be blamed on a broken setup.

## Results

### Tenda AC9 v1.0 — 15.03.05.19 (6318) — ARM

| Step | Result |
|---|---|
| A — `index` present | `HTTP/1.1 200 OK`, `httpd` alive |
| B — `index` absent | connection closed, `httpd` **gone** |
| Debugger | `SIGSEGV`, `pc=0x3fdedafc`, `r0=0`, `r6=0`, `ldrb r3,[r6]` → fault address `0x0` |
| Caller on stack | `0x9b724` — the instruction after `bl atoi` in `formWifiWpsOOB` |

Also reproduced with a `GET` request; the debugger showed the **same program counter and the
same register state** (see `02-gdb-crash.md`).

### Tenda AC6 — 15.03.05.19 — ARM

```
[0] first contact : HTTP/1.0 302 Redirect   ->  cookie password=hvocvb
[A] index present : HTTP/1.1 200 OK         ->  httpd processes: 1
[B] index absent  : (empty / connection closed)  ->  httpd processes: 0
[C] reconnect     : ConnectionRefusedError
```

### Tenda AC15 — 15.03.05.19 — ARM

Downloaded from the vendor's own download center for this test
(`US_AC15V1.0BR_V15.03.05.19_multi_TD01.zip`, released 2017-05-27 — one release newer than
the `15.03.05.18` sample originally available).

```
[0] first contact : HTTP/1.0 302 Redirect   ->  cookie password=dzccvb
[A] index present : HTTP/1.1 200 OK         ->  httpd processes: 1
[B] index absent  : (empty / connection closed)  ->  httpd processes: 0
[C] reconnect     : ConnectionRefusedError
```

### Tenda AC18 — 15.03.05.19 (6318) — ARM

```
[0] first contact : HTTP/1.0 302 Redirect   ->  cookie password=zklcvb
[A] index present : HTTP/1.1 200 OK         ->  httpd processes: 1
[B] index absent  : (empty / connection closed)  ->  httpd processes: 0
[C] reconnect     : ConnectionRefusedError
```

### Tenda AC10U — 15.03.06.48 — MIPSEL

A different architecture, same outcome:

| Step | Result |
|---|---|
| A — `index` present | `HTTP/1.1 200 OK`, body `bbbbbbbbbbbbbbbb;1`, `httpd` running |
| B — `index` absent | no response, container exited with **139** (SIGSEGV) |

The baseline body `bbbbbbbbbbbbbbbb;1` is precisely the output of
`sprintf(buf, "%s;%s", index, "1")` in the same function, which independently confirms that
the MIPSEL build contains the same handler implementation.

## Summary

| Device | Architecture | Case A | Case B | Case C |
|---|---|---|---|---|
| AC6 | ARM | 200 OK, alive | no response, dead | refused |
| AC9 v1.0 | ARM | 200 OK, alive | no response, dead (debugger-verified) | refused |
| AC15 | ARM | 200 OK, alive | no response, dead | refused |
| AC18 | ARM | 200 OK, alive | no response, dead | refused |
| AC10U | MIPSEL | 200 OK, alive | no response, exited 139 | — |

Five devices, two architectures, one defect.

## Re-verification (independent fresh run)

All five devices were run again on 2026-10-09 from clean container instances, to confirm the
records above were not dependent on a particular environment. Each device was started from
its image, allowed to reach a listening state, and then driven through the same three steps.

| Device | Started | Cookie obtained | A (index present) | B (index absent) | C (reconnect) |
|---|---|---|---|---|---|
| AC6 | 16:52:27 | `302` → `password=twhcvb` | `200 OK`, process alive | no response, process gone | `ConnectionRefusedError` |
| AC18 | 16:52:48 | `302` → `password=catcvb` | `200 OK`, process alive | no response, process gone | `ConnectionRefusedError` |
| AC15 | 16:53:10 | `302` → `password=bwqcvb` | `200 OK`, process alive | no response, process gone | `ConnectionRefusedError` |
| AC9 v1.0 | 16:53:46 | `302` → `password=gnhcvb` | `200 OK`, process alive | no response, process gone | `ConnectionRefusedError` |
| AC10U | 17:05 | `302` → `password=auycvb` | `200 OK` | no response, service gone | `ConnectionRefusedError` |

AC10U runs under `qemu-mipsel-static`, so a process-name based liveness probe that looks for
`qemu-arm` reports zero for this device; its service process was confirmed separately in the
process list (`/qemu-user/qemu-mipsel-static /bin/httpd`). The HTTP-level observations above
are unaffected.

Raw transcripts for this run are preserved in the analysis bundle
(`verify5/AC6.txt`, `AC9.txt`, `AC15.txt`, `AC18.txt`, `AC10U.txt`).

## Environment

QEMU user-mode emulation (`qemu-arm` for the ARM builds, `qemu-mipsel-static` for AC10U)
running the vendor's unmodified firmware root filesystems, with the same emulation
scaffolding the firmware was validated against. Static analysis was performed with
`arm-linux-gnueabi-{readelf,objdump}`; the ARM debugger session used `gdb-multiarch`
attached through the QEMU gdb stub.
