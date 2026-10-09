# Evidence 07 — Version Currency Check

The affected versions are not stale builds: for every device, the tested firmware **is the
one currently offered by the vendor**.

Sources: Tenda's own download center and product support pages (China site and the
per-product material pages, which state version, release date and file size).

---

## Per-device comparison

| Device | Tested version | Vendor's current version | Match |
|---|---|---|---|
| AC6 | 15.03.05.19 | 15.03.05.19 — byte-identical to the vendor's live download | yes (**SHA256 verified**) |
| AC9 v1.0 | 15.03.05.19 (6318) | 15.03.05.19 (6318) | yes |
| AC15 | 15.03.05.19 | 15.03.05.19 | yes (downloaded from the vendor and tested) |
| AC18 | 15.03.05.19 (6318) | 15.03.05.19 (6318) | yes |
| AC10U | 15.03.06.48 | 15.03.06.48 | yes |

### Strongest form of the check (AC6)

Rather than comparing version strings, the AC6 archive used in this analysis was compared
**byte-for-byte** against the file the vendor serves today:

```
vendor CDN : https://static.tenda.com.cn/tdcweb/download/uploadfile/AC6/US_AC6V1.0BR_V15.03.05.19_multi_TD01.zip
sha256     : 621ce4eeef735afacfbe877f0e6f3d05f9cbd9146d72321c674f4bae2372aa1b
local copy : 621ce4eeef735afacfbe877f0e6f3d05f9cbd9146d72321c674f4bae2372aa1b   (identical)
```

The same archive is also what the emulation image used for the live reproduction was built
from, so "the version we tested" is provably "the version the vendor ships".

### Note on the AC6 v1.0 version line

The AC6 v1.0 hardware has more than one firmware version in circulation. Public CVE records
reference two of them:

| Version | Referenced by |
|---|---|
| **`15.03.05.19_multi_TD01`** | this report; also CVE-2020-13389…13394 and CVE-2022-45640/45641/45643/45673/45674 |
| `15.03.05.16` / `15.03.05.16_multi` | a later batch of entries, e.g. CVE-2025-0349, CVE-2025-1814, CVE-2025-5852…5855, CVE-2026-4960, CVE-2026-4961 |

Both are filed against the same CPE hardware revision (`tenda:ac6:1.0`), so they are two
builds of the same device, not two different products. The version analysed here is the one
the vendor currently lists for AC6 v1.0 — and, as shown above, it is byte-identical to the
vendor's live download.

**This report makes no claim about `15.03.05.16`** — it was not tested, and it is not listed
as affected. If a reviewer asks, the honest answer is: this analysis covers the build the
vendor currently distributes.


## Details worth quoting in a report

**AC9** — the product page lists, newest first:

```
AC9V3.0 upgrade software  V15.03.06.42_multi     (different hardware revision, not tested)
AC9V1.0 upgrade software  V15.03.05.19 (6318)    <-- tested
AC9V1.0 upgrade software  V15.03.05.14
AC9V1.0 upgrade software  V15.03.2.13
```

So the tested build is the newest available for the AC9 v1.0 hardware.

**AC18** — the current firmware is `V15.03.05.19 (6318)`, dated **2017-05-26**; no newer
release has been published since.

**AC15** — two entries exist:

| Version | Release date | Size |
|---|---|---|
| V15.03.05.18 | 2017-05-16 | 10.07 M |
| **V15.03.05.19** | **2017-05-27** | 10.13 M |

The later build's release notes mention *"fixed some bugs; enhanced device security"*, so
it is a maintenance/security update. It was downloaded (10,626,640 bytes, matching the
10.13 M stated on the page) and tested: **still vulnerable**.

**AC10U** — the current firmware is `V15.03.06.48`, published **2026-07-13**, with the
release note *"fixed some vulnerabilities and improved system security"*. The defect is
therefore present **in a release the vendor issued as a security update**.

**End-of-life status** — the AC6 and AC15 product pages are marked as discontinued
(已退市), so a fix should not be expected for those models.

## AC9 v3.0

A separate hardware revision of the AC9 ships `V15.03.06.42_multi`. That image was not
available during this analysis and is therefore **not claimed** to be affected — note that
its version number belongs to a different branch, so its code may differ.

## Reproducing the check

1. Open the product's support page on the vendor's site.
2. Compare the listed upgrade entries against the table above.
3. For the file itself, the material page states version, date and size, which can be
   matched against the downloaded archive.
