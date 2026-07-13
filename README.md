# RHEL 9 RHCSA / RHCE 内容工程

本仓库以 Markdown 讲义和 YAML Anki Note 为唯一内容真源，提供候选包导入、静态校验、统一 PDF/APKG 构建和显式 Anki 同步工具。二进制生成物与原始课程资料不进入 Git。

## 当前状态

- RHCSA：33/33 个 v5.1 冻结章节已发布，但 v5.1 的最终化验证被阻塞：GitHub Release 只有 38 项资产（缺 Anki HTML 预览与摘要），且正式 PDF 存在阅读组件分页回归。详见 `reports/RHCSA_V5_1_FINAL_REPORT.md`。
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

`build/`、`dist/`、`incoming/`、候选 ZIP/PDF/APKG、原始课件和缓存均被忽略。唯一正式本地发布入口为 `releases/rhcsa-v5.1/`，构建报告与校验规则进入 Git。

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

正式命令要求对应考试全部章节为 `validated` 或 `released`；否则失败。渲染器不猜概念语义，只消费显式 concept 与 operation quickref；整书由 33 个已验收单章 PDF 原样合并，不进行二次重排。当前 v5.1 公开 PDF 的分页回归已在本地修复候选中消除，但必须以 `v5.1.1` 发布，不能移动 v5.1 tag；无 RHEL 9 命令级 live test。

## Anki 安全边界

APKG Model 包含 `Source` 字段，但正式卡面不显示它。构建从不隐式调用 AnkiConnect；`tools/sync_anki.py --all` 默认 dry-run，只有 `--apply --yes` 才执行稳定 ID upsert。同步后使用 `uv run python tools/anki_readback.py --output reports/anki-readback-v5.1.json` 验证。

外部资料策略见 `docs/guides/external-sources.md`；通过 `RHEL_SOURCE_ROOT=/path/to/rhel-sources` 指向本地版权资料，不提交课件、字体或 OCR 临时文件。当前 v5.1 状态与证据见 `reports/RHCSA_V5_1_FINAL_REPORT.md`。
# 正式阅读版与 AnkiConnect

RHCSA 正式 PDF 默认采用大字号阅读版：无页眉、页脚和页码；显式概念组件全宽单列、术语加粗换色，作者的自然完整解释保持原样；显式操作速查提供 SYNOPSIS 和纵向参数。详见 `docs/specs/PDF大字号阅读版排版规范.md`。

```bash
uv run python tools/doctor.py
uv run python tools/build.py rhcsa --profile reading --all-chapters
```

PDF 输出在 `releases/rhcsa-v5.1/`。APKG 是离线包，与 AnkiConnect 写入不同。本次 PDF 修复只执行 canonical dry-run/readback，没有向 AnkiConnect 重复导入 Note。以后同步仍须先执行 `uv run python tools/sync_anki.py --all` dry-run；只有明确需要写入时才使用 `--apply --yes`。正式卡片保留 Source 字段但不显示它。完整流程见 `docs/guides/AnkiConnect同步.md`。
