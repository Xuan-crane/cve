# Per-model verification

All devices were run in QEMU user mode (`qemu-arm` for the ARM builds,
`qemu-mipsel-static` for AC10U) on the vendor's unmodified firmware root filesystems. No
physical hardware was used. The crashes are real process crashes inside the emulated
target, and the debugger captures come from that target.

For each device: request a cookie, send a request with `index` present, then send the same
request with `index` absent. The first step shows the handler works, so a failure in the
second cannot be blamed on a broken setup.

## AC9 V1.0 V15.03.05.19 (6318)

| Step | Result |
| --- | --- |
| `index` present | 200 OK, process alive |
| `index` absent | connection closed, process gone |
| Debugger | SIGSEGV, `pc=0x3fdedafc`, `r0=0`, `r6=0`, `ldrb r3,[r6]`, fault address 0 |
| Caller | return address `0x9b724` on the stack, the instruction after `bl atoi` |

Also reproduced with a GET request; same program counter and registers.

## AC6 V1.0 V15.03.05.19

```
[0] first contact : HTTP/1.0 302 Redirect   ->  cookie password=hvocvb
[A] index present : HTTP/1.1 200 OK         ->  process alive
[B] index absent  : (empty)                 ->  process gone
[C] reconnect     : ConnectionRefusedError
```

## AC15 V1.0 V15.03.05.19

Firmware downloaded from the vendor for this test
(`US_AC15V1.0BR_V15.03.05.19_multi_TD01.zip`, 2017-05-27).

```
[0] first contact : HTTP/1.0 302 Redirect   ->  cookie password=dzccvb
[A] index present : HTTP/1.1 200 OK         ->  process alive
[B] index absent  : (empty)                 ->  process gone
[C] reconnect     : ConnectionRefusedError
```

## AC18 V15.03.05.19 (6318)

```
[0] first contact : HTTP/1.0 302 Redirect   ->  cookie password=zklcvb
[A] index present : HTTP/1.1 200 OK         ->  process alive
[B] index absent  : (empty)                 ->  process gone
[C] reconnect     : ConnectionRefusedError
```

## AC10U V1.0 V15.03.06.48

| Step | Result |
| --- | --- |
| `index` present | 200 OK, body `bbbbbbbbbbbbbbbb;1` |
| `index` absent | no response, process exited 139 |

The body `bbbbbbbbbbbbbbbb;1` is what `sprintf(buf, "%s;%s", index, "1")` in this function
produces, so the MIPSEL build has the same handler.

## Repeat run

The five devices were started again from clean instances and driven through the same steps.

| Device | Cookie | `index` present | `index` absent | Reconnect |
| --- | --- | --- | --- | --- |
| AC6 | `twhcvb` | 200 OK, alive | no response, gone | refused |
| AC18 | `catcvb` | 200 OK, alive | no response, gone | refused |
| AC15 | `bwqcvb` | 200 OK, alive | no response, gone | refused |
| AC9 | `gnhcvb` | 200 OK, alive | no response, gone | refused |
| AC10U | `auycvb` | 200 OK | no response, gone | refused |

AC10U runs as `qemu-mipsel-static`, so a liveness probe that greps for `qemu-arm` reports
zero for it; the process was confirmed in the process list instead
(`/qemu-user/qemu-mipsel-static /bin/httpd`). The HTTP results above are unaffected.
