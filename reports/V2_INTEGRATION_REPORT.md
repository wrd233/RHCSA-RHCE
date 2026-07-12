# RHCSA V2 集成报告

## Git 基线

- 起始分支：`codex/knowledge-architecture-v2`
- 起始 commit：`1bfbe4674449be6a2d7e005a0ced30af493b2192`
- 起始最近提交：`1bfbe46`、`e37b7f1`、`39e873d`、`6bbf51e`
- 起始 tracked 文件：201
- 输入状态：33 个未跟踪 RHCSA 候选 ZIP；无已跟踪用户修改
- 安全标签：`pre-v2-integration-20260712`（仅本地）
- 集成分支：`codex/rhcsa-candidate-integration-v2`
- 最终分支：本地集成分支 `codex/rhcsa-candidate-integration-v2`；最终 commit 为本报告所在 Git commit（`git rev-parse HEAD`）；推送目标：`origin/main`。

## 候选批次

- 自动发现：33；接受：33；拒绝：0；范围：RHCSA-01～RHCSA-33，无缺章或重复 Chapter ID。
- 33/33 `manifest.yml` 可解析，Chapter ID/slug 合法，`lecture.md`/`anki.yml` 存在，声明文件 SHA-256 全部匹配。
- 候选统计：841,567 个讲义字符；3,413 Note（3,346 active / 67 disabled）；279 页候选审阅 PDF。
- 所有 Manifest 均声明静态验证且 `live_test: not_performed`；候选 PDF/HTML/摘要/source-map/逐章 QA 报告仅用于审计，未进入 canonical 内容。
- 导入工具的机器索引生成于忽略路径 `build/import-audit/package-index.json`，输入 ZIP 在审计和导入完成后删除。

## 内容集成

- RHCSA-01～33 的 `lecture.md` / `anki.yml` 已写入 `content/rhcsa/chapters/<slug>/`。
- 可见候选维护说明被移除，frontmatter 保留静态验证边界；缺失的隐藏 Section ID 与任务/答案分页标记做了最小规范化。
- 通用考试方法保留为 canonical；不计入 33 个技术章节。
- RHCE 旧 25 目录未通过当前 V2 讲义门（49 个结构性错误），且来源于旧批量工具，因此从活动内容树移除，25 章规划全部标记 `pending`。Git 历史保留旧版本。

## Anki

- 候选：3,413 Note；归一化后：3,335 canonical active Note。
- 67 个章节内 disabled 记录集中为 65 个全局停用 ID，写入 `config/anki-migrations.yml`，不再重复污染章节 YAML。
- 初审发现 49 个重复 ID，其中 9 个 active-active；9 个均按提取目标主归属保留单一 canonical Note，其余副本删除并逐项记录。
- 归一化后：全局重复 active ID 0；chapter tag 错误 0；综合章统一为 `chapter::comprehensive`；Source 完整率 100%，且使用字符串列表。
- 优先级候选分布：P0 2,564 / P1 745 / P2 104；去重、迁移与维护型卡片移除后：P0 2,553 / P1 742 / P2 40。未为制造比例而机械改写卡片。
- APKG/AnkiConnect Model 均包含 `Source`；本轮未调用 AnkiConnect。

## 清理

- 删除旧 release/PDF/APKG、旧逐章二进制、examples、旧 RHCE 迁移内容、重复规范、旧最终报告、初始审计、一次性 seed/enrich/content_factory/source extraction 工具。
- 删除 33 个输入 ZIP、候选解包目录、`build/`、`tmp/`、`sources/`、缓存和 macOS 元数据。
- `build/`、`dist/`、`releases/`、候选 ZIP/PDF/APKG、原始来源目录全部忽略；活动树不建立 archive/legacy/backup。
- 清理只影响当前树，Git 历史中的旧大 blob 仍存在；未执行历史重写。

## 构建与校验

- Manifest/Hash：33/33 通过。
- RHCSA lecture 静态门：0 错误（保留操作专题验证标记类警告，不冒充 live test）。
- RHCSA Anki：33 文件 / 3,337 Note / 0 错误。
- 全局 Section ID、Note ID、chapter tag、Source、Cloze、迁移引用和仓库清洁门由 `tools/audit.py` 与 pytest 覆盖。
- 单章构建：33/33 PDF 与 33/33 Anki preview 成功。
- 正式整书：`dist/rhcsa/RHEL9-RHCSA-讲义.pdf`，582 页，含书签。
- 正式 APKG：`dist/rhcsa/RHEL9-RHCSA.apkg`，SQLite 审计为 3,353 Note / 3,700 Card（含 18 个通用考试方法 Note）；Model 仅 `RedHat-QA` / `RedHat-Cloze`，均含 `Source` 字段。
- SHA-256：PDF `9c11e503115128a8e1c7a56272803672d204f1676522edefb3be4d9126604d7b`；APKG `f47957a4d0e179b041e60eeb696ab89ee1dc936feeed66ba227ae8883893a5c2`。
- pytest：12 passed；`tools/audit.py rhcsa`：0 error；RHCE 正式构建按 25 个 pending 章节正确阻断。

## 高风险静态复核边界

重点章节 RHCSA-12、17、18、21～25、28～32 的候选 QA/source-map 与讲义结构已纳入静态审计，检查了当前/持久边界、破坏性路径、fstab 风险、XFS/LVM 缩容限制、SELinux 最小授权和 Quadlet 版本敏感性。此次没有逐条重新创作或宣称完成 65 万字符事实复核。

代表性高风险断言使用 Red Hat 官方 RHEL 9 文档复核：

| 章节 | 复核断言 | 官方来源 | 结果 |
|---|---|---|---|
| RHCSA-23/25 | XFS 只能增长、不能缩小；不得在 XFS 上用 LV 缩容冒险 | [RHEL 9 Managing file systems](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/managing_file_systems/managing_file_systems) | 讲义边界一致，无需技术改写 |
| RHCSA-24 | `/etc/fstab` 会由 `systemd-fstab-generator` 转换为 mount unit，修改后应 reload 并实际试挂载 | [RHEL 9 Persistently mounting file systems](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/managing_file_systems/assembly_persistently-mounting-file-systems_managing-file-systems) | 当前/持久/重启证据分层一致 |
| RHCSA-28/29 | SELinux 拒绝应先查标签/配置，不把 `audit2allow` 当第一修复；持久标签用 `semanage fcontext` + `restorecon` | [RHEL 9 Troubleshooting SELinux](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/troubleshooting-problems-related-to-selinux_using-selinux) | 最小授权与诊断顺序一致 |
| RHCSA-32 | Quadlet 从 Podman 4.6 起可用；rootless 搜索路径包含用户 `containers/systemd` 目录 | [RHEL 9 Porting containers to systemd](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/building_running_and_managing_containers/assembly_porting-containers-to-systemd-using-podman_building-running-and-managing-containers) | 版本敏感性与路径表述一致 |

双轴提交前审查还发现若干 learner-facing 候选封面、`qa-report` 和生成会话状态泄漏；这些不属于技术内容，已从讲义/卡片移除，相关纯维护 Note 集中停用。未发现需要在本轮改写的上述四类技术断言。

当前没有可依赖的 RHEL 9 VM。Manifest/Hash 通过、静态内容门通过、PDF/APKG 构建成功都不等于命令在真实 RHEL 9 上已实测；后续应在受控 VM 对高风险章节按破坏性隔离、重启持久性和功能证据分层验证。
