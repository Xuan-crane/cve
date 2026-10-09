# 截图放这里

按 `../docs/reproduce-and-screenshots.md` 的步骤生成后，用下列文件名放进本目录，
README 里的引用就能直接生效：

| 文件名 | 内容 |
|---|---|
| `01-disassembly.png` | `formWifiWpsOOB` 反汇编，标出无保护的 `atoi(index)` 与 44 字节之后的 `cmp #0` |
| `02-gdb-crash.png` | 调试器现场：`SIGSEGV` / `pc=0x3fdedafc` / `r0=0` / `r6=0` / `ldrb r3,[r6]` |
| `03-fault-address.png` | `x/4xb $r6` → `Cannot access memory at address 0x0` |
| `04-caller-on-stack.png` | 栈转储中的 `0x0009b724`（`bl atoi` 的返回地址） |
| `05-trigger-ab.png` | 两用例对照：带 `index` → `200 OK`；缺 `index` → 无响应、进程消失 |
| `06-all-models.png` | 五个机型的结果汇总表 |
| `07-recording.gif` | （可选）30 秒复现录屏 |

截图不是必需的——`evidence/` 里的文本证据已经完整。但放入图片能显著降低审核员的阅读成本，
对通过率是有帮助的。
