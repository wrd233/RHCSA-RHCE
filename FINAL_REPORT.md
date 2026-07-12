# RHEL 9 RHCSA / RHCE 最终交付与质量报告

**最终状态：READY**

## 发布物

| 交付物 | 路径 | 页数 / 数量 |
|---|---|---:|
| RHCSA 讲义 | `releases/rhcsa/RHEL9-RHCSA-讲义.pdf` | 109 页，132 个书签 |
| RHCE 讲义 | `releases/rhce/RHEL9-RHCE-讲义.pdf` | 58 页，104 个书签 |
| 合订版 | `releases/combined/RHEL9-RHCSA-RHCE-合订版.pdf` | 160 页，225 个书签 |
| RHCSA Anki | `releases/rhcsa/RHEL9-RHCSA.apkg` | 445 Note / 478 Card |
| RHCE Anki | `releases/rhce/RHEL9-RHCE.apkg` | 190 Note / 211 Card |

## Anki 统计

| 牌组 | QA | Cloze | Note | Card | `coverage::extra` |
|---|---:|---:|---:|---:|---:|
| RHCSA | 408 | 37 | 445 | 478 | 13 |
| RHCE | 164 | 26 | 190 | 211 | 24 |
| 合计（两包；通用卡按所属考试计入） | 572 | 63 | 635 | 689 | 37 |

源 YAML 共 625 个唯一 Note；两包合计会重复计入分别属于 RHCSA 与 RHCE 的通用考试方法卡。

## 最终章节清单

