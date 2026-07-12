---
title: "第六章 外部数据、敏感变量与 Vault"
chapter_id: RHCE-VAULT
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE-Course-06-12, RHCE9-Mock]
---

# 第六章　外部数据、敏感变量与 Vault

外部变量把用户、服务和环境数据从任务逻辑中分离；Vault 只加密静态内容，不自动隐藏运行时输出。正确流程同时保证数据结构可解析、秘密在磁盘中加密、运行时可解密且日志不泄露。

**[概念]** vars_files 显式加载数据文件，group_vars/host_vars 按 Inventory 自动加载。YAML 列表适合对象集合，字典适合按名称索引；稳定 schema 比在 task 中兼容多种形状更可靠。

**[概念]** Vault 可加密整个文件或单个字符串。vault ID 允许多个密码来源；密码文件本身必须受保护且不进入发布内容。

**[操作语义]** `ansible-vault create/edit/view/encrypt/decrypt/rekey/encrypt_string` 管密文；`--vault-password-file` 或 `--vault-id` 提供运行时秘密。`no_log: true` 只在必要 task 抑制输出。

<section class="topic knowledge" id="RHCE-VAULT-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 外部数据要有明确 schema

### ① [知识点] 外部数据要有明确 schema
批量用户可定义 name/groups/password_hash 等键；Playbook 用 assert 验证必需键，避免部分对象执行到中途才失败。

### ② [知识点] Vault 密文仍是内容源
编辑用 ansible-vault edit，不先 decrypt 留明文临时文件。`rekey` 更换密码保持数据加密；decrypt 是明确导出明文的高风险操作。

### ③ [验证点] 检查文件头和安全输出
Vault 文件以 `$ANSIBLE_VAULT;` 开头；view 能按授权读取。运行后检查目标终态，不打印秘密值。

**[Cheatsheet]** 外部数据要有明确 schema；Vault 密文仍是内容源；检查文件头和安全输出

</section>

<section class="topic operation" id="RHCE-VAULT-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 加载外部用户列表

### ① [操作点] 加载外部用户列表
`vars_files` 加载 YAML，loop 遍历用户字典；密码字段应是目标模块所需哈希，不把明文直接传给 user.password。

### ② [操作点] 创建和改密 Vault
使用 create/edit；密码轮换用 rekey old/new vault-id。密码文件权限收紧并排除版本控制。

### ③ [验证点] 语法、解密与远端对象
先 vault view 和 playbook syntax-check，再 limit；远端用 getent/id 验证用户，不回显哈希。

**[Cheatsheet]** 加载外部用户列表；创建和改密 Vault；语法、解密与远端对象

</section>

<section class="topic diagnosis" id="RHCE-VAULT-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> no vault secrets found

### ① [诊断点] no vault secrets found
检查当前项目是否收到正确 vault-id/password file，文件是否被错误 decrypt 或 vault ID 不匹配。

### ② [诊断点] 秘密出现在日志
给最小敏感 task 设置 no_log，并审查 debug、失败消息与注册变量；不能靠删终端历史作为修复。

### ③ [诊断点] 数据结构与 loop 不匹配
debug 仅显示非敏感键/类型，使用 assert；修正 schema，不在任务中叠加复杂兼容。

**[Cheatsheet]** no vault secrets found；秘密出现在日志；数据结构与 loop 不匹配

</section>

<section class="topic knowledge" id="RHCE-VAULT-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> Vault ID、文件权限与日志泄露面

### ① [参数点] 多 Vault 使用 label
`--vault-id dev@prompt --vault-id prod@/path/key` 将密文 label 与密码来源绑定。运行错误时先确认密文头中的 vault ID 和命令提供的 label，不按文件名猜密码。

### ② [边界] 密码文件不是 Vault
密码文件通常是解密钥匙本身，必须 `0600`、排除版本控制并按题目路径管理；把它再放进同一 Vault 会形成无法启动的循环依赖。

### ③ [验证点] 失败输出也可能泄密
模块失败的 invocation、register、debug 和 callback 均可能包含参数。对传递秘密的最小 task 使用 `no_log`，同时避免随后 debug 整个注册对象。

**[Cheatsheet]** 多 Vault 核对 label；密码文件 0600 且不入库；敏感 task 与后续 register 输出一起审计。

</section>

<section class="classic-task task-page" id="RHCE-VAULT-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 使用加密变量批量创建账号

下载/提供的用户列表保存在外部 YAML，密码哈希放 Vault；按组变量选择附加组。密码文件路径由题目指定且不得泄露。验收 Vault 保持加密、Playbook 可运行、用户/组正确且输出无秘密。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-VAULT-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 以 schema 和 Vault 边界驱动用户任务

### ① [操作点] 验证用户列表必需键，Vault 保存哈希与敏感值。
### ② [操作点] vars_files 加载，user 模块 loop 创建；敏感 task no_log。
### ③ [验证点] vault view/syntax/limit，远端 getent/id，最终确认源文件仍加密。

**[Cheatsheet]** schema/assert → Vault → 安全加载 → user loop → 远端身份 → 密文与日志审计。

</section>

<section class="topic closing" id="RHCE-VAULT-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 加密不等于不会泄露

Vault 保护静态文件，no_log 控制任务输出，文件权限和版本控制保护密码入口。三层同时成立，外部数据才既可维护又安全。

</section>
