# 构建指南

安装依赖并运行静态门禁：

```bash
uv sync
uv run pytest
uv run python tools/audit.py rhcsa
```

单章、全部单章与正式 RHCSA 构建：

```bash
uv run python tools/build.py rhcsa --chapter lvm
uv run python tools/build.py rhcsa --all-chapters
uv run python tools/build.py rhcsa
```

存在未 validated 章节时，正式命令会失败。内部预览必须显式使用 `--allow-incomplete`，输出文件名包含 `INCOMPLETE-PREVIEW`。生成物位于忽略的 `build/` 与 `dist/`。
