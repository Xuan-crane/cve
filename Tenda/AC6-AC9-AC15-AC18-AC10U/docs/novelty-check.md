# Novelty check

Checked on 2026-10-09.

## NVD, by function name

```
https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=formWifiWpsOOB&resultsPerPage=100
```

8 results, all buffer overflow classes (CWE-120, CWE-121, CWE-787, CWE-119). Every one
describes an over-long value for `index`. None is CWE-476 and none describes a missing or
empty parameter.

## NVD, by vendor and class

```
https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=Tenda%20null%20pointer&resultsPerPage=100
```

5 results, all CWE-476, in other functions:

| Location | |
| --- | --- |
| `websReadEvent` / `/goform/GetIPTV` | different function and endpoint |
| `wifiScheduledSet` / `/goform/modules` | different function and endpoint |

None involves `formWifiWpsOOB`.

## CNVD

Public search for the vendor with the endpoint and parameter name returned no entry for this
function/parameter pair. The site was intermittently unreachable during the check, so a
manual search is worth doing before submitting.

## GitHub and web

Searched for the function name, the endpoint and the parameter together with `null pointer`,
`空指针`, `denial of service` and `CWE-476`. Nothing for this defect. Existing material for
the function is about the overflow.

## Result

| Question | Answer |
| --- | --- |
| CWE-476 in `formWifiWpsOOB` already registered? | no |
| Same parameter covered by overflow CVEs? | yes, eight |
| Any of them describe this trigger? | no |
| Triggers mutually exclusive? | yes, see `differentiation.md` |

## Terms to repeat by hand before submitting

```
"formWifiWpsOOB" "null pointer"
Tenda AC9 formWifiWpsOOB CWE-476
Tenda "/goform/WifiWpsOOB" index denial of service
腾达 AC9 formWifiWpsOOB 空指针
腾达 WifiWpsOOB index 参数 拒绝服务

site:nvd.nist.gov formWifiWpsOOB
site:cve.org formWifiWpsOOB
site:vuldb.com Tenda formWifiWpsOOB
site:cnvd.org.cn 腾达 WifiWpsOOB
site:github.com formWifiWpsOOB
```

The eight overflow entries dominate a search for the function name. Check the CWE and the
described trigger of each hit before concluding anything.
