# 截图占位

按 `docs/reproduce-and-screenshots.md` 复现后，用下列文件名放进本目录，主报告的图片引用即可生效。

| 文件名 | 内容 |
| --- | --- |
| `01-disassembly.png` | `formWifiWpsOOB` 反汇编，标出 `atoi(index)` 与 44 字节之后的 `cmp #0` |
| `02-gdb-crash.png` | 调试器现场：`SIGSEGV` / `pc=0x3fdedafc` / `r0=0` / `r6=0` / `ldrb r3,[r6]` |
| `03-fault-address.png` | `x/4xb $r6` → `Cannot access memory at address 0x0` |
| `04-caller-on-stack.png` | 栈转储中的 `0x0009b724` |
| `05-trigger-ab.png` | 带 `index` → 200 OK；缺 `index` → 无响应、进程消失 |
| `06-all-models.png` | 五个机型结果汇总 |

图片不是必需的，`evidence/` 里的文本证据已经完整。
