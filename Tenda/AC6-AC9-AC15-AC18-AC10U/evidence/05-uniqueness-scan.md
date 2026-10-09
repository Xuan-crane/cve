# Whole-binary scan for the same pattern

The AC9 `httpd` was scanned to check whether the missing guard is an isolated case or a
pattern that appears throughout the code. The whole `.text` is 205,838 instructions.

## Getter family

The form handlers read parameters through a three-level chain:

```
formWifiWpsOOB -> 0x9e0b8 (wrapper) -> 0x2b9d4 (core wrapper) -> 0x1fb3c (lookup)
```

Both wrappers take (wp, name, default) and return the default when the parameter is absent.
`0x2b9d4` is called from 486 sites and `0x9e0b8` from about 25, so the family is 511 call
sites.

The other common getter in this binary, the imported `GetValue` (`0xf528`, 1130 call
sites), returns a status code and writes into an output buffer, so it never returns a NULL
pointer. It is not part of this defect class. The framework call sites of the lookup
`0x1fb3c` (`websDefaultHandler`, `websFormHandler`, `error`, `websAccept`) are not followed
by an `atoi`.

## Criterion

A site is flagged when the getter is called with a NULL default (the last write to `r2`
before the `bl` is `mov r2, #0`) and the returned pointer reaches a callee without a
preceding `ldr rX, [fp, #-S]` + `cmp rX, #0` on that stack slot.

## Result

| Site | Function | Slot | Verdict |
| --- | --- | --- | --- |
| 0x2b798 | near `websAccept` | -28 | stored for later use |
| 0x95e28 | `formWifiMacFilterGet` | -28 | guarded |
| 0x96370 | `formWifiMacFilterSet` | -36 | guarded |
| 0x99f28 | `formWifiStatus` | -24 | guarded |
| 0x9a374 | `formWifiWpsStart` | -24 | guarded |
| 0x9b6c0 | `formWifiWpsOOB` | -16 | unguarded |
| 0x9ba5c | unnamed, after `formWifiWpsOOB` | -24 | stored for later use |
| 0x9e0f4 | inside the getter wrapper | -16 | guarded |

One site in the binary meets the criterion.

## Checked against the emulated target

| Site | Scanner says | Missing `index` on the device |
| --- | --- | --- |
| `formWifiStatus` | guarded | 200 OK, no crash |
| `formWifiWpsStart` | guarded | 200 OK, no crash |
| `formWifiWpsOOB` | unguarded | no response, process gone |

The scanner was written by hand, so the two sites it called guarded were tested to make
sure the criterion means something.

## Sibling comparison

`formWifiWpsStart` and `formWifiStatus` read a parameter with the same name, through the
same getter, with the same NULL default, and they check it:

```
; formWifiWpsStart
09a3e0  ldr  r3, [fp, #-24]
09a3e4  cmp  r3, #0
09a3e8  bne  0x9a410
09a410  ldr  r0, [fp, #-24]
09a414  bl   atoi

; formWifiWpsOOB
09b71c  ldr  r0, [fp, #-16]
09b720  bl   atoi
09b74c  cmp  r3, #0
```

## Scope

"One site" refers to the 511 call sites of the two wrappers above. A looser criterion that
derives the callee set per function surfaces more candidates; the two that were tested were
false positives and the rest were not checked individually, so they are not counted here.

## Scripts

`hunt_final.py` implements the criterion above; `hunt_family.py` implements the looser one.
