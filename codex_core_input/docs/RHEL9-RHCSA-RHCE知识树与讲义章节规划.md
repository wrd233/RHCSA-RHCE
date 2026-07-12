# RHEL 9 RHCSA / RHCE 知识树与讲义章节规划

## 1. 总体结构

整套知识树分为三部分：

```text
通用考试方法
├── RHCSA：手工把单台 RHEL 主机配置到目标终态
└── RHCE：用 Ansible 把一组受管节点配置到目标终态
```

RHCSA 负责建立系统机制、手工命令、状态验证和持久化能力。RHCE 不重复复制这些知识，而是训练如何把同一目标状态表达成 Inventory、变量、模块、Playbook、Role 和可重复执行的自动化内容。

推荐最终形成：

```text
通用方法：1 章
RHCSA：12～14 章
RHCE：10～12 章
综合复习：各 1 章
```

章节数量可以在正式编写时根据内容内聚性微调，不应为了固定数量强拆或合并。

---

## 2. 通用考试方法

# 通用章　完成一场红帽实操考试的方法

### 通用能力

- 把题目拆成对象、当前状态、目标状态和限制条件；
- 区分当前生效、持久配置和最终功能；
- 操作前查询当前状态；
- 使用最小、稳定、可验证的修改；
- 每完成一层立即验证；
- 卡题时保留现场，记录缺失证据；
- 最终进行综合验收。

### RHCSA 流程

```text
读题
→ 查询主机、设备、服务和配置
→ 完成手工修改
→ 验证当前状态
→ 验证持久状态
→ 检查不同题目是否相互影响
→ 最终综合检查
```

### RHCE 流程

```text
确认控制节点、Inventory、连接和提权
→ 语法检查
→ 小范围执行
→ 验证受管节点终态
→ 扩展执行
→ 再次执行检查幂等性
→ 综合验收
```

章末分别提供一页以内的 RHCSA 与 RHCE 检查清单，并生成少量流程与失分防范 Anki 卡。

---

# 第一篇　RHCSA

## 第 1 章　命令行、Shell 与本地帮助

### 知识树

```text
Shell 与命令结构
├── 命令、选项、参数
├── 引号、转义、变量与命令替换
├── 文件名展开和通配符
├── 环境变量与 Shell 配置
└── 退出状态与命令连接

输入输出
├── 标准输入、标准输出、标准错误
├── >、>>、2>、2>&1
├── 管道
└── tee

帮助与发现
├── man、info、--help
├── apropos / mandb
├── type、which、whereis
└── dnf provides
```

### 操作专题

- 构造安全、可读的命令行；
- 使用重定向和管道组合查询；
- 从任务目标反查命令和软件包；
- 通过退出状态判断命令是否成功；
- 使用 Bash 历史、补全和快捷键提高操作速度。

### 经典任务

- 在陌生系统中找到完成某个目标所需的命令、配置入口和软件包。

---

## 第 2 章　文件、目录、文本处理与归档传输

### 知识树

```text
文件系统层次
├── 绝对路径与相对路径
├── 关键目录用途
├── 普通文件、目录、设备与链接
└── 硬链接与符号链接

文件操作
├── cp、mv、rm、mkdir、install
├── stat、file、du、df
└── find、locate

文本处理
├── cat、less、head、tail
├── grep 与基础正则
├── cut、sort、uniq、tr、wc
├── sed / awk 的考试常用范围
└── diff

归档与传输
├── tar 与压缩格式
├── scp / sftp
└── rsync
```

### 操作专题

- 按条件查找文件并批量处理；
- 使用 grep、管道和文本工具提取信息；
- 创建与验证归档；
- 在主机之间安全复制或同步文件；
- 正确选择硬链接与符号链接。

### 经典任务

- 从多个目录筛选目标文件，生成压缩归档并传送到指定主机。

---

## 第 3 章　用户、组、权限、ACL 与 sudo

### 知识树

