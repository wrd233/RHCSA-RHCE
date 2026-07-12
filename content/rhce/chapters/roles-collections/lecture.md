---
title: "第七章 Include、Import、Role 与 Collection"
chapter_id: RHCE-ROLES
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE9-Mock, Ansible-Documentation]
---

# 第七章　Include、Import、Role 与 Collection

内容拆分必须保留执行边界。import 在解析期静态展开，include 在运行期动态选择；Role 用固定目录把 tasks、handlers、templates、files 和变量组织为可复用接口；Collection 提供 FQCN、Role 和插件版本。

**[概念]** include_tasks 动态执行并可按 loop/when 选择；import_tasks 静态展开，适合固定结构和 list-tasks。import_playbook 只能在 playbook 顶层。

**[概念]** Role defaults 是低优先级可覆盖接口，vars 更强不适合作为用户配置入口。Collection requirements 锁定依赖来源/版本，FQCN 避免模块名冲突。

**[操作语义]** `ansible-galaxy role init` 创建 Role 骨架，`ansible-galaxy collection install -r requirements.yml` 安装依赖；`ansible-doc -t role`/模块文档查接口。

<section class="topic knowledge" id="RHCE-ROLES-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 动态与静态复用

### ① [知识点] 动态与静态复用
import 在解析时展开，标签/list-tasks 可见；include 在运行时根据变量与循环决定。不要只背先后，按是否需要运行时选择。

### ② [知识点] Role 目录和变量接口
tasks/main.yml 是入口，handlers/templates/files 自动按 Role 路径解析；defaults 提供可覆盖默认值，meta 声明依赖。

### ③ [验证点] 依赖与路径可复现
requirements 文件进入项目；离线/考试材料按给定 tar/路径安装，`ansible-galaxy collection list` 核对实际版本。

**[Cheatsheet]** 动态与静态复用；Role 目录和变量接口；依赖与路径可复现

</section>

<section class="topic operation" id="RHCE-ROLES-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 把单文件重构为 Role

### ① [操作点] 把单文件重构为 Role
移动任务、Handler、模板和文件，不改变 notify 名称与变量语义；把环境差异转为 defaults 或调用时 vars。

### ② [操作点] 安装并使用 Collection/System Role
requirements 指定 name/source/version；Playbook 用 FQCN 和 `roles:` 调用，阅读 Role README/defaults 获取变量 schema。

### ③ [验证点] 语法、任务图与远端终态
syntax-check、list-tasks/tags、limit 执行；Role 重构前后远端终态与第二次执行一致。

**[Cheatsheet]** 把单文件重构为 Role；安装并使用 Collection/System Role；语法、任务图与远端终态

</section>

<section class="topic diagnosis" id="RHCE-ROLES-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 找不到 Role/Collection

### ① [诊断点] 找不到 Role/Collection
检查 roles_path/collections_paths、项目目录、requirements 安装位置和名称空间，不复制内容到随机路径。

### ② [诊断点] 变量无法覆盖
检查是否错误放在 role vars 而非 defaults，以及调用层变量名/schema。

### ③ [诊断点] include 标签行为意外
动态 include 的标签不会自动以相同方式传播到内部 task；按文档使用 apply 或给内部任务标签。

**[Cheatsheet]** 找不到 Role/Collection；变量无法覆盖；include 标签行为意外

</section>

<section class="topic knowledge" id="RHCE-ROLES-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> Role 接口、依赖与标签传播

### ① [知识点] defaults 是公开接口，不是所有变量仓库
调用者需要覆盖的值进入 defaults；Role 内部常量可放 vars，但过强优先级会阻止环境差异。变量名加 Role 前缀可减少多 Role 冲突。

### ② [参数点] requirements 可同时描述 Role 与 Collection
实际项目可分 `roles/requirements.yml` 与 `collections/requirements.yml`，也可按工具支持格式组织。离线 tarball 的 source 与版本要保持题目给定 lineage，不擅自换最新版。

### ③ [验证点] 重构前后比较任务与 Handler
`--list-tasks`、tags、远端 diff 和第二次执行共同证明移动内容没有丢失 Handler、模板路径或变量覆盖。

**[Cheatsheet]** defaults 暴露接口；requirements 固定真实依赖；重构用任务图、远端 diff 与幂等证明等价。

</section>

<section class="classic-task task-page" id="RHCE-ROLES-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 把 Web Playbook 重构为可复用 Role

创建 web_role，包含包、模板、Handler 和服务；默认端口可由组变量覆盖。通过 requirements 安装题目 Collection，并用新 Playbook 调用。验收依赖、任务图、两组差异、Handler 和幂等性。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-ROLES-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 保留行为地移动内容

### ① [操作点] role init，移动 tasks/handlers/templates/files，接口值放 defaults。
### ② [操作点] requirements 安装 Collection，以 FQCN 调用。
### ③ [验证点] syntax/list-tasks、limit、全量、远端终态、第二次执行。

**[Cheatsheet]** 依赖安装 → Role 接口 → 静态边界 → 远端等价 → 幂等。

</section>

<section class="topic closing" id="RHCE-ROLES-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 复用的价值是稳定接口而非更多目录

选择 include/import 的时点语义，Role 用 defaults 暴露最小接口，Collection 用 requirements 固定依赖。重构完成必须证明远端行为未改变。

</section>
