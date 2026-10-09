# Version check

The tested firmware is the version each product page currently lists.

| Device | Tested | Vendor's current | Download |
| --- | --- | --- | --- |
| AC6 V1.0 | V15.03.05.19 | V15.03.05.19 | https://www.tenda.com.cn/download/detail-2681.html |
| AC9 V1.0 | V15.03.05.19 (6318) | V15.03.05.19 (6318) | https://www.tenda.com.cn/download/detail-2682.html |
| AC15 V1.0 | V15.03.05.19 | V15.03.05.19 | https://www.tenda.com.cn/download/detail-2680.html |
| AC18 | V15.03.05.19 (6318) | V15.03.05.19 (6318) | https://www.tenda.com.cn/download/detail-2683.html |
| AC10U V1.0 | V15.03.06.48 | V15.03.06.48 | https://www.tendacn.com/download/detail-3170.html |

## AC6

The archive used here is byte-identical to the file the vendor serves:

```
https://static.tenda.com.cn/tdcweb/download/uploadfile/AC6/US_AC6V1.0BR_V15.03.05.19_multi_TD01.zip
sha256 621ce4eeef735afacfbe877f0e6f3d05f9cbd9146d72321c674f4bae2372aa1b
```

The AC6 v1.0 hardware has more than one firmware build in circulation. Public CVE records
reference two:

| Version | Referenced by |
| --- | --- |
| `15.03.05.19_multi_TD01` | this report; CVE-2020-13389..13394; CVE-2022-45640, 45641, 45643, 45673, 45674 |
| `15.03.05.16` / `15.03.05.16_multi` | CVE-2025-0349, CVE-2025-1814, CVE-2025-5852..5855, CVE-2026-4960, CVE-2026-4961 |

Both map to the same CPE hardware revision (`tenda:ac6:1.0`). Only `15.03.05.19` was
tested; no claim is made about `15.03.05.16`.

## AC9

The product page lists, newest first:

```
AC9V3.0  V15.03.06.42_multi      different hardware revision, not tested
AC9V1.0  V15.03.05.19 (6318)     tested
AC9V1.0  V15.03.05.14
AC9V1.0  V15.03.2.13
```

## AC15

| Version | Date | Size |
| --- | --- | --- |
| V15.03.05.18 | 2017-05-16 | 10.07 M |
| V15.03.05.19 | 2017-05-27 | 10.13 M |

The 2017-05-27 build was downloaded (10,626,640 bytes, matching the stated 10.13 M) and
tested.

## AC18

`V15.03.05.19 (6318)`, dated 2017-05-26. No newer release has been published.

## AC10U

`V15.03.06.48`, published 2026-07-13.

## End of life

The AC6 and AC15 product pages are marked 已退市 (discontinued), which is why the newest
release for both is from 2017.

## AC9 v3.0

The v3.0 hardware ships `V15.03.06.42_multi`. That image was not available and is not
claimed to be affected.
