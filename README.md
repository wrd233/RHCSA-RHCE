# RHEL 9 RHCSA / RHCE 内容工程

本仓库以 Markdown 讲义和 YAML Anki Note 为唯一内容真源，提供候选包导入、静态校验、统一 PDF/APKG 构建和显式 Anki 同步工具。二进制生成物与原始课程资料不进入 Git。

## 当前状态

- RHCSA：33/33 个 v5.1 冻结章节已无损集成，canonical 内容位于 `content/rhcsa/chapters/`；统一 Schema、PDF、HTML、APKG 与 AnkiConnect readback 均通过。
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

`build/`、`dist/`、`releases/`、候选 ZIP/PDF/APKG、原始课件和缓存均被忽略。正式本地发布入口为 `releases/rhcsa-v5.1/`，构建报告与校验规则进入 Git。

## 安装与校验

```bash
uv sync
uv run pytest
uv run python tools/validate_lecture.py
uv run python tools/validate_anki.py
uv run python tools/audit.py rhcsa
uv run python tools/pdf_qa.py releases/rhcsa-v5.1 --json reports/rhcsa-v5.1-pdf-qa.json
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
uv run python tools/finalize_v51.py

# 有 pending 章时只允许明确命名的内部预览
uv run python tools/build.py rhce --allow-incomplete
```

正式命令要求对应考试全部章节为 `validated` 或 `released`；否则失败。v5.1 的章节 PDF、整书 PDF、维护 HTML 和 APKG 由上述两条命令构建并收敛到单一 Release 目录。

## Anki 安全边界

APKG Model 包含 `Source` 字段，但正式卡面不显示它。构建从不隐式调用 AnkiConnect；`tools/sync_anki.py --all` 默认 dry-run，只有 `--apply --yes` 才执行稳定 ID upsert。同步后使用 `uv run python tools/anki_readback.py --output reports/anki-readback-v5.1.json` 验证。

外部资料策略见 `docs/guides/external-sources.md`；通过 `RHEL_SOURCE_ROOT=/path/to/rhel-sources` 指向本地版权资料，不提交课件、字体或 OCR 临时文件。完整 v5.1 证据见 `reports/RHCSA_V5_1_INTEGRATION_REPORT.md`。
# 正式阅读版与 AnkiConnect

RHCSA 正式 PDF 默认采用大字号阅读版：无页眉、页脚和页码；概念全宽单列、术语加粗换色，定义与已有理解说明分层；操作语义采用可查询的 man-page 风格，重要参数逐项排列。详见 `docs/specs/PDF大字号阅读版排版规范.md`。

```bash
uv run python tools/doctor.py
uv run python tools/build.py rhcsa --profile reading --all-chapters
```

PDF 输出在 `dist/rhcsa/reading/`。APKG 是离线包，与 AnkiConnect 写入不同。同步先执行 `uv run python tools/sync_anki.py --all` dry-run；确认 Anki 正在运行且全部门禁通过后，才使用 `--apply --yes`。工具在写入前保存 Note JSON 快照，按稳定 ID 幂等新增或更新，绝不删除用户其他 Note；正式卡片保留 Source 字段但不显示它。完整流程见 `docs/guides/AnkiConnect同步.md`。
