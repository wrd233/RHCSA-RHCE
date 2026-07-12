---
title: "第 21 章 firewalld 与完整服务访问链"
chapter_id: RHCSA-21
exam: RHCSA
part: "第五篇 网络与远程管理"
slug: firewalld-service-access-chain
status: integrated
validation: static
live_test: not_performed
base_commit: 39e873dab15347a0f1a7611a6f212c3d26bd3562
sources:
  - RH134-RHEL9
  - firewalld(1)
  - firewall-cmd(1)
  - Red Hat Enterprise Linux 9 documentation
---

<!-- 维护元数据、来源映射与稳定 ID 仅用于候选包集成，正式渲染不显示。 -->

# 第 21 章　firewalld 与完整服务访问链

一项网络服务可以“看起来已经完成”，却仍然无法从远端使用。服务可能显示 `active`，但只监听在回环地址；端口可能已经加入 firewalld，却加在不处理实际流量的 zone；持久配置可能正确，而当前 runtime 尚未加载；本机 `curl` 可能成功，但请求根本没有经过远端客户端使用的接口和防火墙路径；非标准端口还可能受到 SELinux 端口类型约束。

因此，本章不把 firewalld 理解为一组孤立的“开端口命令”，而是把它放回完整服务访问链：

```text
服务配置
→ 服务进程
→ SELinux 端口绑定许可
→ socket 真实监听
→ 本机协议响应
→ 流量进入正确 zone
→ runtime 规则允许
→ permanent 规则可持续
→ 远端客户端完成协议访问
```

**[概念]** `firewalld` 是动态防火墙管理服务。它通过 zone、service、port 和 rich rule 等高层对象管理主机的包过滤配置；它不启动应用服务，也不会因为“开放端口”而自动产生监听进程。

**[概念]** zone 是一组信任边界和允许规则。接口（interface）或来源（source）把进入主机的流量分类到 zone；未显式选择 zone 的连接和接口使用 default zone。

**[概念]** firewalld 同时维护 runtime 和 permanent 两套配置。runtime 是当前实际使用的规则；permanent 是 reload、服务重启或系统重启后加载的持久配置。两者可以不同，必须分别验证。

**[操作语义]** `firewall-cmd` 是本章主要查询和修改接口；`systemctl` 证明服务管理状态；`ss` 证明真实监听；`curl` 或实际协议客户端证明应用功能；`nc` 只适合做有限的传输层探测。

**[边界]** SELinux 端口类型属于第 29 章《SELinux 文件规则、端口类型与 Boolean》。本章只在完整访问链中识别它是独立层，不完整展开 `semanage port` 和 AVC 分析。

---

<!-- topic: RHCSA-21-S01 -->
## [知识专题] 1. firewalld 管什么，又不能证明什么

排错最常见的问题不是“不会加规则”，而是把一个局部证据扩大成整体结论。首先要明确每个工具所观察的对象，以及它能证明和不能证明的范围。

### ① firewalld 管理网络过滤状态，不管理应用生命周期

`firewalld` 可以允许某个 zone 中的 `http` service 或 `8088/tcp` 端口，但它不会：

- 安装或启动 `httpd`；
- 修改应用监听端口；
- 让仅监听 `127.0.0.1` 的服务自动监听外部地址；
- 为非标准端口建立 SELinux 端口类型；
- 修复上游路由、中间防火墙或客户端 DNS。

因此，下面两个事实必须分开：

```text
firewall-cmd --zone=public --query-port=8088/tcp
```

回答“该 zone 的当前规则是否允许 `8088/tcp`”，而：

```text
ss -lntp
```

回答“主机当前是否存在 TCP 监听，以及监听在哪个地址和端口”。

### ② `active`、监听、协议响应和远端可达是不同终态

| 证据 | 能证明 | 不能证明 |
|---|---|---|
| `systemctl is-active httpd` | systemd 认为服务当前 active | 端口、地址、协议和远端可达正确 |
| `ss -lntp` | TCP listener 的地址、端口及相关进程 | HTTP 内容或远端路径正常 |
| `curl http://127.0.0.1:8088/` | 回环路径上的 HTTP 响应 | 外部地址监听和防火墙允许 |
| `firewall-cmd --query-port` | 指定 zone 的规则状态 | 流量确实进入该 zone，或应用正在监听 |
| 远端 `curl` | 从该客户端到目标服务的协议路径可用 | 所有其他来源、协议和重启后状态都正确 |

最终验收必须由多层证据交集完成，而不是寻找一个“万能成功命令”。

### ③ 入站访问链的最小对象模型

```text
远端客户端
  │
  ├─ 名称解析与路由（第 18、19 章边界）
  │
  ▼
服务器接口 / 来源分类
  │
  ▼
zone
  ├─ service
  ├─ port/protocol
  └─ rich rule
  │
  ▼
本地 socket listener
  │
  ▼
应用协议响应
```

