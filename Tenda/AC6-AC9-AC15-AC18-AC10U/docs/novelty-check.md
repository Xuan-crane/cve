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
function/parameter pair.

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

The eight overflow entries dominate a search for the function name, so each hit has to be
read by its CWE and its described trigger rather than by the function name alone.
