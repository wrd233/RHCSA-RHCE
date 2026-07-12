---
title: "第三章 变量、Facts、注册结果与优先级"
chapter_id: RHCE-VARIABLES
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE-Course-06-07, RHCE9-Mock]
---

# 第三章　变量、Facts、注册结果与优先级

变量把同一自动化逻辑映射到不同主机；Facts 描述受管节点，register 保存某个任务的运行结果。正确性取决于变量来源、数据类型、主机作用域和实际返回结构。

**[概念]** 变量可来自 Inventory、group_vars、host_vars、play vars、vars_files、Facts、register、set_fact 和 extra vars；高优先级覆盖低优先级，但考试重点是减少冲突而非背完整表。

**[概念]** Facts 是每台主机的数据；magic variables 如 inventory_hostname、groups、hostvars 描述 Inventory 上下文。register 结果是字典，字段随模块与循环改变。

**[操作语义]** `ansible-inventory --host` 观察 Inventory 变量；`ansible -m setup -a filter=...` 查询 Facts；`debug: var=` 显示对象结构而不套 Jinja 双括号。

<section class="topic knowledge" id="RHCE-VARIABLES-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 变量来源与作用域

### ① [知识点] 变量来源与作用域
group_vars/all 作用全体，组文件作用组，host_vars 作用单主机。文件名必须与 Inventory 名称对应；把同一变量在多层重复定义会让覆盖难以审计。

### ② [知识点] Facts 与 magic variables
`ansible_facts['distribution']` 等来自远端采集；`inventory_hostname` 不要求 DNS 可解析，`ansible_host` 是连接地址。`groups['web']` 是主机名列表，`hostvars[h]` 访问另一主机变量。

### ③ [验证点] 先看类型和最终值
使用 `debug: var=myvar`、type_debug 过滤器和 inventory --host。字符串 `false` 与布尔 false 不同，when 中尤其危险。

**[Cheatsheet]** 变量来源与作用域；Facts 与 magic variables；先看类型和最终值

</section>

<section class="topic operation" id="RHCE-VARIABLES-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 组织 group_vars 与 host_vars

### ① [操作点] 组织 group_vars 与 host_vars
将共同值放 `group_vars/all.yml`，组差异放 `group_vars/web.yml`，主机例外放 `host_vars/servera.yml`；复杂数据使用 YAML 列表/字典。

### ② [操作点] 注册并读取结果
`command` 任务 `register: check` 后读取 `check.rc/stdout/stderr/changed`；循环 register 的单项结果位于 `results`。不要假设所有模块都有 stdout。

### ③ [验证点] 按主机显示并应用差异
先 debug 代表主机的变量/Facts，再 limit 执行；最终在每组受管节点检查差异化文件和服务。

**[Cheatsheet]** 组织 group_vars 与 host_vars；注册并读取结果；按主机显示并应用差异

</section>

<section class="topic diagnosis" id="RHCE-VARIABLES-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 变量未定义

### ① [诊断点] 变量未定义
用 -vvv、debug 和 inventory --host 查拼写、文件名、作用域和条件分支，不用 default 隐藏必需变量缺失。

### ② [诊断点] 字典字段不存在
先 debug 完整 register/Facts 结构，循环结果尤其查看 results；不要从示例版本推定字段。

### ③ [诊断点] 值正确但类型错误
用 type_debug 检查引号导致的字符串/布尔/整数差异，修正数据源而非在每个 task 强制转换。

**[Cheatsheet]** 变量未定义；字典字段不存在；值正确但类型错误

</section>

<section class="classic-task task-page" id="RHCE-VARIABLES-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 用组变量和 Facts 部署差异配置

web 与 db 组使用不同包、端口和模板值；RHEL 9 才执行目标任务。不得复制两份 Playbook。验收最终变量、Facts 条件、每组文件和服务。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-VARIABLES-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 把差异放入数据并验证返回结构

### ① [操作点] 在 group_vars 定义 `service_package/service_port`，用 Facts 条件限制 RHEL 9。
### ② [操作点] 注册验证命令并根据 rc 显示明确结果。
### ③ [验证点] inventory --host、debug type、limit 与远端文件/监听交叉检查。

**[Cheatsheet]** 数据源 → 类型 → host 最终值 → limit 执行 → 每组终态。

</section>

<section class="topic closing" id="RHCE-VARIABLES-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 变量只有在主机上下文中才有确定值

把共享值、组差异和主机例外放在最小层次；Facts 与 register 先观察结构再引用。这样优先级不再是猜测，而是可查询的数据合并结果。

</section>