当服务使用非标准端口时，还要在 listener 之前增加一条独立判断：服务进程是否被 SELinux 允许绑定该端口。

**[Cheatsheet]** 防火墙允许不等于有监听；服务 active 不等于端口正确；本机成功不等于远端成功；远端成功也不能自动证明 permanent 正确。

---

<!-- topic: RHCSA-21-S02 -->
## [知识专题] 2. zone、default zone 与 active zone

zone 的本质是把不同信任边界的流量映射到不同规则集合。考试和工作中最危险的误判，是在没有确认实际 zone 的情况下，直接对默认 zone 加规则。

### ① zone 是规则容器，也是流量分类结果

一个 zone 可以包含：

- 绑定的 interfaces；
- 绑定的 sources；
- 允许的 services；
- 允许的 ports 和 protocols；
- rich rules；
- ICMP、转发、伪装等其他属性。

本章只完整展开与主机入站服务访问直接相关的 interface/source、service、port/protocol 和 rich rule。NAT、端口转发、policy object 和 direct rule 不进入 RHCSA 主路径。

### ② default zone 是“未显式选择时的回落对象”

```bash
firewall-cmd --get-default-zone
```

显示未单独选择 zone 的连接和接口所使用的默认 zone。设置默认 zone：

```bash
firewall-cmd --set-default-zone=public
```

这是 runtime 和 permanent 同时改变的全局操作。它可能影响所有仍在使用默认 zone 的连接或接口，因此不能把它当作只影响单条规则的轻量修改。

### ③ active zone 只表示当前存在绑定

```bash
firewall-cmd --get-active-zones
```

列出当前绑定了 interface 或 source 的 zones。它不表示：

- zone 中一定有允许规则；
- 该 zone 是 default zone；
- 系统只存在这些 zones；
- 某个服务端口一定开放。

需要查看所有可用 zone 时使用：

```bash
firewall-cmd --get-zones
```

需要查看某个 zone 的详细当前状态时使用：

```bash
firewall-cmd --zone=public --list-all
```

### ④ interface 与 source 是两种分类输入

接口绑定表达“从这个接口进入的流量使用哪个 zone”：

```bash
firewall-cmd --get-zone-of-interface=enp1s0
```

来源绑定表达“来自这个 IP、网段、MAC 或 ipset 的流量使用哪个 zone”：

```bash
firewall-cmd --get-zone-of-source=192.0.2.0/24
```

来源参数不支持主机名。需要基于名称管理来源时，必须先把需求改写为稳定的地址或地址集合；名称解析策略属于第 19 章。

### ⑤ 不依赖模糊的优先级记忆，直接读取实际分类

传统教学常把 source、interface、default 描述成一条简单顺序。现代 firewalld 还存在 zone priority 等版本相关能力。RHCSA 操作中最稳妥的做法不是背诵所有内部匹配细节，而是：

```text
查询来源绑定
→ 查询接口绑定
→ 查询 active zones
→ 明确将修改写入哪个 zone
```

**[Cheatsheet]** `--get-default-zone` 看回落；`--get-active-zones` 看当前绑定；`--get-zone-of-interface/source` 看具体对象；`--list-all` 看某个 zone 的规则。

---

<!-- topic: RHCSA-21-S03 -->
## [操作专题] 3. 查询与维护 interface/source 绑定

绑定操作改变的是“哪些流量使用哪一组规则”。它比单纯增加端口更可能影响现有远程会话，因此必须先建立基线。

### ① 建立绑定基线

```bash
firewall-cmd --state
firewall-cmd --get-default-zone
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --permanent --get-zone-of-interface=enp1s0
```

对来源绑定也要分别查看当前和持久状态：

```bash
firewall-cmd --get-zone-of-source=192.0.2.0/24
firewall-cmd --permanent --get-zone-of-source=192.0.2.0/24
```

### ② 添加、移动、查询和移除 interface

```bash
# 当前生效
firewall-cmd --zone=public --add-interface=enp1s0

# 改到另一个 zone
firewall-cmd --zone=internal --change-interface=enp1s0

# 查询
firewall-cmd --zone=internal --query-interface=enp1s0

# 移除当前绑定
firewall-cmd --remove-interface=enp1s0
```

`--change-interface` 在尚未绑定时相当于添加；已经绑定时相当于先移除再添加。接口由 NetworkManager 管理时，firewalld 会尝试修改使用该接口的连接配置。完整的 NetworkManager connection profile 与 zone 管理归第 18 章。

### ③ 添加、移动、查询和移除 source

```bash
firewall-cmd --zone=internal --add-source=192.0.2.0/24
firewall-cmd --zone=dmz --change-source=192.0.2.0/24
firewall-cmd --zone=dmz --query-source=192.0.2.0/24
firewall-cmd --remove-source=192.0.2.0/24
```

source 可以是单个地址、CIDR 网段、MAC 地址，或带 `ipset:` 前缀的地址集合。考试主路径通常使用 IP/CIDR。

