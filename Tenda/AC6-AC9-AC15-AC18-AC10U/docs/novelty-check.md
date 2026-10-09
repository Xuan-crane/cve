# Novelty Check Record

Performed 2026-10-09, before drafting the submission.

## 1. NVD — by function name

```
https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=formWifiWpsOOB&resultsPerPage=100
```

**8 results.** All are buffer-overflow class; none is CWE-476.

| Class observed | Meaning |
|---|---|
| CWE-120 / CWE-121 / CWE-787 / CWE-119 | buffer overflow / out-of-bounds write |

Every description uses wording of the form
*"the manipulation of the argument index leads to a stack-based buffer overflow"* —
i.e. an over-long value. No entry describes a missing or empty parameter.

## 2. NVD — by vendor and defect class

```
https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=Tenda%20null%20pointer&resultsPerPage=100
```

**5 results**, all CWE-476 — but in entirely different functions:

| Approximate location | Notes |
|---|---|
| `websReadEvent` / `/goform/GetIPTV` | different function, different endpoint |
| `wifiScheduledSet` / `/goform/modules` | different function, different endpoint |

None touches `formWifiWpsOOB` or `/goform/WifiWpsOOB`.

## 3. CNVD

Public search on the national platform for the vendor together with the endpoint and the
parameter name. No entry was found covering this function/parameter pair in this defect
class.

(Note: the CNVD site was intermittently unreachable during the check, so a manual pass
before submission is advisable.)

## 4. GitHub / general web

Searched for the function name, the endpoint path and the parameter together with
`null pointer`, `空指针`, `denial of service` and `CWE-476`. No public PoC, write-up or
advisory for this defect was found.

Results that do exist for this function all correspond to the overflow issues.

## 5. Conclusion

| Question | Answer |
|---|---|
| Is a CWE-476 defect in `formWifiWpsOOB` already registered? | **No** |
| Is the same parameter covered by overflow CVEs? | Yes — eight of them |
| Does any of them describe this trigger? | No — all require an over-long value |
| Are the triggers mutually exclusive? | Yes (see `differentiation.md`) |

→ No duplicate exists; the finding is eligible for its own CVE ID.

## 6. Recommended shape of the entry

CVE-2024-10280 is a single CWE-476 entry covering ten Tenda models with the same defect.
The same shape is appropriate here: **one CVE covering AC6 / AC9 / AC15 / AC18 / AC10U**,
rather than one ID per model.

## 7. Search terms worth repeating by hand before submission

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

Caveat when reading results: those eight overflow entries will dominate a search for the
function name. They are **not** matches for this defect — check the CWE and the described
trigger of every hit before concluding anything.
