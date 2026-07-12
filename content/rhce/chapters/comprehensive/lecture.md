---
title: "第十二章 RHCE 综合任务"
chapter_id: RHCE-COMPREHENSIVE
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE9-Mock, Ansible-Documentation]
---

# 第十二章　RHCE 综合任务

RHCE 综合任务把项目配置、变量、Vault、Role 和系统状态组合为一套多节点声明。完成标准不是 Playbook 数量，而是所有目标主机被正确覆盖、秘密安全、远端终态正确且第二次执行稳定。

**[概念]** 控制面包含 ansible.cfg、Inventory、requirements、group_vars/host_vars、Vault、templates 和 roles；数据面是受管节点上的用户、包、服务、网络、安全和存储。

**[概念]** 执行应从静态边界到单主机，再到主机组和全量；每个阶段保留 recap 与远端证据。

**[操作语义]** 发布入口是可重复的构建/执行命令；`--syntax-check`、inventory graph、requirements install、vault access、limit/full/idempotence 和远端验收构成主链。

<section class="topic knowledge" id="RHCE-COMPREHENSIVE-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 先审计项目完整性

### ① [知识点] 先审计项目完整性
确认题目要求的文件路径、名称、权限、Vault 密文、Role/Collection 依赖和 Inventory 组均存在；不从任意工作目录执行。

### ② [知识点] 桥接 RHCSA 目标为模块 state
用户/包/服务/防火墙/SELinux/存储使用专用模块或 System Roles；shell 仅补明确缺口并定义 changed/failed。

### ③ [验证点] 每组主机有独立终态矩阵
web、db、balancer 等分别核对变量差异、文件、服务、端口和安全；inventory 漏主机不会在 recap 中自动报错。

**[Cheatsheet]** 先审计项目完整性；桥接 RHCSA 目标为模块 state；每组主机有独立终态矩阵

</section>

<section class="topic operation" id="RHCE-COMPREHENSIVE-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 执行前门

### ① [操作点] 执行前门
安装 requirements，vault view，syntax/list-hosts/list-tasks；ping/become；check/diff（支持范围）。

### ② [操作点] 从一台到全量
limit 代表主机，修复控制/连接/task 问题并验远端；扩组、全量，观察 Handler 与失败分类。

### ③ [验证点] 第二次执行和外部功能
再次全量，解释 changed；从客户端验证 HTTP/网络，从节点验证身份、包、服务、SELinux、mount 和数据。

**[Cheatsheet]** 执行前门；从一台到全量；第二次执行和外部功能

</section>

<section class="topic diagnosis" id="RHCE-COMPREHENSIVE-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 全绿但漏主机

### ① [诊断点] 全绿但漏主机
对照题目与 `--list-hosts`/Inventory graph，不能只看 recap 中出现的主机。

### ② [诊断点] 秘密或生成物泄露
检查 debug/no_log、明文密码文件权限、构建输出和版本控制；保持 Vault 加密。

### ③ [诊断点] 修一组破坏另一组
把差异移到变量/模板条件，回归所有共享 Role 消费者；不要复制分叉 Role。

**[Cheatsheet]** 全绿但漏主机；秘密或生成物泄露；修一组破坏另一组

</section>

<section class="topic knowledge" id="RHCE-COMPREHENSIVE-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 交付目录、命名与可重复执行入口

### ① [验证点] 题目要求的路径本身可能评分
Inventory、ansible.cfg、playbook、Vault、templates 和 roles 必须位于指定绝对路径并具备正确权限。内容等价但文件名或入口错误仍可能无法被评分命令发现。

### ② [知识点] 控制节点产物与受管节点产物分开
template 源、requirements 和 Vault 留在控制端；目标配置、用户和挂载在远端。验证脚本要明确在哪一端执行，不能看到控制端文件就判定远端完成。

### ③ [验证点] 最终执行记录可重现
从项目目录运行固定命令，记录 inventory graph、syntax、首次/第二次 recap 和远端矩阵。清理临时明文与 debug 任务，但不删除题目要求的内容源。

**[Cheatsheet]** 路径/命名是接口；控制端与远端对象分开；固定入口重现首次、二次与远端矩阵。

</section>

<section class="classic-task task-page" id="RHCE-COMPREHENSIVE-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 完成一个多组主机自动化项目

建立指定 Inventory/配置、Vault 与 Role，配置用户、仓库、包、模板/Handler、网络、防火墙/SELinux、LVM/mount，并使用 requirements。不得泄露秘密或掩盖错误。验收文件路径、主机覆盖、各组终态、外部功能与第二次执行。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-COMPREHENSIVE-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 按发布门连续推进

### ① [操作点] 审计项目/依赖/Vault/Inventory，syntax/list/ping/become。
### ② [操作点] limit 代表主机，远端验收；扩组与全量。
### ③ [验证点] 全量第二次执行；按主机组矩阵查身份/服务/网络/安全/存储与外部功能。

**[Cheatsheet]** 项目完整性 → 静态/连接 → 单机 → 分组/全量 → 远端矩阵 → 幂等/安全审计。

</section>

<section class="topic closing" id="RHCE-COMPREHENSIVE-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 自动化交付是可复现的正确终态

项目源、依赖、秘密和执行边界必须可重建；受管节点的目标状态必须由专用模块表达并由外部证据验证；第二次执行则证明这种正确状态可以稳定维持。

</section>
