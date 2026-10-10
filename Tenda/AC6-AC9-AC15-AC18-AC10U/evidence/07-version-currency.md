# Version check

Each tested build is the version the vendor's download page currently lists for that model.

| Device | Tested | Vendor's current | Date on page | Page |
| --- | --- | --- | --- | --- |
| AC6 V1.0 | V15.03.05.19 | V15.03.05.19 | 2024-11-28 | https://www.tenda.com.cn/download/detail-2681.html |
| AC9 V1.0 | V15.03.05.19 (6318) | V15.03.05.19 (6318) | 2017-05-27 | https://www.tenda.com.cn/download/detail-2682.html |
| AC15 V1.0 | V15.03.05.19 | V15.03.05.19 | 2017-05-27 | https://www.tenda.com.cn/download/detail-2680.html |
| AC18 | V15.03.05.19 (6318) | V15.03.05.19 (6318) | 2017-05-27 | https://www.tenda.com.cn/download/detail-2683.html |
| AC10U V1.0 | V15.03.06.48 | V15.03.06.48 | 2025-06-05 | https://www.tendacn.com/download/detail-3170.html |

AC9, AC15 and AC18 have had no release since 2017. AC6 was re-published in November 2024 and
AC10U in June 2025, and the missing check is present in both of those as well. So the tested
builds are not stale copies: they are what the vendor serves today, including the two most
recent releases in the line.

## AC6

The archive used here is byte-identical to the file the vendor's CDN serves, verified by
downloading it again:

```
https://static.tenda.com.cn/tdcweb/download/uploadfile/AC6/US_AC6V1.0BR_V15.03.05.19_multi_TD01.zip
6472282 bytes
sha256 621ce4eeef735afacfbe877f0e6f3d05f9cbd9146d72321c674f4bae2372aa1b
```

The download page carries `更新时间 2024-11-28` and the release notes read `修复部分bug` and
`增强设备安全` (fixed some bugs, hardened the device), so this build postdates a
security-hardening release and still carries the missing check.

The AC6 v1.0 hardware has more than one firmware build in circulation. Public CVE records
reference two:

| Version | Referenced by |
| --- | --- |
| `15.03.05.19_multi_TD01` | this report; CVE-2020-13389..13394; CVE-2022-45640, 45641, 45643, 45673, 45674 |
| `15.03.05.16` / `15.03.05.16_multi` | CVE-2025-0349, CVE-2025-1814, CVE-2025-5852..5855, CVE-2026-4960, CVE-2026-4961 |

Both map to the same CPE hardware revision (`tenda:ac6:1.0`). Only `15.03.05.19` was tested;
no claim is made about `15.03.05.16`.

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

`V15.03.05.19 (6318)`, page date 2017-05-27. No newer release has been published.

## AC10U

`V15.03.06.48`, page date 2025-06-05, size 7.26 M. The download page is the one for v1.0
hardware.

## AC9 v3.0

The v3.0 hardware ships `V15.03.06.42_multi`. That image was not tested and is not claimed
to be affected.
