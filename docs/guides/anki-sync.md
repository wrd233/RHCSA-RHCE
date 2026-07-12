# Anki 同步边界

APKG 构建不会连接 AnkiConnect。`tools/sync_anki.py` 默认只输出计划；只有同时传入 `--apply --yes` 才会联系本机 AnkiConnect。同步按稳定 ID 更新，不永久删除 Note，并读取集中迁移配置作为身份审计真源。
