---
title: "第五章 文件、模板与 Jinja2"
chapter_id: RHCE-TEMPLATES
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE-Course-10-11, RHCE9-Mock]
---

# 第五章　文件、模板与 Jinja2

文件自动化首先选择所有权边界：完整内容由 copy/template 管，单行由 lineinfile 管，受标记区块由 blockinfile 管。模板把变量渲染成每台主机的完整文件，错误内容也可能幂等。

**[概念]** file 管路径状态/身份/模式，copy 分发静态内容，template 渲染 Jinja2，lineinfile 维护一行，blockinfile 维护带 marker 的区块。选择过细工具修改完整受管文件会留下未知旧内容。

**[概念]** Jinja2 `{{ }}` 输出表达式，`{% %}` 控制结构，`{# #}` 注释。模板在控制节点渲染，Facts/变量来自目标主机上下文。

**[操作语义]** `template` 的 validate 在替换前用临时文件运行校验命令；成功后原子替换并 notify Handler。diff 与远端语法/功能共同验收。

<section class="topic knowledge" id="RHCE-TEMPLATES-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 按所有权选择文件模块

### ① [知识点] 按所有权选择文件模块
完整文件归项目所有用 template/copy；只拥有一行用 lineinfile；只拥有区块用 blockinfile。`file state=touch` 每次改变时间，不适合只保证存在。

### ② [知识点] 模板变量必须处理缺失与类型
用 mandatory/assert 处理必需数据；default 只用于合法默认。过滤器如 join、sort、to_nice_yaml 改变输出，要检查目标格式。

### ③ [验证点] 内容、元数据和消费者分层
`stat`/slurp/checksum 查文件，应用 `-t` 或 validate 查语法，服务 active/HTTP 查功能。

**[Cheatsheet]** 按所有权选择文件模块；模板变量必须处理缺失与类型；内容、元数据和消费者分层

</section>

<section class="topic operation" id="RHCE-TEMPLATES-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 渲染差异配置

### ① [操作点] 渲染差异配置
模板使用 inventory_hostname、组变量和 Facts；for 循环生成重复行，if 只表达真正主机差异。保持缩进与换行符合目标格式。

### ② [操作点] 安全替换并通知
template 设置 owner/group/mode、backup（按需）、validate，并 notify restart Handler；只有内容/元数据变化才 changed。

### ③ [验证点] check/diff 与远端语法
先 `--check --diff` 预览支持的变化，再 limit 执行；远端运行应用校验并查看渲染内容。

**[Cheatsheet]** 渲染差异配置；安全替换并通知；check/diff 与远端语法

</section>

<section class="topic diagnosis" id="RHCE-TEMPLATES-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 模板变量未定义

### ① [诊断点] 模板变量未定义
定位变量作用域和拼写，debug 数据结构；不在模板各处 default 空字符串。

### ② [诊断点] 渲染成功但服务失败
控制端 Jinja 合法不等于目标配置语法合法；使用 validate 和远端日志。

### ③ [诊断点] lineinfile 每次 changed
检查 regexp 是否能匹配写入后的 line，避免插入重复行；必要时选择 template。

**[Cheatsheet]** 模板变量未定义；渲染成功但服务失败；lineinfile 每次 changed

</section>

<section class="topic knowledge" id="RHCE-TEMPLATES-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 模板渲染、校验与换行细节

### ① [参数点] validate 命令使用占位符
`validate: '/usr/sbin/sshd -t -f %s'` 让模块把临时文件路径代入 `%s`。命令不经 Shell，因此管道与重定向不能直接使用；校验工具必须能读取临时路径。

### ② [知识点] Jinja 空白会改变真实配置
`trim_blocks`、`lstrip_blocks` 和 `-{%` 等控制空白。多一空行通常无害，但 YAML、sudoers、hosts 或严格配置中的缩进与末尾换行可能改变语义，必须查看 `--diff` 和远端文件。

### ③ [验证点] 模板依赖清单
模板引用的每个变量都应能从 defaults、group_vars、host_vars 或 Facts 追溯；修改模板后回归所有消费主机组，而不只测试当前 limit 主机。

**[Cheatsheet]** validate 用 `%s` 临时路径；空白控制可能改语义；diff 后回归所有模板消费者。

</section>

<section class="classic-task task-page" id="RHCE-TEMPLATES-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 为不同主机生成服务配置并安全重载

使用一个模板按 web 组变量生成监听端口和后端列表，所有者/模式固定；配置校验成功且内容变化时才重载服务。验收 diff、远端内容、语法、Handler、监听和第二次执行。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-TEMPLATES-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 让模板成为完整文件真相

### ① [操作点] 在 j2 中使用明确变量、循环与最小条件。
### ② [操作点] template 设元数据和 validate，notify reload Handler。
### ③ [验证点] check/diff、limit、远端语法/监听，第二次无 changed。

**[Cheatsheet]** 数据 → 模板 → validate → 原子替换 → Handler → 远端功能/幂等。

</section>

<section class="topic closing" id="RHCE-TEMPLATES-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 文件模块的选择决定维护边界

完整文件、单行和区块应由不同模块承担。Jinja 只负责渲染，validate 与远端功能证明内容可用；第二次执行证明表达稳定。

</section>
