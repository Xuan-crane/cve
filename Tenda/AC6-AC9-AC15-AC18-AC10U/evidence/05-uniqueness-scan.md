# Evidence 05 — Whole-Binary Uniqueness Scan

Purpose: rule out the objection *"this is just how the codebase is written"* — i.e. show
that the missing guard is an isolated mistake, not a systemic pattern that would make the
finding unremarkable.

Target: Tenda AC9 v1.0 `bin/httpd` — **205,838 instructions** across the whole `.text`.

---

## 1. Identifying the parameter-getter family

The getters used by the form handlers resolve to a three-level chain:

```
formWifiWpsOOB ── bl ──> 0x9e0b8   (wrapper that overrides the default)
                            └── bl ──> 0x2b9d4   (core wrapper: getVar(wp, name, default))
                                          └── bl ──> 0x1fb3c   (real lookup implementation)
```

Both wrappers implement `websGetVar(wp, name, default)` semantics: they take the request
context, a parameter name and a default value, and return a pointer into the request (or
the default).

The core wrapper `0x2b9d4` is invoked from **486** sites; the outer wrapper `0x9e0b8` from
about **25** — together **511 call sites**, which is the complete family.

For completeness, the other high-frequency getter in this binary, the imported
`GetValue` (`0xf528`, 1130 call sites), was examined and excluded: its signature returns a
status code and writes into an output buffer, so it cannot return a `NULL` pointer and is
not part of this defect class. None of the framework call sites of the real lookup
(`0x1fb3c` — in `websDefaultHandler`, `websFormHandler`, `error`, `websAccept`) is followed
by an `atoi` within the next 12 instructions.

## 2. Scan criterion

A site is flagged when **both** hold:

1. the getter is called with a **`NULL` default** — the last write to `r2` before the
   `bl` is `mov r2, #0`; and
2. the returned pointer is loaded into `r0` and passed to a callee **without** a preceding
   `ldr rX, [fp, #-S]` + `cmp rX, #0` guard on that stack slot.

## 3. Result

| Getter call site | Containing function | Slot | Verdict |
|---|---|---|---|
| `0x2b798` | near `websAccept` | -28 | stored for later use (framework path) |
| `0x95e28` | `formWifiMacFilterGet` | -28 | guarded |
| `0x96370` | `formWifiMacFilterSet` | -36 | guarded |
| `0x99f28` | `formWifiStatus` | -24 | guarded |
| `0x9a374` | `formWifiWpsStart` | -24 | guarded |
| **`0x9b6c0`** | **`formWifiWpsOOB`** | **-16** | **UNGUARDED** |
| `0x9ba5c` | (unnamed, after `formWifiWpsOOB`) | -24 | stored for later use |
| `0x9e0f4` | inside the getter wrapper itself | -16 | guarded |

**Exactly one site in the entire binary** meets the criterion: the one described in this
repository.

## 4. The scanner was validated in both directions

A pattern scanner that only ever reports "yes" is worthless, so the two sites it
classified as *guarded* were tested against the emulated target:

| Site | Scanner verdict | Emulated test (missing `index`) |
|---|---|---|
| `formWifiStatus` | guarded | `HTTP/1.1 200 OK` — **no crash** ✔ |
| `formWifiWpsStart` | guarded | `HTTP/1.1 200 OK` — **no crash** ✔ |
| `formWifiWpsOOB` | unguarded | no response, process gone — **crash** ✔ |

The negative cases confirm the criterion is meaningful: sites that look similar but have
the guard really do not crash.

## 5. Stronger form of the same argument: sibling comparison

The two neighbouring handlers read **a parameter with the same name**, using the same
getter, with the same `NULL` default — and they guard it. Only `formWifiWpsOOB` does not:

```asm
; formWifiWpsStart (correct)
09a3e0  ldr  r3, [fp, #-24]
09a3e4  cmp  r3, #0            ; guard first
09a3e8  bne  0x9a410
09a410  ldr  r0, [fp, #-24]
09a414  bl   atoi

; formWifiWpsOOB (this defect)
09b71c  ldr  r0, [fp, #-16]
09b720  bl   atoi              ; no guard
09b74c  cmp  r3, #0            ; guard 44 bytes later
```

## 6. Scope note (avoiding over-claiming)

The statement "only one site" is bounded by the definition above: the `websGetVar`-semantics
getter family, i.e. the 511 call sites of `0x9e0b8` and `0x2b9d4`. A deliberately looser
criterion (deriving the callee set dynamically per function) surfaces additional candidate
sites — the two that were tested turned out to be false positives, and the remainder were
not individually confirmed, so they are **not** claimed here.

## Reproducing the scan

`hunt_final.py` in the analysis bundle performs section 2 over the whole `.text` and prints
the table in section 3. `hunt_family.py` implements the looser criterion used in section 6.