### ④ binding 也有 runtime/permanent 双状态

需要当前和 reload 后都保持时，可分别执行：

```bash
firewall-cmd --zone=internal --add-source=192.0.2.0/24
firewall-cmd --permanent --zone=internal --add-source=192.0.2.0/24
```

或者先完成并验证 runtime，再明确使用：

```bash
firewall-cmd --runtime-to-permanent
```

但后者会用整个 runtime 覆盖 permanent，不是“只保存刚才这一条”。执行前必须审查 runtime 中是否混有临时测试规则。

### ⑤ 远程操作的安全顺序

当当前 SSH 会话也经过待修改接口时，推荐顺序：

```text
确认当前 SSH 来源和接口
→ 确认目标 zone 已允许 SSH 或所需管理端口
→ 记录回滚命令
→ 先做 runtime 修改
→ 开启第二个会话验证
→ 再写入 permanent
```

禁止把接口直接改到 `trusted` 来规避调查。`trusted` 会接受几乎所有流量，不能作为默认排错答案。

**[Cheatsheet]** 绑定改变的是流量分类；先确认管理通道，再移动接口或来源；`runtime-to-permanent` 保存整个当前配置，不是单条规则提交。

---

<!-- topic: RHCSA-21-S04 -->
## [知识专题] 4. runtime、permanent 与 reload

firewalld 的两套配置使管理员可以先做临时测试，再决定是否持久化。但这也产生两类典型故障：当前有效但重载后丢失，以及持久配置存在但当前尚未应用。

### ① runtime 是当前实际规则

不带 `--permanent` 的修改只改变 runtime：

```bash
firewall-cmd --zone=public --add-port=8088/tcp
```

它立即影响当前规则，但 reload、firewalld 重启或系统重启后不保留。

### ② permanent 是下一次加载的配置

```bash
firewall-cmd --permanent --zone=public --add-port=8088/tcp
```

只写入持久配置，不立即改变当前 runtime。执行成功只能证明持久配置被接受，不能证明远端现在已经可访问。

### ③ 同时满足“现在”和“以后”的两种路径

**路径 A：同一修改执行两次。**

```bash
firewall-cmd --zone=public --add-port=8088/tcp
firewall-cmd --permanent --zone=public --add-port=8088/tcp
```

适合单条明确变更，避免 reload 清除其他 runtime-only 状态。

**路径 B：维护 permanent 后 reload。**

```bash
firewall-cmd --permanent --zone=public --add-port=8088/tcp
firewall-cmd --check-config
firewall-cmd --reload
```

适合有计划地统一应用持久配置。执行 reload 前必须确认是否存在仍需保留的 runtime-only 规则。

### ④ reload 的准确语义

```bash
firewall-cmd --reload
```

让当前 permanent 成为新的 runtime，并尽量保留连接状态。未写入 permanent 的 runtime-only 修改会消失。

`--complete-reload` 可能丢失连接跟踪状态，通常只用于严重防火墙状态问题，不是普通配置刷新命令。

### ⑤ runtime-to-permanent 是整体覆盖

```bash
firewall-cmd --runtime-to-permanent
```

用于把已经测试满意的完整 runtime 保存为 permanent。它适合“先临时配置和验证，再整体提交”的工作流，但执行前必须列出并审查所有 runtime 规则。

### ⑥ 双态验证是操作闭环

```bash
firewall-cmd --zone=public --query-port=8088/tcp
firewall-cmd --permanent --zone=public --query-port=8088/tcp
```

输出 `yes` 时退出码为 0；输出 `no` 时退出码为 1。脚本中应判断退出码，而不是解析颜色或完整句子。

| runtime | permanent | 判断 |
|---|---|---|
| yes | yes | 当前和 reload 后都配置 |
| yes | no | 当前可用，但 reload 后丢失 |
| no | yes | 持久配置存在，但当前未应用或之后被改动 |
| no | no | 该 zone 两层都未配置 |

**[Cheatsheet]** runtime 回答“现在”；permanent 回答“下次加载”；reload 用 permanent 重建 runtime；每项变更至少查询两次。

---

<!-- topic: RHCSA-21-S05 -->
## [操作专题] 5. service、port 与 protocol

firewalld 提供两种常用入站放行对象：有语义的 service，以及直接的 port/protocol。选择对象时应从应用真实使用的协议和端口出发。

### ① service 是预定义的通信需求集合

查看系统已知 service：

```bash
firewall-cmd --get-services
```

查看某个 service 的内容：

```bash
firewall-cmd --info-service=http
firewall-cmd --path-service=http
```

service 可以包含一个或多个端口和协议，还可能包含 helper、模块或目标地址信息。不要仅凭 service 名猜测它包含的端口。

### ② 标准服务优先使用 service

```bash
firewall-cmd --zone=public --add-service=http
firewall-cmd --permanent --zone=public --add-service=http
```

查询和列出：

