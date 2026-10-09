# Fix

## Recommended change

Validate the pointer immediately after obtaining it, before any use:

```diff
  index = websGetVar(wp, "index", NULL);
+ if (index == NULL) {
+     /* the parameter is required; report the error and stop */
+     return;
+ }
  idx = atoi(index);
```

The check must sit **before** the `atoi` call. Inside the firmware, the existing check at
`0x9b74c` simply needs to move ahead of the call site at `0x9b720`:

```asm
; before                          ; after
09b71c  ldr  r0, [fp, #-16]       09b748  ldr  r3, [fp, #-16]
09b720  bl   atoi                 09b74c  cmp  r3, #0
09b748  ldr  r3, [fp, #-16]       09b750  bne  <use>
09b74c  cmp  r3, #0               ...
```

## Minimal alternative

Give the parameter a non-NULL default so the pointer can never be NULL:

```diff
- index = websGetVar(wp, "index", NULL);
+ index = websGetVar(wp, "index", "");
```

With an empty string, `atoi()` returns `0` and the subsequent `sprintf` writes a few bytes
into a 24-byte buffer — safe.

## Pointer for the vendor: the sibling handlers already do it right

`formWifiWpsStart` (`0x9a308`) and `formWifiStatus` (`0x99f28`) read a parameter with the
same name and apply the guard correctly:

```asm
09a3e0  ldr r3, [fp, #-24]
09a3e4  cmp r3, #0
09a3e8  bne 0x9a410        ; non-NULL path
09a3ec  ...                ; NULL path: diagnostic
09a410  ldr r0, [fp, #-24]
09a414  bl  atoi
```

Copying that structure into `formWifiWpsOOB` resolves the issue with no change in
behaviour for well-formed requests.

## Audit guidance

Because the same class of mistake can appear wherever a getter's default is `NULL`, the
audit should check every getter call that passes a `NULL` default:

```
for each call to the parameter getter:
    if (default == NULL)
        require a NULL check on the result before the first use
```

In the AC9 image that set is small — eight sites — and the site described here is the only
one that fails the check. See `evidence/05-uniqueness-scan.md` for a complete listing and
for the exact scanning criterion, which can be applied to other images of this product
family.
