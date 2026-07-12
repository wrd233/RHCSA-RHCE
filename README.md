# RHEL 9 RHCSA / RHCE 学习系统

这是一个以 Markdown 和 YAML 为内容真源的 RHEL 9 RHCSA / RHCE 讲义与 Anki 发布项目。最终产物位于 `releases/`，逐章内容位于 `content/`。

## 完整构建

```bash
.venv/bin/python tools/build_release.py
.venv/bin/python tools/final_audit.py --write-report
```

第一条命令依次校验讲义与 Anki、生成全部静态预览、单章 PDF、三本完整 PDF 和两份 APKG。第二条命令直接检查发布 PDF 与 APKG 内部数据库，并生成 `FINAL_REPORT.md`。

## 主要目录

- `content/common/`：通用考试方法。
- `content/rhcsa/chapters/`：13 个 RHCSA 章节。
- `content/rhce/chapters/`：12 个 RHCE 章节。
- `templates/`、`styles/`：PDF 与 Anki 静态预览模板、样式。
- `tools/`：校验、构建、审计及显式同步工具。
- `releases/`：最终 PDF、APKG 与单章 PDF。
- `docs/`：项目架构、讲义、知识树与制卡规范。

## AnkiConnect 安全边界

发布构建不会导入或调用 `tools/sync_anki.py`。同步脚本默认仅做本地 dry-run；只有后续得到明确授权并同时传入 `--apply --yes` 时才连接 AnkiConnect。它按稳定 ID 新增或更新卡片，将 `disabled: true` 的既有卡片暂停，不自动永久删除任何 Note。