```text
身份对象
├── 用户、UID、主组、附加组
├── /etc/passwd、/etc/shadow、/etc/group
└── 登录 Shell 与家目录

权限模型
├── 所有者、所属组、其他
├── r/w/x 在文件与目录上的语义
├── chmod 数字与符号模式
├── chown / chgrp
├── umask
└── setuid、setgid、sticky bit

扩展权限
├── ACL
├── 默认 ACL
└── getfacl / setfacl

账号策略
├── 密码期限
├── 账号锁定
└── sudoers
```

### 操作专题

- 创建具有指定 UID、组和 Shell 的用户；
- 管理附加组与密码期限；
- 建立 setgid 协作目录；
- 配置 ACL 与默认 ACL；
- 配置最小化 sudo 授权；
- 根据目录 x 权限解释访问失败。

### 经典任务

- 为项目团队创建账号、共享目录、默认权限和受控提权环境。

---

## 第 4 章　进程、作业、服务、日志与计划任务

### 知识树

```text
进程与作业
├── PID、父子关系、状态
├── ps、top、pgrep、pidof
├── 前台、后台、jobs、fg、bg
├── 信号、kill、pkill
└── nice / renice

systemd
├── unit、target、依赖
├── active 与 enabled
├── start、stop、restart、reload
├── enable、disable、mask
└── systemctl status / is-active / is-enabled

日志与时间
├── rsyslog
├── journald / journalctl
├── 日志持久化
└── chrony / timedatectl

计划任务
├── at
├── cron / crontab
└── systemd timer 的辨识
```

### 操作专题

- 定位和终止异常进程；
- 管理服务当前状态与启动配置；
- 通过 journalctl 获取指定服务和时间范围的证据；
- 配置一次性和周期性任务；
- 验证时间同步与时区。

### 经典任务

- 配置一个服务、周期任务和持久日志，并根据日志定位启动失败。

---

## 第 5 章　软件包、仓库与基础系统维护

### 知识树

```text
RPM 与 DNF
├── 包安装、升级、删除
├── rpm 查询与验证
├── dnf search、info、provides
└── 依赖解析

仓库
├── repo 文件
├── baseurl、enabled、gpgcheck
├── 仓库启用与禁用
└── repoquery

系统维护
├── 主机名
├── 时间与时区
├── tuned / 性能配置的基本识别
└── 开机服务与默认 target
```

### 操作专题

- 配置并验证软件仓库；
- 查找命令由哪个包提供；
- 安装、更新和删除指定软件；
- 查询包中的文件和配置；
- 处理不可用仓库和签名问题。

### 经典任务

- 从指定仓库安装服务，确认软件包、配置文件和服务单元均正确。

---

## 第 6 章　网络、名称解析、SSH 与 firewalld

### 知识树

```text
网络对象
├── 接口、连接配置与活动连接
├── IPv4 地址、前缀、网关、DNS
├── 路由与监听端口
└── 主机名与名称解析

NetworkManager
├── nmcli device
├── nmcli connection
├── 当前状态与持久连接
└── 修改后重新激活

SSH
├── 远程登录
├── 密钥认证
├── known_hosts
└── sshd 基本配置

firewalld
├── zone、service、port
├── runtime 与 permanent
├── reload
└── 查询与验证
```

### 操作专题

- 查看并配置静态 IPv4；
- 配置主机名和本地名称解析；
- 建立 SSH 密钥认证；
- 判断服务监听、路由和网络连通；
- 配置 firewalld 服务或端口；
- 同时验证 runtime 和 permanent。

### 经典任务

- 为服务器配置静态网络、SSH 密钥登录、指定服务和防火墙访问。

---

## 第 7 章　分区、文件系统、Swap 与持久挂载

### 知识树

