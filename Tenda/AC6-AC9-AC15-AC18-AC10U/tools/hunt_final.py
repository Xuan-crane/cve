#!/usr/bin/env python3
"""Scan a 32-bit ARM httpd for NULL-default parameter getters whose result is used
without a guard.

A site matters only when both hold:

  (a) the getter is called with r2 == NULL - the last write to r2 before the call is
      `mov r2, #0` - and
  (b) the pointer it returns is later loaded into r0 and handed to a callee with no
      `ldr rX, [fp, #-S]` + `cmp rX, #0` on that slot beforehand.

This is the scan behind evidence/05-uniqueness-scan.md. Only the two wrapper addresses
are specific to the AC9 httpd; set BIN and, if needed, HELPERS for another build.

Usage:  python3 hunt_final.py /path/to/httpd [--base 0x8000]
"""
import argparse
import pathlib
import re
import subprocess

READELF = 'arm-linux-gnueabi-readelf'
OBJDUMP = 'arm-linux-gnueabi-objdump'

# the two wrappers that forward (wp, name, default) to the lookup, on AC9
HELPERS = (0x9e0b8, 0x2b9d4)


def disasm(binary, start, size):
    out = subprocess.run(
        [OBJDUMP, '-d', '--no-show-raw-insn',
         '--start-address=0x%x' % start, '--stop-address=0x%x' % (start + size), binary],
        capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
        if m:
            rows.append((int(m.group(1), 16), m.group(2).strip()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary')
    ap.add_argument('--base', type=lambda x: int(x, 0), default=0x8000,
                    help='file offset subtracted from a VA to get the offset in the file')
    args = ap.parse_args()

    symbols = subprocess.run([READELF, '-sW', args.binary], capture_output=True, text=True).stdout
    funcs = []
    for m in re.finditer(
            r'^\s*\d+:\s+([0-9a-f]{8})\s+(\d+)\s+FUNC\s+\w+\s+\w+\s+\d+\s+(\S+)$', symbols, re.M):
        funcs.append((int(m.group(1), 16), int(m.group(2)), m.group(3)))
    funcs.sort()

    def owner(addr):
        best = ('<unnamed>', 0)
        for start, size, name in funcs:
            if start <= addr < start + size:
                return name, start
            if start <= addr:
                best = ('<after %s>' % name, start)
        return best

    rows = disasm(args.binary, 0xf8c8, 0xd8900 - 0xf8c8)
    print('instructions in .text:', len(rows))
    print()
    print('%-26s %-12s %-8s %-12s %s' % ('function', 'call', 'slot', 'first use', 'verdict'))
    print('-' * 96)

    found = []
    for i, (addr, line) in enumerate(rows):
        m = re.match(r'bl\s+([0-9a-f]+)', line)
        if not m or int(m.group(1), 16) not in HELPERS:
            continue

        last_r2 = None
        for k in range(i - 1, max(0, i - 12), -1):
            if re.match(r'mov(w)?\s+r2,\s*(r\d+|#)', rows[k][1]):
                last_r2 = rows[k][1]
                break
        if last_r2 is None or not re.match(r'mov(w)?\s+r2,\s*#0$', last_r2):
            continue

        slot = None
        for k in range(i + 1, min(i + 4, len(rows))):
            mm = re.match(r'str\s+r0,\s*\[fp,\s*#-(\d+)\]', rows[k][1])
            if mm:
                slot = mm.group(1)
                break
        if slot is None:
            continue

        use = None
        for j in range(i + 1, min(i + 90, len(rows))):
            if re.match(r'ldr\s+r0,\s*\[fp,\s*#-%s\]' % slot, rows[j][1]):
                use = j
                break

        guard_at = None
        if use is not None:
            for k in range(i, use):
                if (re.match(r'ldr\s+r\d+,\s*\[fp,\s*#-%s\]' % slot, rows[k][1])
                        and k + 1 < len(rows)
                        and re.search(r'cmp\s+r\d+,\s*#0', rows[k + 1][1])):
                    guard_at = k

        name, _ = owner(addr)
        verdict = ('no use seen (stored for later)' if use is None else
                   ('guarded (safe)' if guard_at is not None else
                    'UNGUARDED - candidate'))
        print('%-26s 0x%-10x -%-7s %-12s %s' % (
            name, addr, slot,
            ('0x%x' % rows[use][0]) if use is not None else '-', verdict))

        if use is not None and guard_at is None:
            found.append((name, addr, slot, rows[use][0]))

    print()
    print('=== NULL default and no guard before use ===')
    for name, call, slot, use in found:
        print('    %-26s call@0x%x  use@0x%x  (slot -%s)' % (name, call, use, slot))
    print('    %d site(s)' % len(found))


if __name__ == '__main__':
    main()