```bash
firewall-cmd --zone=public --query-service=http
firewall-cmd --permanent --zone=public --query-service=http
firewall-cmd --zone=public --list-services
```

移除：

```bash
firewall-cmd --zone=public --remove-service=http
firewall-cmd --permanent --zone=public --remove-service=http
```

### ③ 非标准端口或无合适 service 时使用 port/protocol

```bash
firewall-cmd --zone=public --add-port=8088/tcp
firewall-cmd --permanent --zone=public --add-port=8088/tcp
```

端口对象必须包含协议。`8088/tcp` 与 `8088/udp` 是两个不同规则。

端口范围：

```bash
firewall-cmd --zone=public --add-port=8000-8010/tcp
```

除非应用确实需要整个范围，否则不要为了省事扩大暴露面。

### ④ `--add-protocol` 不是开放某个应用端口

```bash
firewall-cmd --zone=public --add-protocol=icmp
```

允许的是 IP 层协议，而不是 TCP/UDP 端口。普通 Web、SSH、数据库服务通常应使用 service 或 port，而不是把 `tcp` 当作 protocol 整体放行。

### ⑤ timeout 规则只属于 runtime

```bash
firewall-cmd --zone=public --add-port=8088/tcp --timeout=20m
```

该规则到期后自动移除，适合短时测试或临时维护。`--timeout` 不能与 `--permanent` 组合。它是工作迁移扩展，不应替代考试要求的持久终态。

### ⑥ service 与应用真实监听必须一致

如果应用已改到非标准端口 `8088/tcp`，仅添加 `http` service 通常仍只放行 service 定义中的标准端口。正确调查顺序是：

```text
ss 确认真实 listener
→ 查看 service 定义
→ 决定使用 service、port 或自定义 service
```

**[Cheatsheet]** 标准语义用 service；非标准端口用 `port/protocol`；TCP/UDP 分开；开放规则必须和真实 listener 对齐。

---

<!-- topic: RHCSA-21-S06 -->
## [知识专题] 6. 配置文件、覆盖关系与 `--check-config`

多数考试任务使用 `firewall-cmd` 即可完成，但理解配置来源能够解释“为什么同名 service 被覆盖”以及“为什么直接改系统文件会被更新覆盖”。

### ① vendor 与管理员目录职责分离

典型目录：

```text
/usr/lib/firewalld/zones/       发行版或软件包提供的 zone
/usr/lib/firewalld/services/    发行版或软件包提供的 service
/etc/firewalld/zones/           管理员持久 zone 配置
/etc/firewalld/services/        管理员自定义或覆盖的 service
```

不要直接修改 `/usr/lib/firewalld/` 中的 vendor 文件。需要自定义时，在 `/etc/firewalld/` 创建同名覆盖或新对象。

### ② 使用命令查询真实来源路径

```bash
firewall-cmd --path-zone=public
firewall-cmd --path-service=http
```

与“猜某个 XML 一定在哪个目录”相比，查询命令更能反映当前系统的覆盖结果。

### ③ 自定义 service 的必要结构

当多个主机需要重复使用同一组非标准端口时，自定义 service 比每次散列添加端口更易读。最小示例：

```xml
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>training-web</short>
  <description>Training web service on TCP 8088</description>
  <port protocol="tcp" port="8088"/>
</service>
```

保存为：

```text
/etc/firewalld/services/training-web.xml
```

之后检查并加载：

```bash
firewall-cmd --check-config
firewall-cmd --reload
firewall-cmd --info-service=training-web
```

### ④ `--check-config` 只检查 permanent

```bash
firewall-cmd --check-config
```

检查持久 XML 的格式和语义。它不能证明：

- runtime 已应用；
- 端口正在监听；
- service 名对应应用真实端口；
- 远端客户端可以访问；
- SELinux 允许应用绑定非标准端口。

### ⑤ 手工编辑后的加载边界

手工修改 `/etc/firewalld/` 后，需要 reload 才会进入 runtime。更稳妥的流程是：

```text
备份或记录原配置
→ 编辑最小对象
→ check-config
→ 比对当前 runtime-only 规则
→ reload
→ 双态与功能验证
```

**[Cheatsheet]** `/usr/lib` 是 vendor；`/etc` 是管理员；`--path-*` 查真实来源；`--check-config` 只证明持久配置可解析。

---

<!-- topic: RHCSA-21-S07 -->
## [操作专题] 7. rich rule 的必要范围

简单 service 或 port 能表达需求时，应优先使用简单规则。rich rule 用于把“来源、服务/端口和动作”组合为一条更精确的规则。

### ① 最小语法骨架

```text
rule family="ipv4|ipv6"
     source address="地址或网段"
     service name="服务" | port port="端口" protocol="协议"
     accept | reject | drop
```

示例：只允许文档示例网段访问 TCP 8088：

```bash
firewall-cmd --zone=public \
  --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" port port="8088" protocol="tcp" accept'
```

持久配置使用同一规则加 `--permanent`。