```text
块设备
├── 磁盘、分区、设备名称
├── GPT / MBR 的必要认识
├── lsblk、blkid、findmnt
└── 设备签名与数据风险

文件系统
├── XFS 与 ext4
├── mkfs
├── UUID
├── mount / umount
└── 文件系统容量

持久配置
├── /etc/fstab 六字段
├── mount -a
├── findmnt --verify
└── systemd mount units

Swap
├── 分区或 LV
├── mkswap、swapon、swapoff
└── fstab 持久化
```

### 操作专题

- 创建分区和文件系统；
- 使用 UUID 配置持久挂载；
- 在重启前验证 fstab；
- 创建并持久启用 Swap；
- 解释“目录存在但没有挂载”。

### 经典任务

- 在新磁盘上创建分区、XFS 和 Swap，并配置持久启用。

---

## 第 8 章　LVM 逻辑存储

### 知识树

```text
设备 / 分区
→ PV
→ VG
→ LV
→ 文件系统
→ 挂载点

容量单位
├── PE / LE
├── -l 与 -L
├── 目标总量与 +增量
└── 百分比表达

扩容链
├── VG 余量
├── PV 扩容
├── VG 扩容
├── LV 扩容
└── 文件系统扩容
```

### 操作专题

- 使用 `pvs`、`vgs`、`lvs` 建立对象映射；
- 创建指定 PE 的 VG；
- 按 extent 或容量创建 LV；
- 创建文件系统并持久挂载；
- 使用 `lvextend -r` 保留数据扩容；
- VG 空间不足时增加 PV；
- 根据 `lvs`、`df`、`findmnt` 的差异定位失败层。

### 经典任务

- 建立并扩展一个使用 UUID 持久挂载、要求保留数据的项目卷。

---

## 第 9 章　网络文件系统与自动挂载

### 知识树

```text
NFS
├── 服务端导出概念
├── 客户端发现与挂载
├── 当前挂载
└── fstab 持久挂载

Autofs
├── master map
├── indirect / direct map
├── 按需挂载
└── 超时卸载
```

### 操作专题

- 查询 NFS 导出；
- 当前挂载 NFS；
- 使用 fstab 持久挂载；
- 配置 autofs 按需挂载；
- 验证挂载源、文件系统类型和触发行为。

### 经典任务

- 将远端共享以持久方式或按需方式提供到指定目录。

---

## 第 10 章　SELinux

### 知识树

```text
安全上下文
├── user : role : type : level
├── 进程 domain
└── 文件 type

运行模式
├── Enforcing
├── Permissive
├── Disabled
├── 当前模式
└── 持久模式

策略入口
├── 文件上下文规则
├── 当前标签
├── Boolean
├── 端口类型
└── AVC 审计证据
```

### 操作专题

- 查看当前与持久运行模式；
- 区分 `chcon`、`semanage fcontext` 和 `restorecon`；
- 为自定义目录建立持久上下文；
- 区分只读与可写 Web 内容类型；
- 查询和设置 Boolean；
- 查询、添加和修改端口类型；
- 使用 `ausearch` 获取 AVC 证据；
- 从文件类型、端口类型和 Boolean 中选择最小修复。

### 经典任务

- 在 Enforcing 下部署使用自定义目录和非标准端口的 Web 服务。

---

## 第 11 章　启动过程、Target 与系统恢复

### 知识树

```text
启动过程
├── firmware / boot loader
├── kernel / initramfs
├── systemd
└── target

控制
├── reboot / poweroff
├── isolate / set-default
└── rescue / emergency

恢复
├── 中断启动
├── 重置 root 密码
├── SELinux relabel
├── 修复 fstab
└── 处理服务或文件系统导致的启动失败
```

### 操作专题

- 查看和切换 target；
- 配置默认 target；
- 进入 rescue / emergency；
- 中断启动并重置 root 密码；
- 修复错误 fstab；
- 理解恢复后 SELinux 重新标记要求。

### 经典任务

- 从无法正常启动的系统中恢复 root 访问并修正持久配置。

---

## 第 12 章　Podman 容器与持久运行

### 知识树

