# CVE Records

Vulnerability research by **Xincheng Xu** (徐新程, [@Xuan-crane](https://github.com/Xuan-crane))
and **Xingchi Chen** (陈星池, [@Chauncy-lab](https://github.com/Chauncy-lab)).

Each directory is one advisory, containing a self-contained technical report: root cause,
annotated disassembly, debugger captures, a reproducible proof of concept, and the evidence
used to distinguish the finding from previously assigned CVEs.

Findings are reported through the VulDB CNA process for CVE assignment; the affected vendor
is contacted before publication.

---

## Advisories

| Entry | Vendor / Product | Type | CVE |
|---|---|---|---|
| [tendaAC_formWifiWpsOOB_index_nullpointer](tendaAC_formWifiWpsOOB_index_nullpointer/) | Tenda AC6 / AC9 / AC15 / AC18 / AC10U | CWE-476 · remote denial of service | *pending* |

---

## Layout

```
<vendor><model>_<function>_<parameter>_<type>/
├── README.md      technical report — root cause, impact, fix, reproduction
├── poc.sh         one-command reproduction
├── poc.py         reproduction with an explicit verdict
├── images/        screenshots of the reproduction
├── docs/          differentiation from earlier CVEs, fix guidance, novelty check
└── evidence/      disassembly, debugger captures, per-device verification records
```

## Disclosure policy

- Affected vendors are notified through their published security contact before public
  release; the notification date is recorded in each report.
- Reports state exactly what was tested. Where a finding was reproduced under emulation
  rather than on physical hardware, this is stated explicitly in the report's environment
  section.
- Nothing here should be used against devices you do not own or are not authorised to test.

## License

[MIT](tendaAC_formWifiWpsOOB_index_nullpointer/LICENSE) © 2026 Xincheng Xu and Xingchi Chen