### ② 地址与 family 必须一致

当 rich rule 使用 source/destination 地址时，应显式指定 `family="ipv4"` 或 `family="ipv6"`。IPv4 地址不能放入 IPv6 family，反之亦然。

### ③ service 与 port 二选一表达目标

基于标准服务：

```bash
firewall-cmd --zone=public \
  --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" service name="ssh" accept'
```

基于非标准端口：

```bash
firewall-cmd --zone=public \
  --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" port port="8088" protocol="tcp" accept'
```

### ④ accept、reject 与 drop 的区别

- `accept`：允许匹配流量；
- `reject`：拒绝并返回相应错误；
- `drop`：静默丢弃，客户端常表现为超时。

不能仅根据客户端“超时”断言是 drop；路由、中间设备和服务端其他过滤层也可能产生相似症状。

### ⑤ 查询与删除要复用完整规则字符串

```bash
RULE='rule family="ipv4" source address="192.0.2.0/24" port port="8088" protocol="tcp" accept'

firewall-cmd --zone=public --query-rich-rule="$RULE"
firewall-cmd --zone=public --remove-rich-rule="$RULE"
```

先使用：

```bash
firewall-cmd --zone=public --list-rich-rules
```

读取系统当前规则，再复制进行查询或删除，避免引号、属性顺序或遗漏导致匹配失败。

### ⑥ 日志和限速只覆盖必要范围

rich rule 可结合 `log` 和 `limit`，但本章只用于说明“受控地收集拒绝证据”，不展开复杂审计策略。不要在高流量生产入口无上限记录每个包。

### ⑦ rich rule 不是更“高级”的默认选择

如果目标只是“public zone 允许 8088/tcp”，简单端口规则更清晰：

```bash
firewall-cmd --zone=public --add-port=8088/tcp
```

只有需要来源限制或特定动作时，才升级到 rich rule。

**[Cheatsheet]** 简单需求用 service/port；来源限制用 rich rule；地址要配 family；查询和删除复用完整规则。

---

<!-- topic: RHCSA-21-S08 -->
## [操作专题] 8. 从监听到远端请求的分层验收

正确验收不是在服务器上连续运行几条命令，而是让每条证据回答不同问题，并最终从独立客户端进行协议访问。

### ① 第 0 层：明确目标终态

把模糊要求“开放 Web 服务”改写为：

```text
httpd 当前运行；
在服务器目标地址监听 TCP 8088；
本机请求返回 HTTP 响应；
实际入站 zone 的 runtime 和 permanent 均允许 8088/tcp；
指定远端客户端可取得 HTTP 响应。
```

### ② 第 1 层：服务管理状态

```bash
systemctl is-active httpd
systemctl status httpd --no-pager
```

如果服务未运行，先处理服务配置和日志，不要用开放防火墙掩盖服务失败。

### ③ 第 2 层：真实监听

```bash
ss -lntp
ss -lntp | grep ':8088'
```

关注四个维度：

- `tcp` 还是 `udp`；
- 端口是否正确；
- `127.0.0.1`、单个服务器地址还是 `0.0.0.0`/`[::]`；
- 相关进程是否为目标服务。

只监听 `127.0.0.1:8088` 时，远端访问不会因为 firewalld 放行而成功。

### ④ 第 3 层：本机协议验证

```bash
curl -I http://127.0.0.1:8088/
curl -I http://<SERVER_IP>:8088/
```

回环地址成功而服务器地址失败，优先检查监听地址、应用虚拟主机和本地路由，不要先扩大防火墙规则。

### ⑤ 第 4 层：实际 zone 与双态规则

```bash
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --zone=public --query-port=8088/tcp
firewall-cmd --permanent --zone=public --query-port=8088/tcp
```

把示例 `public` 替换为查询得到的实际 zone。不能只检查 default zone。

### ⑥ 第 5 层：远端协议验证

从题目指定的独立客户端执行：

```bash
curl -I http://<SERVER_IP>:8088/
```

或者执行应用自身的客户端命令。`nc -vz <SERVER_IP> 8088` 只能证明 TCP 建连，不能证明 HTTP 内容、TLS 证书或应用认证正确。

### ⑦ 非标准端口的 SELinux 分支

如果服务启动失败或日志显示无法绑定非标准端口，应检查 SELinux 端口类型。此时：

```text
firewalld 允许端口
```

和：

```text
SELinux 允许该域绑定端口
```

是两套独立状态。具体 `semanage port` 操作归第 29 章。

### ⑧ 验收矩阵

| 层 | 推荐证据 | 成功仍不能证明 |
|---|---|---|
| 服务 | `systemctl is-active` | 监听与协议正确 |
| socket | `ss -lntp` | 应用响应与远端可达 |
| 本机协议 | `curl 127.0.0.1`、服务器地址 | 远端 zone 和中间路径 |
| runtime | `query-service/port` | reload 后保留 |
| permanent | `--permanent --query-*` | 当前已应用 |
| 远端协议 | 客户端 `curl` | 其他客户端和重启后仍正确 |

