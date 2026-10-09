# Differentiation From the Existing CVEs on the Same Function and Parameter

This is the single most important document for the submission, because the same function
and the same parameter have already been assigned multiple CVE IDs.

**If a reviewer concludes "this is the same vulnerability seen from another angle", the
report is closed as a duplicate.** The material below exists to make that conclusion
impossible to reach honestly.

---

## 1. What already exists

Searching NVD for this function returns **eight** entries, every one of them a memory
corruption / buffer overflow class:

| CWE family | Meaning |
|---|---|
| CWE-120 | Buffer Copy without Checking Size of Input |
| CWE-121 | Stack-based Buffer Overflow |
| CWE-787 | Out-of-bounds Write |
| CWE-119 | Improper Restriction of Operations within the Bounds of a Memory Buffer |

Representative description wording from those entries:

> *"…the manipulation of the argument index leads to a stack-based buffer overflow…"*

None of them is a NULL-pointer defect, and searching NVD for a NULL-pointer issue on this
function returns nothing.

## 2. Side-by-side

| | Existing CVEs | **This finding** |
|---|---|---|
| Vulnerable operation | `sprintf(buf[24], "%s;%s", index, "1")` | `atoi(index)` |
| CWE | CWE-121 (also 120/787/119) | **CWE-476 — NULL Pointer Dereference** |
| What the attacker must send | `index` with **length >= 22 bytes** | `index` **absent**, or present but empty |
| Where it faults | inside `httpd`, addresses `0x9b85c`–`0x9b87c`, corrupting the saved frame; dies on return | inside libc `strtol`, program counter `0x3fdedafc`, reading address `0x0` |
| Server response before dying | `200 OK`, then the crash | **no response at all** |
| Minimal proof | a 22+ byte value | one request, no parameters |
| Fix | bound the length / use `snprintf` | add the missing NULL check |

## 3. The two triggers are mutually exclusive

This is the strongest argument, and it is empirical rather than interpretive:

- Sending a **long** value (`index=` + many bytes) exercises the `sprintf` path. The pointer
  is non-NULL, so the `atoi` call cannot fault.
- Sending **no** value exercises the `atoi` path. There is no value to overrun the buffer,
  so the `sprintf` path cannot fault.

Each trigger is incapable of reaching the other defect's faulting instruction. They are
therefore two separate defects that happen to live in the same function — not one defect
observed twice.

Measured confirmation:

| Input | Overflow path | NULL path | Observed |
|---|---|---|---|
| `index=1` | not reachable (too short) | not reachable (non-NULL) | `200 OK` |
| `index=` + 22+ bytes | reachable | not reachable | overflow |
| `index` absent | not reachable | reachable | **NULL dereference** |

## 4. Different faulting instruction, different library

The overflow corrupts the stack inside `httpd` and manifests when the function returns.
This defect terminates immediately inside the C library, before any output is produced.
The debugger shows the program counter inside `strtol`, with the fault address exactly
`0x0` — see `evidence/02-gdb-crash.md` and `evidence/03-strtol-crosscheck.md`.

A signature difference of this kind is the standard way CNAs separate defects that share a
parameter, and the fault address `0x0` is unambiguous.

## 5. It is one omission among correctly-written siblings

Across the whole binary there is exactly one unguarded `NULL`-default getter use
(`evidence/05-uniqueness-scan.md`), while the two neighbouring handlers read the *same
parameter name* and guard it properly. So this cannot be characterised as "the known
overflow, described differently" — the source-level mistake is a distinct line of code
that the existing CVEs' fixes would not touch.

## 6. Novelty check performed

- **NVD REST API**, `keywordSearch=formWifiWpsOOB` → 8 CVEs, all overflow-class, none
  CWE-476.
- **NVD REST API**, `keywordSearch=Tenda null pointer` → 5 CVEs, all CWE-476, but in
  entirely different functions (`websReadEvent` / `/goform/GetIPTV`, `wifiScheduledSet` /
  `/goform/modules`).
- **CNVD** public search → no entry for this function/parameter pair in this class.

Conclusion: no existing record covers this defect.

## 7. Precedent for how this should be numbered

CVE-2024-10280 is a single CWE-476 entry covering ten Tenda models with the same defect.
That is the appropriate shape here: **one CVE, several affected models**, rather than a
separate ID per device.
