# CVE / Vulnerability Records

Vulnerability research by **Xincheng Xu** (徐新程, [@Xuan-crane](https://github.com/Xuan-crane))
and **Xingchi Chen** (陈星池, [@Chauncy-lab](https://github.com/Chauncy-lab)).

Each entry is one advisory: root cause, annotated disassembly, debugger captures, a
reproducible proof of concept, and the evidence used to distinguish the finding from
previously assigned CVEs.

Findings are reported through the VulDB CNA process for CVE assignment; the affected vendor
is contacted before publication.

---

## Advisories

| Vendor | Product | Vulnerability | Type | CVE |
|---|---|---|---|---|
| Tenda | AC6 / AC9 / AC15 / AC18 / AC10U | [formWifiWpsOOB NULL pointer dereference](Tenda/AC6-AC9-AC15-AC18-AC10U/formWifiWpsOOB-null-pointer-dereference.md) | CWE-476 · remote denial of service | *pending* |

---

## Layout

```
<vendor>/
└── <models>/
    ├── <function>-<vulnerability>.md    full technical report
    ├── poc.sh / poc.py                  reproduction scripts
    ├── image/                           screenshots
    ├── docs/                            differentiation from earlier CVEs, fix guidance, novelty check
    └── evidence/                        disassembly, debugger captures, per-device verification
```

## Disclosure policy

- Affected vendors are notified through their published security contact before public
  release; the notification date is recorded in each report.
- Reports state exactly what was tested. Where a finding was reproduced under emulation
  rather than on physical hardware, this is stated explicitly in the report's environment
  section.
- Nothing here should be used against devices you do not own or are not authorised to test.

## License

[MIT](LICENSE) © 2026 Xincheng Xu and Xingchi Chen