```text
镜像与容器
├── registry
├── image
├── container
├── tag
└── inspect

运行配置
├── 端口映射
├── 卷挂载
├── 环境变量
├── rootless
└── SELinux 挂载标签

持久运行
├── 用户服务
├── systemd 集成
└── 开机启动
```

### 操作专题

- 搜索、拉取和查看镜像；
- 创建和管理容器；
- 配置端口、环境变量和持久存储；
- 处理 SELinux 卷标签；
- 生成或配置 systemd 用户服务；
- 验证容器当前运行和重启后运行。

### 经典任务

- 使用指定镜像、端口和持久目录部署 rootless 容器服务。

---

## 第 13 章　RHCSA 综合任务

本章不引入大量新知识，主要重组前面能力：

- 用户、组、权限与共享目录；
- 软件包、服务、网络与防火墙；
- 分区、LVM、文件系统与持久挂载；
- SELinux 自定义目录和端口；
- 计划任务、日志和时间；
- 容器持久运行；
- 启动恢复与最终验收。

经典任务应交叉多个章节，并要求读者自行识别操作层次。

---

# 第二篇　RHCE

## 第 1 章　Ansible 架构、配置与 Inventory

### 知识树

```text
控制节点
├── ansible-core
├── 配置文件
├── 项目目录
└── 执行入口

受管节点
├── SSH
├── Python
└── privilege escalation

Inventory
├── 主机与组
├── 嵌套组
├── 主机范围
├── 静态 Inventory
└── Inventory 变量

配置优先级
├── ansible.cfg
├── 环境变量
└── 命令参数
```

### 操作专题

- 建立项目目录和配置；
- 编写 Inventory；
- 检查主机匹配；
- 测试连接与提权；
- 使用 ad hoc 命令执行查询和简单操作；
- 区分控制节点与受管节点上的文件和命令。

### 经典任务

- 建立一个包含多个主机组、连接参数和提权配置的 Ansible 项目。

---

## 第 2 章　YAML、Playbook、Task 与模块

### 知识树

```text
YAML
├── 缩进
├── 映射
├── 列表
├── 字符串
└── 布尔值

Playbook
├── play
├── hosts
├── gather_facts
├── become
├── tasks
└── module arguments

执行
├── syntax check
├── list-hosts / list-tasks
├── limit
└── verbosity

幂等性
├── 目标状态
├── changed
└── 重复执行
```

### 操作专题

- 编写最小 Playbook；
- 选择 FQCN 模块；
- 区分 command、shell 与专用模块；
- 做语法检查和限制范围执行；
- 读取 recap；
- 验证“执行成功”与“远端终态正确”的区别。

### 经典任务

- 使用 Playbook 在指定主机组安装、配置并启动服务。

---

## 第 3 章　变量、Facts、注册结果与优先级

### 知识树

```text
变量来源
├── play vars
├── vars_files
├── host_vars
├── group_vars
├── Inventory
├── Facts
└── extra vars

Facts
├── ansible_facts
├── 常用系统事实
└── gather_facts

运行时数据
├── register
├── stdout / rc / changed
└── set_fact
```

### 操作专题

- 定义和引用变量；
- 使用 host_vars / group_vars；
- 从 Facts 选择系统差异；
- 注册命令或模块结果；
- 根据返回字段作出判断；
- 理解高频变量优先级，不扩展成纯理论表。

### 经典任务

- 使用组变量和 Facts 为不同主机部署不同配置。

---

## 第 4 章　循环、条件、Handler、Block 与错误控制

### 知识树

```text
循环
├── loop
├── item
└── 字典列表

条件
├── when
├── Facts 条件
├── 注册结果条件
└── 布尔与比较

Handler
├── notify
├── changed
└── flush_handlers

错误控制
├── block / rescue / always
├── failed_when
├── changed_when
└── ignore_errors 的边界
```

### 操作专题

- 使用循环处理多个对象；
- 根据系统事实选择任务；
- 仅在配置变化时触发 Handler；
- 根据返回值定义失败与变更；
- 使用 Block 组织相关任务和恢复逻辑。

