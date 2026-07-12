---
title: "第四章 循环、条件、Handler、Block 与错误控制"
chapter_id: RHCE-CONTROL
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE-Course-05-09, RHCE9-Mock]
---

# 第四章　循环、条件、Handler、Block 与错误控制

控制结构用于对数据集合和主机差异重复表达目标，同时让变更、失败和恢复保持可解释。循环不是复制 task，Handler 不是无条件重启，错误控制也不能把必须失败的状态吞掉。

**[概念]** loop 为每项设置 item，可用 loop_control 改名；when 对每台主机和每个 item 求值。Handler 只在通知 task 返回 changed 时排队，默认在 play 后部运行。

**[概念]** block 组织任务并可配 rescue/always；failed_when 和 changed_when 改写结果语义，必须基于可靠返回字段。

**[操作语义]** `notify` 触发命名 Handler，`meta: flush_handlers` 提前运行；`assert` 把前置条件写成明确失败。

<section class="topic knowledge" id="RHCE-CONTROL-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 循环数据应保持结构

### ① [知识点] 循环数据应保持结构
字典列表让 item.name/item.state 明确。避免平行列表和基于索引拼接。loop_control.label 只改善输出，不改变数据。

### ② [知识点] when 不使用 Jinja 定界符
`when: ansible_facts['os_family'] == 'RedHat'` 是表达式；字符串布尔需要显式类型。多个条件列表通常 AND。

### ③ [知识点] Handler 合并通知
同一 Handler 被多次通知通常只运行一次；通知 task 未 changed 则不运行。配置变化才重启是幂等关键。

**[Cheatsheet]** 循环数据应保持结构；when 不使用 Jinja 定界符；Handler 合并通知

</section>

<section class="topic operation" id="RHCE-CONTROL-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 循环创建对象

### ① [操作点] 循环创建对象
使用 user/package 等专用模块遍历字典；给 loop_var 命名避免 include 嵌套 item 冲突。

### ② [操作点] 根据 register 定义结果
command 探测可用 `changed_when: false`，按 rc 定义 failed_when；但专用查询模块优先。

### ③ [验证点] 检查 changed 与 Handler 时点
第一轮配置变化应通知，第二轮无变化不应重启；必要时 flush 后再做依赖 Handler 的功能验证。

**[Cheatsheet]** 循环创建对象；根据 register 定义结果；检查 changed 与 Handler 时点

</section>

<section class="topic diagnosis" id="RHCE-CONTROL-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> ignore_errors 掩盖失败

### ① [诊断点] ignore_errors 掩盖失败
它继续执行但主机仍有失败语义，可能让后续使用无效状态。合法替代是明确 failed_when 或 block/rescue。

### ② [诊断点] Handler 未运行
查通知 task 是否 changed、notify 名称、play 是否在失败前到达 Handler，必要时 flush。

### ③ [诊断点] 每轮都 changed
查 command/shell、时间戳内容、changed_when 和模块目标值；第二次执行定位具体 task。

**[Cheatsheet]** ignore_errors 掩盖失败；Handler 未运行；每轮都 changed

</section>

<section class="topic knowledge" id="RHCE-CONTROL-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 控制结构的输出与边界检查

### ① [参数点] loop_control 不改变业务数据
`label` 只缩短终端输出，`loop_var` 改变循环变量名，`index_var` 保存索引。调试时仍应检查原始 item 结构，不能因为 label 美观就认为数据完整。

### ② [验证点] failed_when 与 changed_when 必须可复核
条件应引用稳定的 `rc`、模块字段或明确输出，不匹配本地化人类文本。执行后用 `debug: var=result` 抽查被改写的任务结果，确保真实失败没有被标成成功。

### ③ [边界] rescue 不是事务回滚
block 中前一任务已经改变的远端状态不会自动撤销。rescue 必须显式恢复需要恢复的对象，always 只适合清理、记录和无条件收束。

**[Cheatsheet]** loop_control 管输出/变量名；结果改写必须基于稳定字段；rescue 需显式恢复，不是自动回滚。

</section>

<section class="classic-task task-page" id="RHCE-CONTROL-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 批量创建服务并只在变化时重启

从字典列表安装多个包并部署配置；仅配置改变时重启对应服务。对不满足内存条件主机明确跳过，并在失败时输出可诊断信息。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-CONTROL-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 让数据、条件和 Handler 对齐

### ① [操作点] loop 字典调用 package，模板 task notify Handler。
### ② [操作点] when 使用 Facts；block/rescue 处理受控异常。
### ③ [验证点] 第一轮观察 changed/handler，第二轮确认无重启，远端查服务。

**[Cheatsheet]** 结构数据 → when → 变更通知 → Handler → 第二次执行。

</section>

<section class="topic closing" id="RHCE-CONTROL-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 控制结构应提高可解释性

循环减少重复，条件限定适用主机，Handler 绑定真实变更，block 保留失败边界。任何结构都应让 recap 和远端终态更清楚，而不是隐藏错误。

</section>
