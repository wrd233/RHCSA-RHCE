---
title: "第十一章 Ansible 故障排除、验证与幂等性"
chapter_id: RHCE-TROUBLESHOOTING
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE9-Mock, Ansible-Documentation]
---

# 第十一章　Ansible 故障排除、验证与幂等性

Ansible 故障首先归类为控制端解析、Inventory 匹配、SSH/提权、模块执行或远端终态。verbosity 和 register 提供证据；ignore_errors、无条件 changed_when 或 recap 绿色不能替代根因修复。

**[概念]** FAILED 表示主机可达但任务失败，UNREACHABLE 表示连接层未建立，SKIPPED 是条件未满足，CHANGED 是模块认为状态改变。它们是执行分类，不是业务结论。

**[概念]** 幂等性要求相同目标状态重复执行不再改变；正确性要求目标本身符合题意。错误配置也可能稳定幂等，因此两者必须组合。

**[操作语义]** 从 `--syntax-check/--list-hosts` 开始，使用 `-v/-vvv` 增加证据，debug 注册对象，`--step/--start-at-task` 谨慎缩小；远端协议与系统查询最终验收。

<section class="topic knowledge" id="RHCE-TROUBLESHOOTING-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 按失败层分类

### ① [知识点] 按失败层分类
YAML/模块字段在控制端；0 hosts 在 Inventory；unreachable 在 SSH；become 在 sudo；failed msg 在模块/远端；绿色 recap 后仍查终态。

### ② [知识点] changed 语义可被模块与规则改写
changed_when 应基于可靠输出，不为追求全绿无条件 false；failed_when 不能吞掉真实失败。

### ③ [验证点] 第二次执行与远端状态并行
比较两次 recap/任务 diff，同时从受管节点查文件、服务、端口、挂载和数据。

**[Cheatsheet]** 按失败层分类；changed 语义可被模块与规则改写；第二次执行与远端状态并行

</section>

<section class="topic operation" id="RHCE-TROUBLESHOOTING-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 最小化复现

### ① [操作点] 最小化复现
syntax/list/limit 单主机，使用 tags/start-at-task 前确认依赖；verbosity 只提升到能回答问题的层。

### ② [操作点] 读取 register 结构
debug var 完整结果，区分 rc/stdout/msg/results；用 assert 明确前置和验收条件。

### ③ [验证点] 修复后做全链回归
从失败层向下到远端功能，再全组执行和第二次执行；检查 Handler 是否按变化运行。

**[Cheatsheet]** 最小化复现；读取 register 结构；修复后做全链回归

</section>

<section class="topic diagnosis" id="RHCE-TROUBLESHOOTING-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 变量未定义/模板错误

### ① [诊断点] 变量未定义/模板错误
查最终 hostvars、数据类型、模板路径和 scope；不要用 default 空值掩盖。

### ② [诊断点] unreachable 被当作 task 失败
业务模块尚未执行，先修 SSH/host key/remote_user/Python。

### ③ [诊断点] 每次 changed 但终态相同
查 command/shell、mtime、随机值、模板动态内容与 module 参数；不要全局 changed_when false。

**[Cheatsheet]** 变量未定义/模板错误；unreachable 被当作 task 失败；每次 changed 但终态相同

</section>

<section class="topic knowledge" id="RHCE-TROUBLESHOOTING-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> check mode、diff 与可观测性边界

### ① [知识点] check mode 支持度取决于模块
支持 check_mode 的模块预测 changed，不支持的任务可能跳过或仍需特殊处理。不能把一次 `--check` 全绿当作真实执行成功。

### ② [验证点] diff 只显示可公开差异
`--diff` 有助于模板/文件审查，但可能暴露敏感内容；秘密任务应 no_log，并用非敏感结构证据验收。二进制或某些模块没有可读 diff。

### ③ [诊断点] start-at-task 会跳过前置状态
从中间开始可能缺少 Facts、变量设置、文件下载或 Handler 通知，只适合前置状态已明确成立的复现。最终仍从完整 Playbook 回归。

**[Cheatsheet]** check 支持度要核对；diff 注意秘密；start-at-task 不替代完整回归。

</section>

<section class="classic-task task-page" id="RHCE-TROUBLESHOOTING-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 修复一个多层故障项目

项目同时存在错误 Inventory 组、变量类型、模板字段、Handler 名称和无条件 changed。要求逐层修复，不能 ignore_errors；最终全组终态正确且第二次无无法解释 changed。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-TROUBLESHOOTING-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 按层收缩并回归

### ① [诊断点] syntax/list-hosts/inventory 先修控制与范围；ping/become 修连接。
### ② [诊断点] limit 运行，debug register/变量，修模板与 Handler。
### ③ [验证点] 远端文件/服务/端口，全组与第二次执行。

**[Cheatsheet]** 控制端 → Inventory → 连接/become → task/Handler → 远端终态 → 全量/幂等。

</section>

<section class="topic closing" id="RHCE-TROUBLESHOOTING-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 绿色执行不是最终判据

可靠排错让每个错误回到所属层，可靠验收同时看执行语义和远端事实。幂等性是正确终态的附加条件，不是替代条件。

</section>
