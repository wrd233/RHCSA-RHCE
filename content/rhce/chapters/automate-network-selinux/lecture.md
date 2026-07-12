---
title: "第九章 自动化网络、防火墙与 SELinux"
chapter_id: RHCE-NETWORK
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE9-Mock, Ansible-Documentation]
---

# 第九章　自动化网络、防火墙与 SELinux

网络、安全与 SELinux 自动化要求同时表达当前和持久状态，并避免批量断连。模块或 RHEL System Role 描述目标连接；firewalld immediate/permanent、SELinux fcontext/port/boolean 分别对应不同策略对象。

**[概念]** 网络变更可能切断 Ansible 控制通道，应先 limit、保留旧连接和控制台恢复路径。RHEL network System Role 以结构化变量表达连接集合。

**[概念]** firewalld 的 permanent 与 immediate 分别写持久和 runtime；SELinux fcontext 建规则后仍要 restorecon，端口和 Boolean 是独立入口。

**[操作语义]** `ansible.posix.firewalld`、`community.general.sefcontext/seport` 与 `ansible.posix.seboolean`（以安装 collection 文档为准）表达状态；command 只补没有模块的恢复动作。

<section class="topic knowledge" id="RHCE-NETWORK-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 网络 role 输入必须按节点变量化

### ① [知识点] 网络 role 输入必须按节点变量化
每台主机地址/网关/DNS 放 host/group vars，不在 task 中按主机名堆 when。应用连接前验证设备名与现有连接。

### ② [知识点] firewalld 双态
`permanent: true` 写持久；`immediate: true` 同时应用 runtime，前提 firewalld 运行。zone/service/port 必须匹配。

### ③ [知识点] SELinux 三类状态
sefcontext 管路径规则，restorecon 应用当前标签；seport 管协议/端口类型；seboolean 的 persistent 管持久值。

**[Cheatsheet]** 网络 role 输入必须按节点变量化；firewalld 双态；SELinux 三类状态

</section>

<section class="topic operation" id="RHCE-NETWORK-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 小范围应用网络

### ① [操作点] 小范围应用网络
syntax/check（role 支持范围）、limit 单主机，等待连接恢复并重新 gather facts；再扩全组。

### ② [操作点] 部署非标准 Web 安全状态
template 配置端口，firewalld service/port 双态，sefcontext+restorecon，seport，服务 Handler。

### ③ [验证点] 远端终态和外部访问
nmcli/ip、firewall-cmd 双查询、semanage/ls -Z/getsebool、ss 与外部 curl；第二次执行。

**[Cheatsheet]** 小范围应用网络；部署非标准 Web 安全状态；远端终态和外部访问

</section>

<section class="topic diagnosis" id="RHCE-NETWORK-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 网络 task 后 unreachable

### ① [诊断点] 网络 task 后 unreachable
从控制台/旧地址确认 profile 与 route，检查 Ansible 是否等待重连；不要在全组重复错误连接。

### ② [诊断点] firewalld 每次 changed
检查 immediate/permanent、zone 和 module 版本字段，避免 reload command 每次执行。

### ③ [诊断点] 标签规则存在但访问仍拒绝
确认 restorecon 已应用、目标类型/端口/Boolean 与 AVC；规则存在不等于当前标签。

**[Cheatsheet]** 网络 task 后 unreachable；firewalld 每次 changed；标签规则存在但访问仍拒绝

</section>

<section class="topic knowledge" id="RHCE-NETWORK-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 网络批量变更的串行与恢复策略

### ① [边界] serial 降低影响但不修复错误
play 设置 `serial: 1` 可逐台应用网络，配合 `max_fail_percentage` 控制停止条件。第一台失败时立即停止并调查，不能依赖 serial 自动回滚连接。

### ② [验证点] 等待重连要验证新地址
网络 Role 完成后可用 `wait_for_connection`，但成功只证明 Ansible 重新连接；继续运行 `ip route get`、`getent` 和目标协议测试，确认连接不是经错误备用路径恢复。

### ③ [边界] SELinux module 与 restorecon 分工
规则模块只保证 policy mapping，当前对象仍需恢复标签。restorecon command 可先用 `-n` 预览差异，再在规则确定后应用并用 `matchpathcon`/`ls -Z` 对比。

**[Cheatsheet]** 网络用 serial/停止条件降低批量风险；重连后验地址/路由；fcontext 规则与 restorecon 当前标签分开。

</section>

<section class="classic-task task-page" id="RHCE-NETWORK-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 自动部署自定义目录与端口 Web 服务

按主机变量配置网络；部署 httpd 自定义目录和 8080，配置 firewalld 当前/持久、SELinux 文件规则和端口类型。不得 Permissive。先一台再全组，验收连接恢复、安全三层、监听、外部 HTTP 和幂等性。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-NETWORK-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 按风险顺序应用网络与安全

### ① [操作点] network role limit，一台恢复连接并验证路由/DNS。
### ② [操作点] 模板/Handler、firewalld 双态、sefcontext+restorecon、seport。
### ③ [验证点] 远端命令与外部 curl，全组后第二次执行。

**[Cheatsheet]** 网络小范围/重连 → 服务 → 防火墙双态 → SELinux 规则/当前标签/端口 → 外部功能/幂等。

</section>

<section class="topic closing" id="RHCE-NETWORK-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 自动化仍要尊重系统状态分层

模块把目标状态写成参数，但连接风险、runtime/permanent 和规则/当前标签的区别没有消失。先小范围、再远端证据、最后全量和幂等。

</section>
