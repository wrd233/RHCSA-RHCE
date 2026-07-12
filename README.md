# RHEL 9 RHCSA / RHCE 内容工程 V2

本仓库以 Markdown 讲义和 YAML Anki Note 为唯一内容真源，提供候选包导入、静态校验、统一 PDF/APKG 构建和显式 Anki 同步工具。二进制生成物与原始课程资料不进入 Git。

## 当前状态

- RHCSA：33/33 候选章节已完成 Manifest/Hash 导入并标记 `validated`，canonical 内容位于 `content/rhcsa/chapters/`；正式本地 PDF/APKG 构建通过。
- RHCE：25 章规划保留在 `config/chapters.yml`，目前全部 `pending`，不声明为正式 V2 内容。
- 通用考试方法：保留一份 canonical `lecture.md` / `anki.yml`。
- 无 RHEL 9 VM：当前结论是静态内容审计与工程构建结果，不代表命令级 live test。

## 目录

```text
config/      章节与 Anki 身份迁移真源
content/     canonical Markdown/YAML
docs/        唯一规范、维护指南和章节计划
styles/      PDF/Anki 样式
templates/   HTML 模板
tools/       导入、校验、构建、审计和安全同步工具
tests/       V2 行为与清洁门禁
reports/     当前集成报告与项目状态
```

`build/`、`dist/`、`releases/`、候选 ZIP/PDF/APKG、原始课件和缓存均被忽略。

## 安装与校验

```bash
uv sync
uv run pytest
uv run python tools/validate_lecture.py
uv run python tools/validate_anki.py
uv run python tools/audit.py rhcsa
```

## 导入候选包

默认 dry-run，不写 canonical 内容：

```bash
uv run python tools/import_candidates.py incoming/
```

审计确认后才写入：

```bash
uv run python tools/import_candidates.py incoming/ --apply --yes
```

支持目录、单章 ZIP、批次 ZIP 与嵌套 ZIP；Chapter ID/slug 来自 `manifest.yml`，并校验声明的 SHA-256，自动过滤 macOS 元数据。

## 构建

```bash
# 单章 HTML/PDF/Anki preview
uv run python tools/build.py rhcsa --chapter lvm

# 全部单章与正式整书/APKG
uv run python tools/build.py rhcsa --all-chapters

# 有 pending 章时只允许明确命名的内部预览
uv run python tools/build.py rhce --allow-incomplete
```

正式命令要求对应考试全部章节为 `validated` 或 `released`；否则失败。预览文件名包含 `INCOMPLETE-PREVIEW`，不会覆盖正式文件。

## Anki 安全边界

APKG Model 包含 `Source` 字段。构建从不调用 AnkiConnect。`tools/sync_anki.py` 默认 dry-run，只有 `--apply --yes` 才会联系本机 AnkiConnect；本轮未调用该接口。

外部资料策略见 `docs/guides/external-sources.md`，完整集成证据见 `reports/V2_INTEGRATION_REPORT.md`。
