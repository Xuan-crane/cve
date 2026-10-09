#!/usr/bin/env python3
"""Loose variant of the scan: for every function, flag a getter call whose result is
stored to a stack slot and later handed to a callee with no NULL guard.

This is the broader criterion referred to in evidence/05-uniqueness-scan.md. It derives
the set of getter wrappers from the two known addresses and reports every unguarded use,
including ones that turn out to be false positives when tested on the device.

Usage:  python3 hunt_family.py /path/to/httpd
"""
import argparse
import pathlib
import re
import struct
import subprocess

READELF = 'arm-linux-gnueabi-readelf'
OBJDUMP = 'arm-linux-gnueabi-objdump'

HELPERS = (0x9e0b8, 0x2b9d4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary')
    ap.add_argument('--base', type=lambda x: int(x, 0), default=0x8000)
    ap.add_argument('--r4', type=lambda x: int(x, 0), default=0xfd3b8,
                    help='file offset of the string base pointed at by r4')
    args = ap.parse_args()

    data = pathlib.Path(args.binary).read_bytes()

    def va2off(va):
        return va - args.base

    def cstr(va, n=48):
        off = va2off(va)
        if off < 0 or off >= len(data):
            return None
        end = data.find(b'\x00', off, off + n)
        return data[off:end if end > 0 else off + n].decode('latin1', 'replace')

    def disasm(start, size):
        out = subprocess.run(
            [OBJDUMP, '-d', '--no-show-raw-insn',
             '--start-address=0x%x' % start, '--stop-address=0x%x' % (start + size), args.binary],
            capture_output=True, text=True).stdout
        rows = []
        for line in out.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
            if m:
                rows.append((int(m.group(1), 16), m.group(2).strip()))
        return rows

    symbols = subprocess.run([READELF, '-sW', args.binary], capture_output=True, text=True).stdout
    funcs = []
    for m in re.finditer(
            r'^\s*\d+:\s+([0-9a-f]{8})\s+(\d+)\s+FUNC\s+\w+\s+\w+\s+\d+\s+(\S+)$', symbols, re.M):
        funcs.append((int(m.group(1), 16), int(m.group(2)), m.group(3)))
    funcs.sort()

    print('%-30s %-12s %-16s %-10s %s' % ('function', 'parameter', 'use@', 'callee', 'verdict'))
    print('-' * 100)
    suspects = []

    for start, size, name in funcs:
        if size == 0 or size > 6000:
            continue
        rows = disasm(start, size)
        for i, (addr, line) in enumerate(rows):
            m = re.match(r'bl\s+([0-9a-f]+)', line)
            if not m or int(m.group(1), 16) not in HELPERS:
                continue

            slot = None
            for k in range(i + 1, min(i + 4, len(rows))):
                mm = re.match(r'str\s+r0,\s*\[fp,\s*#-(\d+)\]', rows[k][1])
                if mm:
                    slot = mm.group(1)
                    break
            if slot is None:
                continue

            pname = None
            for k in range(i - 1, max(0, i - 9), -1):
                mm = re.match(r'ldr\s+r3,\s*\[pc,\s*#(\d+)\]', rows[k][1])
                if mm:
                    lit = rows[k][0] + 8 + int(mm.group(1))
                    if 0 <= va2off(lit) < len(data):
                        val = struct.unpack('<I', data[va2off(lit):va2off(lit) + 4])[0]
                        pname = cstr((args.r4 + val) & 0xffffffff)
                    break

            for j in range(i + 1, min(i + 60, len(rows))):
                line_j = rows[j][1]
                if not re.match(r'ldr\s+r0,\s*\[fp,\s*#-%s\]' % slot, line_j):
                    continue
                callee = None
                for k in range(j + 1, min(j + 4, len(rows))):
                    mc = re.match(r'bl\s+([0-9a-f]+)', rows[k][1])
                    if mc:
                        callee = rows[k][1]
                        break
                if callee is None:
                    continue

                guard = False
                for k in range(max(0, j - 45), j):
                    if (re.match(r'ldr\s+r\d+,\s*\[fp,\s*#-%s\]' % slot, rows[k][1])
                            and k + 1 < len(rows)
                            and re.search(r'cmp\s+r\d+,\s*#0', rows[k + 1][1])):
                        guard = True
                    if (re.search(r'\[fp,\s*#-%s\]' % slot, rows[k][1])
                            and re.search(r'cmp\s+r\d+,\s*#0', rows[k][1])):
                        guard = True

                verdict = 'guarded' if guard else 'UNGUARDED'
                if not guard:
                    suspects.append((name, pname, rows[j][0], callee))
                print('%-30s %-12s 0x%-14x %-10s %s' % (
                    name, pname, rows[j][0], callee.split()[0], verdict))

    print()
    print('=== unguarded uses ===')
    seen = set()
    for name, param, addr, callee in suspects:
        key = (name, param)
        if key in seen:
            continue
        seen.add(key)
        print('    %-30s param=%-12s use@0x%x  -> %s' % (name, param, addr, callee))


if __name__ == '__main__':
    main()
