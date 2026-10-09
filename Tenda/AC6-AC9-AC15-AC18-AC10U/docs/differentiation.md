# Relationship to the existing CVEs

The `index` parameter of `formWifiWpsOOB` is already covered by several CVE IDs. All of them
are stack buffer overflows. This report describes a separate defect.

## What exists

Searching NVD for the function returns eight entries, in the buffer overflow classes
(CWE-120, CWE-121, CWE-787, CWE-119). Their descriptions read like:

> the manipulation of the argument index leads to a stack-based buffer overflow

No entry describes a missing or empty parameter, and no entry is CWE-476.

## Comparison

| | Existing CVEs | This issue |
| --- | --- | --- |
| Operation | `sprintf(buf, "%s;%s", index, "0"/"1")` at `0x9b87c` / `0x9b928` | `atoi(index)` |
| CWE | CWE-121 (also 120/787/119) | CWE-476 |
| Input | `index`, 22 bytes or longer | `index` absent or empty |
| Fault | in httpd, on return from the function | in libc `strtol` at `0x3fdedafc`, immediately |
| Response before dying | 200 OK, then crash | none |
| Fix | bound the length | add the NULL check |

## Triggers do not overlap

A long value takes the `sprintf` path. The pointer is non-NULL, so `atoi` cannot fault. An
absent value takes the `atoi` path, and there is no value to overrun the buffer. Neither
input can reach the other's faulting instruction.

| Input | Overflow | NULL dereference | Observed |
| --- | --- | --- | --- |
| `index=1` | no | no | 200 OK |
| `index=` + 22 bytes or more | yes | no | overflow |
| `index` absent | no | yes | crash |

## Different faulting instruction and different library

The overflow corrupts the stack inside httpd and takes effect when the function returns.
This defect faults inside the C library before any output is produced, with fault address
`0x0`. See `evidence/02-gdb-crash.md` and `evidence/03-strtol-crosscheck.md`.

## One omission, not a pattern

Across the binary there is one unguarded NULL-default getter use
(`evidence/05-uniqueness-scan.md`). The two neighbouring handlers read a parameter with the
same name and guard it. So this is a distinct line of code that a fix for the overflow
would not touch.

## Shape of the entry

CVE-2024-10280 is a single CWE-476 entry covering ten Tenda models with the same defect,
which is the shape used here: one CVE for several models rather than one per model.