**[Cheatsheet]** 服务、listener、本机协议、实际 zone、runtime、permanent、远端协议必须逐层验收。

---

<!-- topic: RHCSA-21-S09 -->
## [诊断专题] 9. 多层访问故障：从症状推进到下一条证据

诊断不能从症状直接跳到结论。每一步都应选择最能区分假设的证据。

### ① `Connection refused`

**症状：** 远端 TCP 连接立即被拒绝。

**首选证据：**

```bash
ss -lntp
```

**主要假设：** 目标地址/端口没有 listener，或有显式 reject。先确认 listener，再检查 zone 动作和 rich rule。不要仅凭 refused 断言服务一定停止。

### ② 连接超时

**症状：** 客户端长时间等待后超时。

**首选证据链：**

```text
服务器是否监听
→ 本机地址请求是否成功
→ 实际 zone 是什么
→ runtime 是否允许
→ 来源是否命中另一 zone/rich rule
→ 路由和中间设备
```

超时常见于 drop 或路径中断，但不是 firewalld 的唯一特征。

### ③ 服务 active，但 `ss` 没有目标 listener

```text
active 只是 systemd 状态
→ 查看服务配置和启动日志
→ 核对端口和监听地址
→ 非标准端口时检查 SELinux
```

此时增加 firewalld 规则没有区分度。

### ④ 本机回环成功，服务器地址失败

优先检查：

- 服务是否只监听回环；
- 是否只监听 IPv6 或单一地址；
- 应用是否限制 Host 头或虚拟主机；
- 服务器地址是否正确存在。

### ⑤ 本机服务器地址成功，远端失败

这是进入防火墙和路径调查的强信号：

```bash
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --zone=<ACTUAL_ZONE> --list-all
```

之后分别查询 runtime/permanent，而不是直接重复 `--add-port`。

### ⑥ permanent 为 yes，runtime 为 no

**可能原因：**

- 尚未 reload；
- reload 后又删除了 runtime；
- 查询的 zone 不一致；
- 管理工具只写入 permanent。

**最小修复：** 若只需单条规则立即生效，可添加对应 runtime；若要统一应用完整 permanent，先审查 runtime-only 变化再 reload。

### ⑦ runtime 为 yes，permanent 为 no

当前访问可能成功，但 reload 后丢失。若终态要求持久化，补充 permanent 并再次双态查询。不要把当前远端成功扩大为持久终态完成。

### ⑧ 规则存在于错误 zone

典型误判：

```text
public 中 query-port=yes
```

但实际接口属于 `internal`。下一条证据应是 `--get-zone-of-interface` 或 active zones，而不是再次向 public 添加相同规则。

### ⑨ service 规则与非标准 listener 不匹配

`http` service 允许标准端口，不自动跟随应用改到 `8088/tcp`。使用 `--info-service=http` 与 `ss` 对照，再决定添加端口或建立自定义 service。

### ⑩ TCP/UDP 协议写错

同号端口不等于同一网络对象。监听为 UDP 时：

```bash
ss -lnup
```

防火墙规则也必须是 `/udp`。`nc` 对 UDP 的成功判断有限，最终应使用实际协议客户端。

### ⑪ rich rule 限制了来源

普通 port/service 显示允许，但 rich rule 可能对特定来源 reject/drop，或请求来源命中另一 source-bound zone。列出：

```bash
firewall-cmd --zone=<ZONE> --list-rich-rules
firewall-cmd --get-active-zones
```

再按客户端真实源地址判断。

### ⑫ 标准诊断模板

```text
症状
→ 当前证据
→ 至少两个可竞争假设
→ 下一条最有区分度的证据
→ 最小修复
→ 从原客户端再验证
→ 核对 runtime/permanent
```

**[Cheatsheet]** refused 先查 listener；timeout 按路径分层；本机成功远端失败再查 zone；先确认协议、地址和实际 zone，再加规则。

---

<!-- topic: RHCSA-21-S10 -->
## [诊断专题] 10. 最小放行、远程变更与清理边界

防火墙不仅要求“能访问”，还要求不扩大无关暴露面，并且变更可回退。

### ① 不关闭 firewalld 验证服务

停止 firewalld 可能暂时改变症状，但它同时移除了大量安全边界，不能作为默认修复。更好的对照实验是添加一条精确 runtime 规则，并在验证后决定保存或移除。

### ② 不使用 `trusted` 绕过调查

把接口或来源放入 `trusted` 会接受几乎所有流量。这不能证明原规则哪里错误，也会扩大攻击面。

### ③ 最小规则包含四个维度

```text
正确 zone
+ 必要来源范围
+ 必要协议
+ 必要端口或 service
```

没有来源限制要求时使用普通 service/port；明确只允许某网段时使用 rich rule。

### ④ reload 前审查 runtime-only 状态

