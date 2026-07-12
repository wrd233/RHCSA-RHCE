# AnkiConnect 同步

APKG 是离线构建物；AnkiConnect 同步是对正在运行的 Anki 的显式写操作。canonical 数据只来自 `content/**/anki.yml` 与 `config/anki-migrations.yml`。

先验证与预演：

```bash
uv run python tools/validate_anki.py
uv run python tools/sync_anki.py --all
```

预演不连接 AnkiConnect。正式同步必须同时给出两个开关：

```bash
uv run python tools/sync_anki.py --all --apply --yes --report reports/anki-sync.json
```

同步以 `ID` 字段定位 Note：不存在则新增；字段或标签变化才更新；相同则 unchanged；disabled 不导入也不改动现有用户卡；源中消失的 Note 不删除。写入前会保存 `backups/anki/*.notes.json` 回读快照。若同 ID 重复、模型字段不兼容或 AnkiConnect 不可达，工具真实失败并停止。Source 字段保留供 Browser 维护，但正式模板不渲染 Source。