| # | 章节 | 讲义 / Anki / 预览 / 摘要 / 单章 PDF |
|---:|---|---|
| 1 | 完成一场红帽实操考试的方法（COMMON-STRATEGY） | `content/common/exam-strategy/lecture.md` · `content/common/exam-strategy/anki.yml` · `content/common/exam-strategy/anki-preview.html` · `content/common/exam-strategy/anki-summary.md` · `releases/common/chapters/01-exam-strategy.pdf` |
| 2 | 命令行、Shell 与本地帮助（RHCSA-SHELL） | `content/rhcsa/chapters/shell-help/lecture.md` · `content/rhcsa/chapters/shell-help/anki.yml` · `content/rhcsa/chapters/shell-help/anki-preview.html` · `content/rhcsa/chapters/shell-help/anki-summary.md` · `releases/rhcsa/chapters/01-shell-help.pdf` |
| 3 | 文件、目录、文本处理与归档传输（RHCSA-FILES） | `content/rhcsa/chapters/files-text-archive/lecture.md` · `content/rhcsa/chapters/files-text-archive/anki.yml` · `content/rhcsa/chapters/files-text-archive/anki-preview.html` · `content/rhcsa/chapters/files-text-archive/anki-summary.md` · `releases/rhcsa/chapters/02-files-text-archive.pdf` |
| 4 | 用户、组、权限、ACL 与 sudo（RHCSA-USERS） | `content/rhcsa/chapters/users-permissions/lecture.md` · `content/rhcsa/chapters/users-permissions/anki.yml` · `content/rhcsa/chapters/users-permissions/anki-preview.html` · `content/rhcsa/chapters/users-permissions/anki-summary.md` · `releases/rhcsa/chapters/03-users-permissions.pdf` |
| 5 | 进程、作业、服务、日志与计划任务（RHCSA-SERVICES） | `content/rhcsa/chapters/processes-services-logs/lecture.md` · `content/rhcsa/chapters/processes-services-logs/anki.yml` · `content/rhcsa/chapters/processes-services-logs/anki-preview.html` · `content/rhcsa/chapters/processes-services-logs/anki-summary.md` · `releases/rhcsa/chapters/04-processes-services-logs.pdf` |
| 6 | 软件包、仓库与基础系统维护（RHCSA-PACKAGES） | `content/rhcsa/chapters/packages-repositories/lecture.md` · `content/rhcsa/chapters/packages-repositories/anki.yml` · `content/rhcsa/chapters/packages-repositories/anki-preview.html` · `content/rhcsa/chapters/packages-repositories/anki-summary.md` · `releases/rhcsa/chapters/05-packages-repositories.pdf` |
| 7 | 网络、名称解析、SSH 与 firewalld（RHCSA-NETWORK） | `content/rhcsa/chapters/network-ssh-firewall/lecture.md` · `content/rhcsa/chapters/network-ssh-firewall/anki.yml` · `content/rhcsa/chapters/network-ssh-firewall/anki-preview.html` · `content/rhcsa/chapters/network-ssh-firewall/anki-summary.md` · `releases/rhcsa/chapters/06-network-ssh-firewall.pdf` |
| 8 | 分区、文件系统、Swap 与持久挂载（RHCSA-FILESYSTEMS） | `content/rhcsa/chapters/partitions-filesystems/lecture.md` · `content/rhcsa/chapters/partitions-filesystems/anki.yml` · `content/rhcsa/chapters/partitions-filesystems/anki-preview.html` · `content/rhcsa/chapters/partitions-filesystems/anki-summary.md` · `releases/rhcsa/chapters/07-partitions-filesystems.pdf` |
| 9 | LVM 逻辑存储（RHCSA-LVM） | `content/rhcsa/chapters/lvm/lecture.md` · `content/rhcsa/chapters/lvm/anki.yml` · `content/rhcsa/chapters/lvm/anki-preview.html` · `content/rhcsa/chapters/lvm/anki-summary.md` · `releases/rhcsa/chapters/08-lvm.pdf` |
| 10 | 网络文件系统与自动挂载（RHCSA-NFS） | `content/rhcsa/chapters/nfs-autofs/lecture.md` · `content/rhcsa/chapters/nfs-autofs/anki.yml` · `content/rhcsa/chapters/nfs-autofs/anki-preview.html` · `content/rhcsa/chapters/nfs-autofs/anki-summary.md` · `releases/rhcsa/chapters/09-nfs-autofs.pdf` |
| 11 | SELinux（RHCSA-SELINUX） | `content/rhcsa/chapters/selinux/lecture.md` · `content/rhcsa/chapters/selinux/anki.yml` · `content/rhcsa/chapters/selinux/anki-preview.html` · `content/rhcsa/chapters/selinux/anki-summary.md` · `releases/rhcsa/chapters/10-selinux.pdf` |
| 12 | 启动过程、Target 与系统恢复（RHCSA-BOOT） | `content/rhcsa/chapters/boot-recovery/lecture.md` · `content/rhcsa/chapters/boot-recovery/anki.yml` · `content/rhcsa/chapters/boot-recovery/anki-preview.html` · `content/rhcsa/chapters/boot-recovery/anki-summary.md` · `releases/rhcsa/chapters/11-boot-recovery.pdf` |
| 13 | Podman 容器与持久运行（RHCSA-PODMAN） | `content/rhcsa/chapters/podman/lecture.md` · `content/rhcsa/chapters/podman/anki.yml` · `content/rhcsa/chapters/podman/anki-preview.html` · `content/rhcsa/chapters/podman/anki-summary.md` · `releases/rhcsa/chapters/12-podman.pdf` |
| 14 | RHCSA 综合任务（RHCSA-COMPREHENSIVE） | `content/rhcsa/chapters/comprehensive/lecture.md` · `content/rhcsa/chapters/comprehensive/anki.yml` · `content/rhcsa/chapters/comprehensive/anki-preview.html` · `content/rhcsa/chapters/comprehensive/anki-summary.md` · `releases/rhcsa/chapters/13-comprehensive.pdf` |
| 15 | Ansible 架构、配置与 Inventory（RHCE-INVENTORY） | `content/rhce/chapters/architecture-inventory/lecture.md` · `content/rhce/chapters/architecture-inventory/anki.yml` · `content/rhce/chapters/architecture-inventory/anki-preview.html` · `content/rhce/chapters/architecture-inventory/anki-summary.md` · `releases/rhce/chapters/01-architecture-inventory.pdf` |
| 16 | YAML、Playbook、Task 与模块（RHCE-PLAYBOOK） | `content/rhce/chapters/yaml-playbook-modules/lecture.md` · `content/rhce/chapters/yaml-playbook-modules/anki.yml` · `content/rhce/chapters/yaml-playbook-modules/anki-preview.html` · `content/rhce/chapters/yaml-playbook-modules/anki-summary.md` · `releases/rhce/chapters/02-yaml-playbook-modules.pdf` |
| 17 | 变量、Facts、注册结果与优先级（RHCE-VARIABLES） | `content/rhce/chapters/variables-facts/lecture.md` · `content/rhce/chapters/variables-facts/anki.yml` · `content/rhce/chapters/variables-facts/anki-preview.html` · `content/rhce/chapters/variables-facts/anki-summary.md` · `releases/rhce/chapters/03-variables-facts.pdf` |
| 18 | 循环、条件、Handler、Block 与错误控制（RHCE-CONTROL） | `content/rhce/chapters/loops-conditionals-handlers/lecture.md` · `content/rhce/chapters/loops-conditionals-handlers/anki.yml` · `content/rhce/chapters/loops-conditionals-handlers/anki-preview.html` · `content/rhce/chapters/loops-conditionals-handlers/anki-summary.md` · `releases/rhce/chapters/04-loops-conditionals-handlers.pdf` |
| 19 | 文件、模板与 Jinja2（RHCE-TEMPLATES） | `content/rhce/chapters/files-templates-jinja/lecture.md` · `content/rhce/chapters/files-templates-jinja/anki.yml` · `content/rhce/chapters/files-templates-jinja/anki-preview.html` · `content/rhce/chapters/files-templates-jinja/anki-summary.md` · `releases/rhce/chapters/05-files-templates-jinja.pdf` |
| 20 | 外部数据、敏感变量与 Vault（RHCE-VAULT） | `content/rhce/chapters/external-data-vault/lecture.md` · `content/rhce/chapters/external-data-vault/anki.yml` · `content/rhce/chapters/external-data-vault/anki-preview.html` · `content/rhce/chapters/external-data-vault/anki-summary.md` · `releases/rhce/chapters/06-external-data-vault.pdf` |
| 21 | Include、Import、Role 与 Collection（RHCE-ROLES） | `content/rhce/chapters/roles-collections/lecture.md` · `content/rhce/chapters/roles-collections/anki.yml` · `content/rhce/chapters/roles-collections/anki-preview.html` · `content/rhce/chapters/roles-collections/anki-summary.md` · `releases/rhce/chapters/07-roles-collections.pdf` |
| 22 | 自动化用户、软件包、仓库、服务与计划任务（RHCE-SYSTEM） | `content/rhce/chapters/automate-system-services/lecture.md` · `content/rhce/chapters/automate-system-services/anki.yml` · `content/rhce/chapters/automate-system-services/anki-preview.html` · `content/rhce/chapters/automate-system-services/anki-summary.md` · `releases/rhce/chapters/08-automate-system-services.pdf` |
| 23 | 自动化网络、防火墙与 SELinux（RHCE-NETWORK） | `content/rhce/chapters/automate-network-selinux/lecture.md` · `content/rhce/chapters/automate-network-selinux/anki.yml` · `content/rhce/chapters/automate-network-selinux/anki-preview.html` · `content/rhce/chapters/automate-network-selinux/anki-summary.md` · `releases/rhce/chapters/09-automate-network-selinux.pdf` |
| 24 | 自动化存储、文件系统与挂载（RHCE-STORAGE） | `content/rhce/chapters/automate-storage/lecture.md` · `content/rhce/chapters/automate-storage/anki.yml` · `content/rhce/chapters/automate-storage/anki-preview.html` · `content/rhce/chapters/automate-storage/anki-summary.md` · `releases/rhce/chapters/10-automate-storage.pdf` |
| 25 | Ansible 故障排除、验证与幂等性（RHCE-TROUBLESHOOTING） | `content/rhce/chapters/troubleshooting-idempotency/lecture.md` · `content/rhce/chapters/troubleshooting-idempotency/anki.yml` · `content/rhce/chapters/troubleshooting-idempotency/anki-preview.html` · `content/rhce/chapters/troubleshooting-idempotency/anki-summary.md` · `releases/rhce/chapters/11-troubleshooting-idempotency.pdf` |
| 26 | RHCE 综合任务（RHCE-COMPREHENSIVE） | `content/rhce/chapters/comprehensive/lecture.md` · `content/rhce/chapters/comprehensive/anki.yml` · `content/rhce/chapters/comprehensive/anki-preview.html` · `content/rhce/chapters/comprehensive/anki-summary.md` · `releases/rhce/chapters/12-comprehensive.pdf` |