```bash
firewall-cmd --zone=<ZONE> --list-all
firewall-cmd --permanent --zone=<ZONE> --list-all
```

把差异记录下来。reload 会清除未持久化的 runtime-only 修改。

### ⑤ 清理规则也要先确认依赖

删除 `http` service 或端口前，不能只看当前目标应用。需要确认该 zone 中是否还有其他服务共享端口或 service 定义。

### ⑥ 远程变更保留回滚通道

推荐至少准备：

- 第二个 SSH 会话；
- out-of-band 控制台或虚拟机控制台；
- 明确的反向命令；
- 修改前的 `list-all` 记录。

**[Cheatsheet]** 只改目标 zone/来源/协议/端口；不关防火墙、不进 trusted；reload 前比对双态；远程操作先保住管理通道。

<div class="page-break"></div>

<!-- topic: RHCSA-21-S11 -->
## [经典任务] 11. 发布非标准端口 Web 服务并完整验收

### 任务环境

以下地址仅为本章任务使用的 RFC 5737 文档示例地址，不代表真实考试环境。

| 对象 | 参数 |
|---|---|
| 服务器 | `servera`，地址 `192.0.2.21` |
| 远端客户端 | `clienta`，地址 `192.0.2.31` |
| 服务 | `httpd` |
| 目标端口 | `8088/tcp` |
| 入站接口 | `enp1s0` |
| 目标页面 | `/index.html` |

### 当前状态

- `httpd` 已安装；
- 应用配置已要求监听 `8088/tcp`；
- SELinux 对该端口的映射由前置步骤处理，但本任务仍要求识别它是独立层；
- `firewalld` 已安装并运行；
- 不保证目标端口已经位于正确 zone；
- 不保证 runtime 与 permanent 一致。

### 目标终态

1. `httpd` 当前为 active；
2. 服务器在非回环地址监听 `8088/tcp`；
3. 本机回环和服务器地址均返回 HTTP 响应；
4. `enp1s0` 实际使用的 zone 在 runtime 和 permanent 中均允许 `8088/tcp`；
5. `clienta` 可以访问 `http://192.0.2.21:8088/`；
6. 不开放无关端口，不关闭 firewalld，不使用 `trusted`。

### 验收证据

```text
服务状态
listener
本机回环 HTTP
本机服务器地址 HTTP
实际 zone
runtime query
permanent query
远端 HTTP
```

<div class="page-break"></div>

<!-- topic: RHCSA-21-S12 -->
## [参考解答] 经典任务 11

### 一、调查服务和监听

```bash
systemctl is-active httpd
systemctl status httpd --no-pager
ss -lntp | grep ':8088'
```

如果没有 listener，不先修改防火墙。应检查应用配置、启动日志和 SELinux 端口绑定边界。

### 二、验证本机协议路径

```bash
curl -I http://127.0.0.1:8088/
curl -I http://192.0.2.21:8088/
```

两条命令分别测试回环和服务器地址。这里只要求获得有效 HTTP 响应；不要编造固定状态码或响应头。

### 三、识别实际 zone

```bash
firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
```

把查询结果保存为变量只是示意，实际考试可直接代入：

```bash
ZONE=$(firewall-cmd --get-zone-of-interface=enp1s0)
printf '%s\n' "$ZONE"
```

若输出为 `no zone` 或空，需要回到 NetworkManager/接口绑定调查，不能盲目假设是 `public`。

### 四、建立最小 runtime 和 permanent 规则

```bash
firewall-cmd --zone="$ZONE" --add-port=8088/tcp
firewall-cmd --permanent --zone="$ZONE" --add-port=8088/tcp
```

这条路径避免为了单一变更执行 reload，从而误删其他 runtime-only 规则。

### 五、核对两套状态

```bash
firewall-cmd --zone="$ZONE" --query-port=8088/tcp
firewall-cmd --permanent --zone="$ZONE" --query-port=8088/tcp
firewall-cmd --zone="$ZONE" --list-all
firewall-cmd --permanent --zone="$ZONE" --list-all
```

### 六、从远端完成最终协议验收

在 `clienta` 上执行：

```bash
curl -I http://192.0.2.21:8088/
```

如果失败，按本章诊断链继续，不把本机成功或 query=yes 当作远端成功。

### 七、结果解释

- `systemctl` 证明服务管理状态；
- `ss` 证明真实 listener；
- 本机 `curl` 证明应用本地协议路径；
- 两次 query 证明 runtime/permanent；
- 远端 `curl` 才证明从该客户端出发的完整访问链。

### 典型错误

- 把规则写到 default zone，而实际接口属于另一个 zone；
- 只写 `--permanent`，没有使当前规则生效；
- 只写 runtime，遗漏持久化；
- 加入 `http` service，但应用真实监听 `8088/tcp`；
- 服务只监听 `127.0.0.1`；
- 把 SELinux 端口问题误判为 firewalld 问题。