### 经典任务

- 批量部署多个服务或用户，并根据主机差异选择配置和 Handler。

---

## 第 5 章　文件、模板与 Jinja2

### 知识树

```text
文件模块
├── file
├── copy
├── fetch
├── lineinfile
├── blockinfile
└── synchronize 的必要认识

模板
├── template
├── Jinja2 变量
├── 表达式
├── 条件
├── 循环
└── 过滤器
```

### 操作专题

- 根据目标选择 copy、template、lineinfile 或 blockinfile；
- 使用模板生成服务配置；
- 使用变量、Facts、循环和条件渲染内容；
- 配置验证后通知 Handler；
- 验证文件所有者、权限、内容和服务结果。

### 经典任务

- 为不同主机生成差异化配置文件，并在内容变化时安全重启服务。

---

## 第 6 章　外部数据、敏感变量与 Vault

### 知识树

```text
数据组织
├── vars_files
├── host_vars / group_vars
├── YAML 字典和列表
└── 变量文件拆分

Vault
├── 加密文件
├── 加密字符串
├── 查看与编辑
├── 密码来源
└── 运行时解密
```

### 操作专题

- 将复杂数据移出 Playbook；
- 使用外部 YAML 驱动批量任务；
- 加密敏感变量；
- 编辑和重新加密 Vault 内容；
- 在不泄露秘密的情况下运行 Playbook。

### 经典任务

- 使用加密变量和外部用户数据完成批量账号配置。

---

## 第 7 章　Include、Import、Role 与 Collection

### 知识树

```text
内容拆分
├── include_tasks
├── import_tasks
├── import_playbook
└── 动态与静态的必要区别

Role
├── tasks
├── handlers
├── templates
├── files
├── defaults
├── vars
└── meta

Collection
├── FQCN
├── 模块
├── Role
└── requirements

System Roles
└── 使用官方系统角色表达系统状态
```

### 操作专题

- 拆分复杂 Playbook；
- 创建和调用 Role；
- 理解 defaults 与 vars 的使用边界；
- 安装并引用 Collection；
- 使用 requirements 文件；
- 使用 RHEL System Roles 完成标准管理任务。

### 经典任务

- 将一个单文件 Playbook 重构为可复用 Role，并通过 requirements 部署依赖内容。

---

## 第 8 章　自动化用户、软件包、仓库、服务与计划任务

### 知识树

```text
身份
├── user
├── group
└── authorized_key

软件
├── package / dnf
├── yum_repository
└── rpm_key

服务
├── service / systemd_service
├── enabled
├── state
└── Handler

计划任务
├── cron
└── at 的自动化边界
```

### 操作专题

- 批量创建用户和组；
- 配置 SSH 公钥；
- 配置仓库和软件包；
- 管理服务当前与启动状态；
- 配置计划任务；
- 验证受管节点真实终态。

### 经典任务

- 使用变量数据为多组主机配置用户、仓库、软件和服务。

---

## 第 9 章　自动化网络、防火墙与 SELinux

### 知识树

```text
网络
├── nmcli / network system role
├── 地址、网关、DNS
└── 连接激活

防火墙
├── firewalld 模块
├── service / port
├── permanent / immediate
└── zone

SELinux
├── 模式
├── Boolean
├── 文件上下文
├── 端口类型
└── restorecon
```

### 操作专题

- 用模块或系统角色表达网络终态；
- 配置防火墙当前与持久状态；
- 管理 SELinux Boolean；
- 建立持久文件上下文并应用；
- 配置非标准端口类型；
- 将手工系统状态映射为幂等任务。

### 经典任务

- 自动部署使用自定义目录和端口的 Web 服务，并完成网络、防火墙和 SELinux 配置。

---

## 第 10 章　自动化存储、文件系统与挂载

### 知识树

