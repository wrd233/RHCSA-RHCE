---
title: "第十三章 RHCSA 综合任务"
chapter_id: RHCSA-COMPREHENSIVE
exam: RHCSA
validation: static-verified
sources: [RHCSA9-Mock, RH124-RHEL9, RH134-RHEL9]
---

# 第十三章　RHCSA 综合任务

综合题不引入新的命令体系，而是要求识别多个对象之间的依赖和交叉影响。本章用一台服务器的完整终态训练读题、风险排序、分层验证和最终清单。

**[概念]** 综合验收把身份、网络、仓库、服务、存储、SELinux、调度和容器视为共享同一主机状态的多个目标，后做的修改可能破坏先完成的题。

**[概念]** 证据矩阵把每项要求映射到当前状态、持久配置和功能验证，避免以一条成功命令覆盖多个评分点。

**[操作语义]** 调查命令先建立共享对象图；最小修改只推进一个目标层；最终检查从题目原文逐项反查证据。

<section class="topic knowledge" id="RHCSA-COMPREHENSIVE-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 把题目编排为依赖图与风险队列

### ① [知识点] 基础依赖先于业务
网络/解析影响仓库、NFS 与 SSH；仓库影响软件；身份影响权限和 rootless 容器；存储与 SELinux 影响服务数据。

### ② [知识点] 高风险写操作必须有证据门
磁盘初始化、网络切换、fstab、启动恢复和权限递归修改先记录基线与恢复路径。

### ③ [验证点] 每题记录当前、持久、功能三列
例如服务为 active/enabled/HTTP，挂载为 findmnt/fstab/data，防火墙为 runtime/permanent/remote request。

**[Cheatsheet]** 先画依赖与共享对象；低风险基础先做；高风险操作设证据门；每题维护当前/持久/功能三列。

</section>

<section class="topic operation" id="RHCSA-COMPREHENSIVE-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 执行中保持局部闭环

### ① [操作点] 完成一层立即验证
仓库刷新后再装包，服务语法通过后再启动，fstab verify/mount 后再继续，SELinux 规则应用后再测业务。

### ② [诊断点] 卡题保存缺失证据
记录最后错误、已证实层、未证实层和共享影响，不用删除/重建清空现场。

### ③ [验证点] 每次共享对象变化后回归相关题
修改 httpd 端口后回查 firewalld/SELinux；改变用户组后用新会话回查目录与容器。

**[Cheatsheet]** 局部闭环 → 保存卡点 → 共享对象变化后回归；不把局部成功扩大。

</section>

<section class="topic operation" id="RHCSA-COMPREHENSIVE-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 完成最终一页检查

### ① [验证点] 身份、网络和软件
`id/getent`、nmcli/ip/getent、dnf/rpm；确认题目值和持久性。

### ② [验证点] 服务、安全和调度
active/enabled/listen/function；firewalld 双态；SELinux Enforcing/规则/标签；cron 实际产物。

### ③ [验证点] 存储和容器
lsblk/pvs/vgs/lvs、findmnt/df/fstab、swapon；Podman image/container/volume/port/user unit/linger。

### ④ [边界] 重启前先跑静态检查
网络 profile、`findmnt --verify`、服务语法和恢复入口都成立后才决定是否重启。

**[Cheatsheet]** 从原题逐项复核；静态配置→当前状态→功能→持久性；共享对象回归；重启不是第一排错。

</section>

<section class="classic-task task-page" id="RHCSA-COMPREHENSIVE-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 把服务器配置为可综合验收的终态

服务器需同时完成项目用户与共享目录、静态网络与仓库、HTTP 服务及非标准内容目录、XFS/LVM/Swap 持久存储、NFS autofs、周期健康检查、rootless 容器和默认 target。题目给定设备与地址必须按现场值使用，已有数据不得删除，SELinux 保持 Enforcing。请自行安排顺序并提供最终证据矩阵。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-COMPREHENSIVE-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 按依赖和风险推进一条推荐路径

### ① [操作点] 先调查网络、设备、身份、现有服务和挂载，建立共享对象表。
### ② [操作点] 完成网络/解析/仓库，再创建身份与目录；随后安装配置服务。
### ③ [操作点] 设备证据充分后完成分区/LVM/文件系统/fstab/Swap；再配置 NFS、SELinux、计划任务和容器。
### ④ [验证点] 每题使用本章三列表；运行服务语法、findmnt verify、Anki 中的各层命令，回查共享端口/路径/用户。重启前确认恢复路径。

**[Cheatsheet]** 依赖图 → 基础连接 → 身份/软件 → 高风险存储 → 安全/调度/容器 → 证据矩阵 → 回归与持久性。

</section>

<section class="topic closing" id="RHCSA-COMPREHENSIVE-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 最终答案是一组互相一致的系统状态

综合能力不是执行更多命令，而是让用户、路径、端口、设备和服务在当前与重启后保持一致。证据矩阵让每个评分点都有对应查询，也让交叉影响在交卷前被发现。

</section>