## 覆盖与构建检查

- 26/26 章的 Markdown、Anki YAML、HTML 预览、覆盖摘要与单章 PDF 均存在且非空。
- 讲义校验覆盖章首概念/操作语义、正式专题、稳定专题 ID、Cheatsheet、经典任务与答案强制分页、代码块闭合及占位/维护元数据禁用。
- Anki 校验覆盖 YAML schema、QA/Cloze 合法性、全局稳定 ID 唯一、必需标签、来源字段、重复提取目标及 Cloze 编号上限。
- APKG 已直接解包并查询 SQLite：Note/Card 数与源 YAML 推导一致；仅含 `RedHat-QA`、`RedHat-Cloze`，牌组名正确。
- 三本完整 PDF 均有页码、目录与正式专题书签；全文扫描未发现内部维护元数据。
- 经典任务题面与参考解答使用独立强制分页区，避免答案与题面同页泄露。

完整重建命令：

```bash
.venv/bin/python tools/build_release.py
.venv/bin/python tools/final_audit.py --write-report
```

## 静态不确定项

- 命令、模块参数与题解经过静态资料交叉整理和语法级检查，但本交付没有在一套真实 RHEL 9 / Ansible 考试环境中逐条执行；实际操作仍应以当前安装版本的 `man`、`--help`、`ansible-doc` 和目标机状态为准。
- PDF 已进行代表性页面的视觉检查和全量结构扫描；不同 PDF 阅读器的字体渲染、书签展开状态可能略有差异。
- APKG 已做包内数据库检查，但按 Goal 明确边界未导入现有 Anki 档案。

## AnkiConnect 边界

**本次构建、审计和交付均未调用 AnkiConnect，也没有向现有 Anki 写入任何内容。** `tools/sync_anki.py` 仅作为后续明确授权后的同步入口；默认模式只输出 dry-run，实际写入必须同时提供 `--apply --yes`。
