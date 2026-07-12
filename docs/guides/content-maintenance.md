# 内容维护

每个已集成章节只维护 `lecture.md` 与 `anki.yml`。章节顺序和状态由 `config/chapters.yml` 唯一管理；稳定 Note ID 的主归属、停用和重定向由 `config/anki-migrations.yml` 管理。

候选包默认只审计：

```bash
uv run python tools/import_candidates.py incoming/
```

确认报告后才允许写入：

```bash
uv run python tools/import_candidates.py incoming/ --apply --yes
```

导入器支持目录、单章 ZIP、批次 ZIP 和嵌套 ZIP，并验证 Manifest 与 SHA-256。