<div class="page-break"></div>

<!-- topic: RHCSA-21-S13 -->
## [经典任务] 12. 诊断“permanent 已配置但仍然超时”

### 预置场景

- `httpd` 正在 `0.0.0.0:8088` 监听；
- 服务器本机访问 `http://192.0.2.21:8088/` 成功；
- `public` 的 permanent 中存在 `8088/tcp`；
- `public` 的 runtime 中不存在该端口；
- `enp1s0` 当前实际属于 `internal`；
- `clienta` 访问超时。

### 要求

1. 用最少证据定位至少两个独立配置错误；
2. 在实际 zone 建立正确的 runtime/permanent 终态；
3. 不直接删除 `public` 中的遗留规则，先说明清理前需要确认什么；
4. 从 `clienta` 再验证。

<div class="page-break"></div>

<!-- topic: RHCSA-21-S14 -->
## [参考解答] 经典任务 12

### 一、现有证据已经排除的层

listener 与本机服务器地址请求均成功，因此服务和本机协议路径已基本成立。下一步最有区分度的证据是实际 zone 与两套规则，而不是重启 `httpd`。

### 二、确认实际分类

```bash
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
```

预置场景表明实际 zone 为 `internal`。

### 三、确认错误 zone 和双态漂移

```bash
firewall-cmd --zone=public --query-port=8088/tcp
firewall-cmd --permanent --zone=public --query-port=8088/tcp

firewall-cmd --zone=internal --query-port=8088/tcp
firewall-cmd --permanent --zone=internal --query-port=8088/tcp
```

两个独立错误为：

1. 规则位于不处理该接口流量的 `public`；
2. `public` 也只有 permanent，没有对应 runtime。

即使此时执行 reload，`public` 的规则会进入 runtime，但接口仍属于 `internal`，因此问题仍可能存在。

### 四、最小修复

```bash
firewall-cmd --zone=internal --add-port=8088/tcp
firewall-cmd --permanent --zone=internal --add-port=8088/tcp
```

### 五、验证

```bash
firewall-cmd --zone=internal --query-port=8088/tcp
firewall-cmd --permanent --zone=internal --query-port=8088/tcp
```

在 `clienta` 上：

```bash
curl -I http://192.0.2.21:8088/
```

### 六、处理 `public` 中遗留规则

删除前要确认：

- 是否还有其他接口或 source 使用 `public`；
- 是否有其他业务依赖 `8088/tcp`；
- 该规则是否为历史变更或回滚需要。

确认无依赖后，才分别删除 runtime/permanent 中的遗留规则。当前场景中 runtime 本来不存在，因此持久删除可能是：

```bash
firewall-cmd --permanent --zone=public --remove-port=8088/tcp
```

完成后再次 `--check-config`，并在合适变更窗口决定是否 reload。不能为了清理一条未生效的持久规则，未经调查就影响其他 runtime-only 规则。

---

<!-- topic: RHCSA-21-S15 -->
## [本章收束] 13. 把“开放端口”改写为证据矩阵

本章的关键不是记住 `--add-port`，而是建立以下判断顺序：

```text
应用是否能启动
→ 是否真实监听正确地址/端口/协议
→ 本机协议是否成功
→ 流量实际进入哪个 zone
→ runtime 是否允许
→ permanent 是否可持续
→ 远端客户端是否完成真实协议访问
```

遇到故障时，不从症状直接猜命令，而是选择下一条最有区分度的证据：

- refused 优先确认 listener；
- timeout 按 listener、本机、zone、规则和路径推进；
- permanent=yes/runtime=no 说明持久状态尚未成为当前状态；
- 规则存在但远端失败时，先确认实际 zone、监听地址、协议和来源限制；
- 非标准端口启动失败时，把 SELinux 端口类型作为独立分支。

### 章末速查

```bash
# daemon 与 zone
firewall-cmd --state
firewall-cmd --get-default-zone
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --get-zone-of-source=192.0.2.0/24

# 某 zone 当前/持久全貌
firewall-cmd --zone=public --list-all
firewall-cmd --permanent --zone=public --list-all

# service
firewall-cmd --zone=public --add-service=http
firewall-cmd --permanent --zone=public --add-service=http
firewall-cmd --zone=public --query-service=http

# port
firewall-cmd --zone=public --add-port=8088/tcp
firewall-cmd --permanent --zone=public --add-port=8088/tcp
firewall-cmd --zone=public --query-port=8088/tcp

# 配置转换与检查
firewall-cmd --check-config
firewall-cmd --reload
firewall-cmd --runtime-to-permanent

# 服务访问链
systemctl is-active httpd
ss -lntp
curl -I http://127.0.0.1:8088/
curl -I http://<SERVER_IP>:8088/
```

**最终判断：** 配置文件可解析、命令执行成功、服务 active、端口开放和业务远端可用是五种不同事实。RHCSA 任务应把它们组合成可核验终态，而不是用其中一个替代全部。