```text
块设备事实
├── 设备识别
└── 环境差异

LVM
├── lvg
├── lvol
└── 容量目标

文件系统
├── filesystem
├── mount
└── 持久状态

存储系统角色
└── 标准化存储配置
```

### 操作专题

- 使用 LVM 模块创建 VG 和 LV；
- 创建文件系统；
- 配置当前和持久挂载；
- 扩展卷和文件系统；
- 使用变量描述存储布局；
- 在多节点上验证不同设备条件。

### 经典任务

- 使用变量或系统角色为指定主机组创建并挂载逻辑卷。

---

## 第 11 章　Ansible 故障排除、验证与幂等性

### 知识树

```text
控制端
├── YAML 语法
├── 模块参数
├── 变量未定义
├── Inventory 匹配
└── 路径与文件

连接
├── SSH
├── Python
├── become
└── 权限

执行
├── failed
├── unreachable
├── changed
├── skipped
└── recap

远端终态
├── 服务
├── 文件
├── 端口
├── 挂载
└── 数据
```

### 操作专题

- 根据错误类型定位控制端、连接层或远端任务；
- 使用 verbosity 获取必要证据；
- 解释 registered result；
- 修正不必要 changed；
- 执行第二次 Playbook 检查幂等性；
- 不把 recap 成功当作最终验收。

### 经典任务

- 修复一个存在 Inventory、变量、模板、Handler 和幂等性问题的自动化项目。

---

## 第 12 章　RHCE 综合任务

综合任务围绕完整系统终态，不按模块列表出题：

- 项目配置与 Inventory；
- group_vars / host_vars；
- Vault；
- 用户、仓库、包和服务；
- 模板与 Handler；
- 网络、防火墙和 SELinux；
- 存储和挂载；
- Role、Collection 或系统角色；
- 故障处理；
- 第二次执行与远端验收。

---

## 3. RHCSA 到 RHCE 的桥接关系

| RHCSA 系统能力 | RHCE 自动化表达 |
|---|---|
| `useradd`、组和权限 | `user`、`group`、`file`、`acl` 模块 |
| `dnf` 与 repo 文件 | `dnf/package`、`yum_repository` |
| `systemctl` | `service/systemd_service`、Handler |
| `firewall-cmd` | `firewalld` 模块 |
| `semanage`、`restorecon` | SELinux 相关模块、command 只作必要补充 |
| `nmcli` | 网络模块或 RHEL Network System Role |
| `pvcreate/vgcreate/lvcreate` | `lvg`、`lvol` 或 Storage System Role |
| `mkfs`、`fstab`、`mount` | `filesystem`、`mount` |
| Shell 配置文件 | `copy`、`template`、`lineinfile`、`blockinfile` |
| 当前状态与持久状态验证 | 远端终态验证与第二次执行 |
| 手工排错 | 控制端、连接层、模块执行、远端状态分层排错 |

同一系统机制只在 RHCSA 完整解释一次。RHCE 章节做最小回顾，然后重点讲自动化表达、变量化、幂等性、批量执行和远端验证。

---

## 4. 推荐编写顺序

为了尽快建立可用材料，建议按照依赖和考试价值编写：

### RHCSA 第一阶段

```text
考试方法
→ 命令行与帮助
→ 用户权限
→ 服务与日志
→ 网络与防火墙
→ 文件系统
→ LVM
→ SELinux
```

### RHCSA 第二阶段

```text
软件包与仓库
→ 计划任务
→ 网络文件系统
→ 启动恢复
→ 容器
→ 综合任务
```

### RHCE

```text
架构与 Inventory
→ Playbook 与模块
→ 变量与 Facts
→ 条件、循环与 Handler
→ 模板
→ Vault
→ Role 与 Collection
→ 自动化 RHCSA 任务
→ 故障排除
→ 综合任务
```

LVM 高密度操作版与 SELinux 样章用于固定讲义和 Anki 风格。后续章节不需要机械复制篇幅，但必须复制其高内聚专题、命令参数说明、点式组织、代码注释和专题末 Cheatsheet 方法。
