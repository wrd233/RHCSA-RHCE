---
title: "第八章 自动化用户、软件包、仓库、服务与计划任务"
chapter_id: RHCE-SYSTEM
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE9-Mock, Ansible-Documentation]
---

# 第八章　自动化用户、软件包、仓库、服务与计划任务

本章把 RHCSA 手工状态映射为专用模块参数。自动化重点是声明最终用户、仓库、包、服务和 cron，而不是远程执行对应命令；变量数据驱动多对象，Handler 只响应配置变化。

**[概念]** user/group/authorized_key 管身份，dnf/package/yum_repository 管软件，service/systemd_service 管当前与启动状态，cron 管周期声明。每个模块的 state 对应目标终态。

**[概念]** 模块幂等依赖稳定输入：随机密码盐、动态时间戳、无 regexp 的追加文本都会制造持续 changed。

**[操作语义]** 使用 FQCN；`password` 传哈希，`groups` 配合 append；`enabled` 与 `state` 分别表达启动和当前服务。

<section class="topic knowledge" id="RHCE-SYSTEM-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 身份模块参数边界

### ① [知识点] 身份模块参数边界
user.groups 默认可替换附加组，`append: true` 才追加；remove 要明确是否删除家目录。authorized_key 的 exclusive 对循环逐项使用可能互相删除。

### ② [知识点] 仓库与包分层
yum_repository 创建 repo 配置，rpm_key 管 key，dnf 安装包。仓库文件存在后仍要 makecache/包事务证据。

### ③ [验证点] 服务双态与 cron 身份
service 的 started/enabled 分别验证；cron 的 user、时间字段和 job 必须与题意一致，远端检查 crontab/产物。

**[Cheatsheet]** 身份模块参数边界；仓库与包分层；服务双态与 cron 身份

</section>

<section class="topic operation" id="RHCE-SYSTEM-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 用外部列表创建用户

### ① [操作点] 用外部列表创建用户
loop 字典调用 group/user/authorized_key；密码哈希从 Vault，no_log 限制敏感 task。

### ② [操作点] 配置仓库、包和服务
先 key/repo，再 dnf；模板 notify Handler，service 保证 started+enabled。

### ③ [验证点] 模块结果与远端对象
第二次执行无 changed；getent/id、dnf repolist/rpm、systemctl、crontab 和实际服务功能。

**[Cheatsheet]** 用外部列表创建用户；配置仓库、包和服务；模块结果与远端对象

</section>

<section class="topic diagnosis" id="RHCE-SYSTEM-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 用户附加组丢失

### ① [诊断点] 用户附加组丢失
检查 groups 是否在未 append 情况下替换全部列表；修正数据为完整目标或 append。

### ② [诊断点] 服务每次重启
检查 Handler 是否被动态模板/无条件 changed task 每次通知。

### ③ [诊断点] cron 存在但不执行
远端查 user、绝对路径、环境、crond 日志和产物；模块 changed=0 只证明条目稳定。

**[Cheatsheet]** 用户附加组丢失；服务每次重启；cron 存在但不执行

</section>

<section class="topic knowledge" id="RHCE-SYSTEM-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 模块参数的替换、追加与删除语义

### ① [参数点] user 模块表达最终账号而非 useradd 命令
`state`、`uid`、`group`、`groups`、`append`、`shell`、`password_expire_max` 等共同描述目标。删除账号时 `remove: true` 会删除家目录，必须由题意明确。

### ② [参数点] dnf state 的范围
`present` 保证安装，`latest` 会随仓库元数据升级并可能持续改变发布结果，`absent` 删除。只有题目要求最新时使用 latest，并阅读依赖事务。

### ③ [验证点] authorized_key 与 sudoers 仍需功能测试
公钥文件存在后从控制节点实际 SSH；sudoers 由 template/copy 部署时用 `visudo -cf %s` validate，再以目标用户执行允许与拒绝命令。

**[Cheatsheet]** user 删除/组语义要显式；dnf latest 只按题意；公钥与 sudoers 最终做真实认证/授权测试。

</section>

<section class="classic-task task-page" id="RHCE-SYSTEM-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 用变量为多组主机配置基础服务

从外部用户数据创建组/用户/公钥，配置指定仓库和包，部署服务并只在配置变化时重启，创建周期任务。验收每组数据差异、秘密安全、服务双态、cron 产物和第二次执行。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-SYSTEM-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 把手工命令映射为专用模块

### ① [操作点] group/user/authorized_key loop；Vault 哈希。
### ② [操作点] rpm_key/yum_repository/dnf/template/Handler/service。
### ③ [操作点] cron 声明；远端 getent/rpm/systemctl/crontab/功能，第二次执行。

**[Cheatsheet]** 数据 → 身份 → 仓库/包 → 配置/Handler/服务 → cron → 远端/幂等。

</section>

<section class="topic closing" id="RHCE-SYSTEM-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 自动化对象要以 state 而非命令表达

专用模块让 Ansible 比较当前和目标；变量提供差异，Handler 绑定真实变化。recap 之外仍需在受管节点证明身份、包、服务和调度功能。

</section>
