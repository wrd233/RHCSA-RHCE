# Project status

- 当前版本：RHCSA V2 validated，正式本地构建通过。
- RHCSA：33/33 候选已接受、进入 canonical 路径并通过静态/工程门；pending 0。
- RHCE：0/25 integrated，25 pending；不参与正式发布。
- 正式 RHCSA release 阻断项：无工程阻断；真实 RHEL 9 命令级 live test 未执行，不应与静态通过混淆。
- 下一步：在 RHEL 9 VM 执行高风险章节 live test；未来 RHCE 按同一候选包流水线逐章导入。
# 2026-07-12 Reading PDF and AnkiConnect

Status: `CLOSED_VERIFIED`. RHCSA formal output now defaults to the A4 large-font reading profile. All 33 technical chapters, the common chapter, 9 parts and the 540-page book passed PDF QA. RHCSA APKG and AnkiConnect contain 3,353 Notes / 3,700 Cards; readback found zero duplicate stable IDs and formal templates hide Source. See `PDF_REDESIGN_AND_ANKI_SYNC_REPORT.md`.
