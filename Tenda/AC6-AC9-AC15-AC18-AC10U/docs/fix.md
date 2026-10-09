# Fix

Validate the pointer before use:

```diff
  index = websGetVar(wp, "index", NULL);
+ if (index == NULL) {
+     return;
+ }
  idx = atoi(index);
```

In the AC9 build the existing check at `0x9b74c` only has to move ahead of the call at
`0x9b720`:

```
; now                             ; fixed
09b71c  ldr  r0, [fp, #-16]       09b748  ldr  r3, [fp, #-16]
09b720  bl   atoi                 09b74c  cmp  r3, #0
09b748  ldr  r3, [fp, #-16]       09b750  bne  <use>
09b74c  cmp  r3, #0
```

Or give the parameter a default that is not NULL:

```diff
- index = websGetVar(wp, "index", NULL);
+ index = websGetVar(wp, "index", "");
```

With an empty string `atoi` returns 0 and the later `sprintf` writes a few bytes into a
24-byte buffer.

The two neighbouring handlers already do this. `formWifiWpsStart`:

```
09a3e0  ldr  r3, [fp, #-24]
09a3e4  cmp  r3, #0
09a3e8  bne  0x9a410
09a3ec  ...
09a410  ldr  r0, [fp, #-24]
09a414  bl   atoi
```

Copying that structure into `formWifiWpsOOB` changes nothing for well-formed requests.

## Auditing other builds

The same mistake can appear at any getter call whose default is NULL:

```
for each call to the parameter getter:
    if (default == NULL)
        require a NULL check before the first use
```

In the AC9 image there are eight such sites and this is the only one without the check.
`evidence/05-uniqueness-scan.md` lists them and gives the criterion, which applies to other
images in this product family.
