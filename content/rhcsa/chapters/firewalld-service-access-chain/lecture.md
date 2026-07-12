---
title: "第 21 章 firewalld 与完整服务访问链"
chapter_id: RHCSA-21
exam: RHCSA
part: "第五篇 网络与远程管理"
slug: firewalld-service-access-chain
status: content_frozen_for_integration
validation: static
live_test: not_performed
base_commit: 961a29b3af4c07a828078a5de90c221a036546df
version: 5.1
---

<!-- 维护元数据仅用于集成，阅读版不显示。 -->

<section class="cover" id="RHCSA-21-COVER">

<div class="cover-kicker">RHEL 9 · RHCSA 实操讲义</div>

<div class="cover-number">21</div>

# firewalld 与完整服务访问链

<div class="cover-subtitle">从服务进程到远端请求：把监听、SELinux、zone、双态规则和协议验收放进同一条证据链。</div>

<div class="cover-tags">
<span>对象模型</span><span>操作语义</span><span>验证</span><span>诊断</span><span>经典任务</span>
</div>

<div class="cover-edition">大字号阅读版</div>

</section>

<section class="navigation pagebreak" id="RHCSA-21-NAV">

# 本章阅读导航

先抓住一条主线：**允许远端访问不是一个命令的结果，而是多个独立对象同时满足条件。** 服务进程、真实监听、SELinux 端口许可、流量进入的 zone、runtime 规则、permanent 规则和远端协议请求，必须按层建立证据。

<div class="model-grid">
<div><b>01</b><strong>定义目标终态</strong><small>明确服务、地址、端口、协议和允许来源</small></div>
<div><b>02</b><strong>证明真实监听</strong><small>服务 active 之后继续检查 socket</small></div>
<div><b>03</b><strong>识别实际 zone</strong><small>从接口或来源绑定确认规则作用范围</small></div>
<div><b>04</b><strong>核对两份状态</strong><small>runtime 回答现在，permanent 回答下次加载</small></div>
<div><b>05</b><strong>完成本机验证</strong><small>区分回环地址、服务器地址与应用协议</small></div>
<div><b>06</b><strong>完成远端验收</strong><small>从独立客户端验证真实访问路径</small></div>
</div>

<div class="nav-columns">
<div>

## 专题地图

| 类型 | 专题 |
|---|---|
| 知识专题 | firewalld 在完整访问链中的职责边界 |
| 知识专题 | zone、default zone 与流量分类 |
| 操作专题 | 查询和维护 interface/source 绑定 |
| 知识专题 | runtime、permanent 与 reload |
| 操作专题 | service、port/protocol 与查询闭环 |
| 知识专题 | 配置来源、覆盖关系与静态检查 |
| 操作专题 | rich rule 的必要表达范围 |
| 操作专题 | 从监听到远端请求的分层验收 |
| 诊断专题 | 从症状推进到下一条区分性证据 |
| 诊断专题 | 最小放行、远程变更与清理边界 |
| 经典任务 | 发布非标准端口 Web 服务 |
| 经典任务 | 修复“permanent 已有但仍然超时” |

</div>
<div>

## 阅读时持续回答

1. 当前请求最终进入哪个 zone？
2. 规则存在于 runtime、permanent，还是两者？
3. service 定义实际包含哪些端口和协议？
4. 应用真正监听在哪个地址和端口？
5. 本机请求证明了哪一段路径？
6. 远端失败时，下一条最有区分度的证据是什么？
7. 非标准端口是否触发 SELinux 独立边界？
8. 哪些修改会在 reload 后丢失或覆盖当前状态？

<div class="note-box"><b>章节边界：</b>NetworkManager 连接配置归第 18 章；systemd 服务生命周期归第 12 章；SELinux 端口类型和 AVC 证据归第 29 章。本章只引用这些对象来完成访问链验收。</div>

</div>
</div>

</section>

<section class="opening pagebreak" id="RHCSA-21-OPEN">

<div class="body-kicker">第 21 章 · 正文</div>

一项网络服务可以“看起来已经完成”，却仍然无法从远端使用。`systemctl is-active httpd` 可能返回 `active`，但进程只监听在 `127.0.0.1`；`8088/tcp` 可能已经加入 firewalld，却加在不处理实际流量的 zone；permanent 配置可能正确，而当前 runtime 尚未加载；本机 `curl` 可能成功，但该请求没有经过远端客户端所使用的接口和防火墙路径。

真正稳定的处理方法，是把“开放端口”改写为一组可以逐层判定的终态：

```text
服务配置正确
→ 服务进程已运行
→ SELinux 允许进程绑定目标端口
→ socket 在正确地址/端口/协议上监听
→ 本机应用协议能够响应
→ 请求被分类到预期 zone
→ runtime 当前允许
→ permanent 能在下次加载后恢复
→ 独立远端客户端完成协议访问
```

本章围绕 firewalld 的核心对象推进：zone 决定规则集合，interface/source 绑定决定流量分类，service 或 port/protocol 表达允许内容，runtime 与 permanent 分别保存“现在”和“下次加载”的状态。诊断时不把局部成功扩大为整体结论，而是用下一条有区分度的证据缩小故障层。

<div class="concept-stack">

<div class="concept"><span>概念</span><p><strong>firewalld</strong> 是动态防火墙管理服务，它通过 zone、service、port 和 rich rule 等高层对象维护主机的包过滤状态。它能允许或拒绝进入主机的流量，却不安装应用、不启动服务，也不会因为“开放端口”而生成监听 socket。观察它时主要使用 <code>firewall-cmd</code>；判断应用是否真正存在，还要转向 <code>systemctl</code>、<code>ss</code> 和协议客户端。</p></div>

<div class="concept"><span>概念</span><p><strong>Zone</strong> 是一组信任边界和允许规则，也是一次入站请求被分类后的处理上下文。接口绑定描述“从哪个接口进入”，来源绑定描述“来自哪个地址范围”；没有显式绑定时，流量可能回落到 default zone。规则写入某个 zone 并不等于实际请求会经过它，所以每次变更都应先确认实际分类。</p></div>

<div class="concept"><span>概念</span><p><strong>接口绑定与来源绑定</strong> 都把流量映射到 zone，但它们表达不同维度。interface 适合描述接入路径，source 适合描述可信网段或单个来源。绑定本身也有 runtime/permanent 两层状态；远程移动管理接口或来源时，可能立刻改变 SSH 会话所经过的规则，因此必须先保留管理通道和回滚路径。</p></div>

<div class="concept"><span>概念</span><p><strong>Runtime 与 permanent</strong> 是 firewalld 同时维护的两份配置。runtime 是当前实际生效的规则；permanent 是 reload、firewalld 重启或系统重启时用于重建 runtime 的持久状态。修改 permanent 不会自动改变现在，修改 runtime 也不会自动保存以后；两者可以暂时不同，但最终必须按题目要求分别验证。</p></div>

<div class="concept"><span>概念</span><p><strong>Service 定义与 port/protocol</strong> 是两种允许流量的表达方式。service 是带名称的通信需求集合，可能包含一个或多个端口、协议或辅助信息；port 规则直接指定端口号或范围及传输协议。标准服务优先使用 service，非标准端口或没有合适定义时使用 <code>PORT/PROTO</code>，并确保它与真实 listener 一致。</p></div>

<div class="concept"><span>概念</span><p><strong>完整服务访问链</strong> 是由多个独立证据组成的业务终态。服务 active 只证明 systemd 的当前管理状态；<code>ss</code> 证明真实 socket；本机 <code>curl</code> 证明一段应用路径；firewalld 查询证明指定 zone 的规则；只有独立远端客户端成功完成协议请求，才证明该客户端到服务的整条访问链可用。任何一层通过，都不能替代其余层。</p></div>

</div>

</section>

<section class="quickref pagebreak" id="RHCSA-21-QUICKREF">

<div class="quickref-intro"><span>操作语义</span> 以下入口分别观察 zone 分类、允许规则、双态转换和访问证据。先理解命令作用对象，再记关键参数。</div>

## `firewall-cmd` 查询 zone 与规则

**SYNOPSIS**

```bash
firewall-cmd [--permanent] [--zone=ZONE] OPTION
```

读取 firewalld 当前或持久配置。查询时显式写出 zone，可以避免把默认上下文误当成真实流量所在位置。

**重要参数 / 形式**

`--get-active-zones`
: 列出当前绑定了 interface 或 source 的活动 zone；不表示这些 zone 一定放行目标服务。

`--get-zone-of-interface=IFACE`
: 查询指定接口当前属于哪个 zone。

`--get-zone-of-source=CIDR`
: 查询指定来源当前属于哪个 zone；source 不使用主机名。

`--zone=ZONE --list-all`
: 查看一个 zone 的当前完整摘要，包括 interfaces、sources、services、ports 和 rich rules。

`--permanent --zone=ZONE --list-all`
: 查看同一 zone 的持久摘要，用于与 runtime 对照。

---

## `firewall-cmd` 添加、删除和查询允许项

**SYNOPSIS**

```bash
firewall-cmd [--permanent] --zone=ZONE \
  --add-service=SERVICE | --add-port=PORT/PROTO
```

对明确的 zone 添加或删除 service、port/protocol，并用同类 `--query-*` 或 `--list-*` 完成闭环。

**重要参数 / 形式**

`--add-service=http`
: 按 service 定义允许通信需求；不会让 `--list-ports` 出现同一端口。

`--add-port=8088/tcp`
: 直接允许目标端口和协议；TCP 与 UDP 是不同对象。

`--remove-service=SERVICE` / `--remove-port=PORT/PROTO`
: 从目标状态中删除对应允许项；删除前分别核对 runtime 和 permanent。

`--query-service=SERVICE` / `--query-port=PORT/PROTO`
: 返回 `yes/no`，常见退出码为存在时 0、不存在时 1，适合脚本条件判断。

`--get-services` / `--info-service=SERVICE`
: 查看可用 service 名称及其实际定义，避免只凭名称猜端口。

---

## `--permanent`、`--reload` 与 `--runtime-to-permanent`

**SYNOPSIS**

```bash
firewall-cmd --permanent ...
firewall-cmd --reload
firewall-cmd --runtime-to-permanent
```

控制两份状态之间的关系。`--permanent` 选择持久配置；`--reload` 用 permanent 重建 runtime；`--runtime-to-permanent` 把整个当前 runtime 保存为 permanent。

**重要参数 / 形式**

`--permanent`
: 让随后支持该选项的操作作用于持久配置；它本身不让修改立即生效。

`--reload`
: 重新加载持久配置并重建 runtime；未持久化的 runtime-only 修改会丢失。

`--runtime-to-permanent`
: 整体保存当前 runtime，不是只提交上一条命令。使用前必须审查是否存在不应持久化的临时规则。

`--check-config`
: 检查 permanent XML 和语义是否可解析；不证明当前规则、监听或远端功能正确。

</section>

<section class="quickref continuation" id="RHCSA-21-QUICKREF-2">

## interface/source 绑定

**SYNOPSIS**

```bash
firewall-cmd [--permanent] --zone=ZONE \
  --change-interface=IFACE | --add-source=CIDR
```

改变流量被分类到哪个 zone。绑定操作比单纯开放端口更容易影响现有远程会话，因此必须先查基线。

**重要参数 / 形式**

`--change-interface=IFACE`
: 将接口放入目标 zone；若接口尚未绑定，通常表现为添加。NetworkManager 管理的 connection profile 细节留给第 18 章。

`--query-interface=IFACE`
: 判断指定接口是否属于当前给出的 zone。

`--add-source=CIDR`
: 将单个地址或网段作为来源绑定到目标 zone。

`--change-source=CIDR`
: 将既有来源移动到另一个 zone。

---

## rich rule

**SYNOPSIS**

```bash
firewall-cmd [--permanent] --zone=ZONE \
  --add-rich-rule='rule family="ipv4" source address="CIDR" \
  port port="PORT" protocol="tcp" accept'
```

在简单 service/port 无法表达“仅允许指定来源”等条件时使用。查询和删除应复用完整规则文本。

**重要参数 / 形式**

`family="ipv4"` / `family="ipv6"`
: 当规则包含地址时显式限定地址族，并与 source 地址一致。

`source address="CIDR"`
: 限制匹配来源；主机名不是稳定的 source 表达。

`service name="http"` 或 `port port="8088" protocol="tcp"`
: 选择通信目标。能用简单 service/port 完成时，不应为了“高级”而改用 rich rule。

`accept` / `reject` / `drop`
: 分别允许、显式拒绝或静默丢弃。诊断时三者表现可能不同。

---

## `ss`、`curl` 与 `nc`

**SYNOPSIS**

```bash
ss -lntp
curl -I http://HOST:PORT/
nc -vz HOST PORT
```

分别验证 socket、应用协议和有限的传输层连通。最终验收优先使用真实协议客户端，而不是只看 TCP 建连。

**重要参数 / 形式**

`ss -lntp`
: 查看 TCP 监听、数字地址、端口和关联进程；UDP 使用 `ss -lnup`。

`curl -I URL`
: 对 HTTP 服务请求响应头；它能证明请求路径上的 HTTP 交互，不证明其他客户端或重启后状态。

`nc -vz HOST PORT`
: 尝试 TCP 建连并输出详细信息；成功不代表 HTTP、TLS 或业务内容正确。

</section>

<section class="topic knowledge pagebreak" id="RHCSA-21-K01">

<div class="topic-heading"><span>知识专题</span><h2>firewalld 在完整服务访问链中的职责边界</h2></div>

排错最常见的问题不是“不会加规则”，而是把一个局部证据扩大成整体结论。先明确每个工具观察的对象，再决定下一步，能避免在错误层反复修改。

### ① <span class="node-label">知识点</span> 防火墙允许与应用监听是两个对象

```bash
firewall-cmd --zone=public --query-port=8088/tcp
```

回答“`public` 的当前规则是否允许 `8088/tcp`”。它不能证明应用已经启动、监听地址正确或请求实际进入 `public`。

```bash
ss -lntp '( sport = :8088 )'
```

回答“主机是否存在 TCP 8088 listener，以及监听地址和进程”。它不能证明 firewalld 允许远端访问，也不能证明 HTTP 内容正确。

### ② <span class="node-label">判断</span> `active`、监听、协议响应和远端可达是四个终态

| 证据 | 能证明 | 不能证明 |
|---|---|---|
| `systemctl is-active httpd` | systemd 当前认为服务 active | 端口、地址、协议和远端可达正确 |
| `ss -lntp` | TCP listener 的地址、端口和进程 | HTTP 内容与远端路径正常 |
| 本机 `curl` | 本机到目标地址的 HTTP 路径 | 指定远端客户端可达、permanent 正确 |
| 远端 `curl` | 该客户端到目标的 HTTP 请求成功 | 所有来源、所有协议和重启后状态正确 |

### ③ <span class="node-label">边界</span> 非标准端口存在独立的 SELinux 分支

服务配置要求监听非标准端口时，SELinux 可能阻止进程绑定，即使 firewalld 已经放行。此时先用服务状态、日志和 `ss` 确认“进程没有建立 listener”，再把 SELinux port type 作为独立假设交给第 29 章的方法验证。不要用关闭 SELinux 或改为 Permissive 作为默认答案。

### ④ <span class="node-label">验证</span> 每条证据都写清证明边界

稳定的验收记录应写成：

```text
证据：firewall-cmd --zone=internal --query-port=8088/tcp → yes
证明：internal 的 runtime 当前包含 8088/tcp
不能证明：请求实际进入 internal、应用正在监听、permanent 已保存
下一证据：查询接口/来源绑定，并检查 permanent 与远端请求
```

<div class="cheatsheet"><b>Cheatsheet</b> 防火墙允许不等于有监听；服务 active 不等于端口正确；本机成功不等于远端成功；远端成功也不能自动证明 permanent 正确。</div>

</section>

<section class="topic knowledge" id="RHCSA-21-K02">

<div class="topic-heading"><span>知识专题</span><h2>zone、default zone 与流量分类</h2></div>

zone 的本质是规则集合与信任边界。考试中最危险的误判，是没有确认请求实际进入哪个 zone，就直接在默认 zone 中增加规则。

### ① <span class="node-label">知识点</span> active zone 只说明当前存在绑定

```bash
firewall-cmd --get-active-zones
```

输出中的 zone 当前至少绑定了 interface 或 source。它不表示该 zone 一定允许目标服务，也不表示系统只存在这些 zone。查看所有定义使用 `--get-zones`，查看一个 zone 的规则使用 `--zone=ZONE --list-all`。

### ② <span class="node-label">知识点</span> default zone 是未显式选择时的回落对象

```bash
firewall-cmd --get-default-zone
```

default zone 不是“最安全”或“最常用”的同义词。改变它可能影响所有依赖默认分类的连接，因此 `--set-default-zone=...` 不是修复单个服务的首选捷径。

### ③ <span class="node-label">比较</span> interface 与 source 描述不同分类维度

```bash
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --get-zone-of-source=192.0.2.0/24
```

interface 适合回答请求从哪条接入路径进入；source 适合表达某个地址或网段的信任范围。source 支持 IP/CIDR、MAC 或 ipset，不支持主机名。名称到地址的稳定映射属于第 19 章。

### ④ <span class="node-label">查询</span> 不靠模糊优先级记忆，读取实际分类

现代 firewalld 还可能存在 zone priority 等版本相关能力。RHCSA 主路径不要求背完内部匹配算法，而是建立可复查顺序：

```text
查询来源绑定
→ 查询接口绑定
→ 查看 active zones
→ 读取目标 zone 的完整规则
→ 明确此次修改写入哪个 zone
```

<div class="cheatsheet"><b>Cheatsheet</b> `--get-default-zone` 看回落；`--get-active-zones` 看当前绑定；`--get-zone-of-interface/source` 看具体对象；`--list-all` 看目标 zone 的规则全貌。</div>

</section>

<section class="topic operation" id="RHCSA-21-O01">

<div class="topic-heading"><span>操作专题</span><h2>查询和维护 interface/source 绑定</h2></div>

绑定改变的是流量分类，而不是单一端口。远程管理服务器时，错误移动接口或来源可能立即让当前 SSH 会话失去允许规则，因此先建立当前/持久基线，再做最小修改。

### ① <span class="node-label">查询</span> 建立绑定基线

```bash
firewall-cmd --state
firewall-cmd --get-default-zone
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --permanent --get-zone-of-interface=enp1s0
firewall-cmd --get-zone-of-source=192.0.2.0/24
firewall-cmd --permanent --get-zone-of-source=192.0.2.0/24
```

先记录当前管理接口、当前 SSH 所需的允许项和预备回滚命令。若 permanent 与 runtime 已经不同，先理解差异来源，不要立即 reload 覆盖现场。

### ② <span class="node-label">操作</span> 添加、移动、查询和移除 interface

```bash
firewall-cmd --zone=public --add-interface=enp1s0
firewall-cmd --zone=internal --change-interface=enp1s0
firewall-cmd --zone=internal --query-interface=enp1s0
firewall-cmd --remove-interface=enp1s0
```

`--change-interface` 在接口尚未绑定时通常相当于添加；已经绑定时把它移到目标 zone。NetworkManager 管理的接口可能由 connection profile 持久关联，完整配置留给第 18 章。

### ③ <span class="node-label">操作</span> 添加、移动、查询和移除 source

```bash
firewall-cmd --zone=internal --add-source=192.0.2.0/24
firewall-cmd --zone=dmz --change-source=192.0.2.0/24
firewall-cmd --zone=dmz --query-source=192.0.2.0/24
firewall-cmd --zone=dmz --remove-source=192.0.2.0/24
```

source 绑定适合把特定网段映射到专用 zone。不要把来源范围写得比题意更宽，也不要把临时客户端地址无调查地持久化。

### ④ <span class="node-label">验证</span> 绑定也要核对两份状态

```bash
firewall-cmd --get-zone-of-source=192.0.2.0/24
firewall-cmd --permanent --get-zone-of-source=192.0.2.0/24
firewall-cmd --zone=internal --list-all
firewall-cmd --permanent --zone=internal --list-all
```

查询结果证明分类和规则所在位置，但不能证明远端客户端已完成协议访问。绑定修改后仍要继续验证 listener、本机请求和远端请求。

### ⑤ <span class="node-label">边界</span> 远程变更先保住管理通道

推荐顺序：确认当前 SSH 来源和接口 → 在目标 zone 先允许管理服务 → 记录回滚命令 → 修改绑定 → 立即开第二个会话验证 → 再处理 permanent。不要关闭防火墙或把接口移入 `trusted` 作为“保险”。

<div class="cheatsheet"><b>Cheatsheet</b> 绑定决定规则作用范围；先保存管理通道，再移动接口或来源；变更后同时查具体绑定和目标 zone 的完整规则。</div>

</section>

<section class="topic knowledge" id="RHCSA-21-K03">

<div class="topic-heading"><span>知识专题</span><h2>runtime、permanent 与 reload：两份状态怎样转换</h2></div>

firewalld 的双态模型允许先临时试验、再决定是否持久化，也允许先准备持久配置、再统一应用。便利的代价是：只看到一份状态时，很容易误判“已经完成”。

### ① <span class="node-label">知识点</span> 不带 `--permanent` 修改当前 runtime

```bash
firewall-cmd --zone=public --add-port=8088/tcp
```

该规则立即进入当前 runtime，但 reload、firewalld 重启或系统重启后会丢失。它适合临时验证和低风险试验，不满足“重启后仍生效”的持久终态。

### ② <span class="node-label">知识点</span> 带 `--permanent` 只修改持久配置

```bash
firewall-cmd --permanent --zone=public --add-port=8088/tcp
```

命令成功表示 permanent 已更新，不表示当前 runtime 已放行。下一步要么补充等价 runtime 修改，要么在审查当前临时状态后执行 reload。

### ③ <span class="node-label">比较</span> 四种双态组合表达不同终态

| Runtime | Permanent | 解释 | 常见下一步 |
|---|---|---|---|
| `yes` | `yes` | 当前和下次加载都允许 | 继续 listener 与远端验收 |
| `yes` | `no` | 当前允许，reload 后丢失 | 若要求持久，补 permanent |
| `no` | `yes` | 持久配置存在，当前尚未应用或后来被改变 | 补 runtime，或审查后 reload |
| `no` | `no` | 两层都不允许 | 确认实际 zone 后最小添加 |

### ④ <span class="node-label">操作</span> 同时满足“现在”和“以后”的两条路径

**逐层修改：**

```bash
firewall-cmd --zone=public --add-port=8088/tcp
firewall-cmd --permanent --zone=public --add-port=8088/tcp
```

优点是不会为了单条变更覆盖其他 runtime-only 状态，适合远程或已有临时规则的系统。

**先准备持久配置再统一应用：**

```bash
firewall-cmd --permanent --zone=public --add-port=8088/tcp
firewall-cmd --check-config
firewall-cmd --reload
```

适合维护窗口中有计划地重建 runtime。reload 前必须确认现有 runtime-only 项是否可以丢失。

### ⑤ <span class="node-label">边界</span> `--runtime-to-permanent` 保存整个当前配置

```bash
firewall-cmd --runtime-to-permanent
```

它不是“保存上一条操作”，而是把整个 runtime 复制为 permanent。若当前含有超宽来源、临时测试端口或应到期的规则，这些状态也可能被保存，因此使用前要比较完整摘要并清理不应持久化的内容。

### ⑥ <span class="node-label">验证</span> 每个目标规则至少查询两次

```bash
firewall-cmd --zone=public --query-port=8088/tcp
firewall-cmd --permanent --zone=public --query-port=8088/tcp
```

`yes/yes` 只证明该 zone 的双态规则，不能证明实际请求进入该 zone，也不能证明应用监听或远端成功。

<div class="cheatsheet"><b>Cheatsheet</b> runtime 回答“现在”；permanent 回答“下次加载”；reload 用 permanent 重建 runtime；`runtime-to-permanent` 是整体复制。</div>

</section>

<section class="topic operation" id="RHCSA-21-O02">

<div class="topic-heading"><span>操作专题</span><h2>service、port/protocol 与增删查列闭环</h2></div>

规则表达应尽量贴近业务对象。标准服务使用有语义的 service 定义；非标准端口或没有合适定义时直接使用 port/protocol。无论选择哪一种，都要完成查询、修改和验证闭环。

### ① <span class="node-label">查询</span> 先看 service 真实定义

```bash
firewall-cmd --get-services
firewall-cmd --info-service=http
firewall-cmd --path-service=http
```

service 名称只是入口，实际允许内容来自定义。不要根据“http”这个词猜所有 Web 端口都包含在内；非标准 8088 通常需要单独 port 规则或自定义 service。

### ② <span class="node-label">操作</span> 标准服务优先使用 service

```bash
firewall-cmd --zone=public --add-service=http
firewall-cmd --permanent --zone=public --add-service=http
firewall-cmd --zone=public --query-service=http
firewall-cmd --permanent --zone=public --query-service=http
firewall-cmd --zone=public --list-services
```

删除时使用对称的 `--remove-service=http`。`--list-services` 只列 service 名称；service 打开的端口不会自动出现在 `--list-ports`，需要 `--list-all` 或 `--info-service` 组合理解。

### ③ <span class="node-label">操作</span> 非标准端口使用 `PORT/PROTO`

```bash
firewall-cmd --zone=public --add-port=8088/tcp
firewall-cmd --permanent --zone=public --add-port=8088/tcp
firewall-cmd --zone=public --query-port=8088/tcp
firewall-cmd --permanent --zone=public --query-port=8088/tcp
firewall-cmd --zone=public --list-ports
```

端口可写为单个端口或范围，例如 `8000-8010/tcp`。TCP 与 UDP 同号端口是两个不同对象，必须按真实 listener 和题意选择。

### ④ <span class="node-label">参数</span> `--add-protocol` 不是开放应用端口

`--add-protocol=gre` 等操作允许的是 IP protocol，不接受 `8088/tcp` 这样的端口表达。普通 Web、SSH、DNS 等服务访问通常使用 service 或 port/protocol，不要把“protocol”这个词混为一谈。

### ⑤ <span class="node-label">边界</span> timeout 只适用于 runtime 临时规则

```bash
firewall-cmd --zone=public --add-port=8088/tcp --timeout=20m
```

规则到期后自动移除，且 `--timeout` 不能与 `--permanent` 组合。它适合受控测试，不应被误写成题目要求的持久答案。

### ⑥ <span class="node-label">验证</span> 规则必须和 listener 对齐

```bash
ss -lntp '( sport = :8088 )'
firewall-cmd --zone=public --query-port=8088/tcp
```

若应用监听 `8088/tcp`，只允许 `http` service（通常指标准端口）并不能自动覆盖它；反过来，开放 8088 也不会让应用改为监听该端口。

<div class="cheatsheet"><b>Cheatsheet</b> 标准通信需求用 service；非标准端口用 `PORT/PROTO`；TCP/UDP 分开；add/remove/query/list 形成闭环。</div>

</section>

<section class="topic knowledge" id="RHCSA-21-K04">

<div class="topic-heading"><span>知识专题</span><h2>配置来源、覆盖关系与 `--check-config`</h2></div>

大多数 RHCSA 任务可以用 `firewall-cmd` 完成，但理解配置来源能避免直接修改 vendor 文件，也能解释自定义 service 和静态检查的边界。

### ① <span class="node-label">知识点</span> vendor 与管理员目录职责分离

```text
/usr/lib/firewalld/zones/       发行版或软件包提供的 zone
/usr/lib/firewalld/services/    发行版或软件包提供的 service
/etc/firewalld/zones/           管理员自定义或覆盖的 zone
/etc/firewalld/services/        管理员自定义或覆盖的 service
```

不要直接编辑 `/usr/lib/firewalld/` 中的 vendor 文件，因为软件包更新可能覆盖它。需要自定义时，通过 `firewall-cmd --permanent --new-service=...` 等接口或在 `/etc/firewalld/` 中建立管理员对象。

### ② <span class="node-label">查询</span> 读取真实定义与路径

```bash
firewall-cmd --info-zone=public
firewall-cmd --path-zone=public
firewall-cmd --info-service=http
firewall-cmd --path-service=http
```

`--path-*` 能帮助确认当前对象来自 vendor 还是管理员目录。路径存在不代表 runtime 已经加载其内容，仍需查询当前 zone。

### ③ <span class="node-label">配置</span> 自定义 service 的必要结构

下面只说明最小对象，不在本章扩展所有 service XML 元素：

```xml
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>web-alt</short>
  <description>Alternative HTTP listener</description>
  <port protocol="tcp" port="8088"/>
</service>
```

自定义 service 的价值是复用和表达业务语义；只需一次开放的非标准端口，直接 port 规则通常更简单。

### ④ <span class="node-label">验证</span> `--check-config` 只检查 permanent

```bash
firewall-cmd --check-config
```

通过表示持久 XML 和语义可解析。它不能证明：

- 当前 runtime 已经加载；
- 实际请求进入目标 zone；
- 应用正在监听；
- SELinux 允许端口；
- 远端客户端能够访问。

### ⑤ <span class="node-label">边界</span> 手工编辑后仍要按双态应用和验收

修改 `/etc/firewalld/` 后先 `--check-config`，再在维护窗口中 reload，随后重新查询 runtime/permanent 和业务访问。不要把“文件保存成功”当作 firewalld 已接受配置。

<div class="cheatsheet"><b>Cheatsheet</b> `/usr/lib` 属于 vendor，`/etc` 属于管理员；`--path-*` 查真实来源；`--check-config` 只证明 permanent 可解析。</div>

</section>

<section class="topic operation" id="RHCSA-21-O03">

<div class="topic-heading"><span>操作专题</span><h2>rich rule 的必要表达范围</h2></div>

rich rule 用于把来源、服务或端口与动作组合起来。本章只覆盖主机入站服务常用的最小模型，不延伸到复杂转发、标记、策略对象或底层 nftables 设计。

### ① <span class="node-label">语法</span> 最小来源限制规则

```bash
RULE='rule family="ipv4" source address="192.0.2.0/24" \
port port="8088" protocol="tcp" accept'

firewall-cmd --zone=public --add-rich-rule="$RULE"
firewall-cmd --permanent --zone=public --add-rich-rule="$RULE"
```

规则表达：在 `public` 中，仅允许 `192.0.2.0/24` 访问 `8088/tcp`。它不会自动拒绝 zone 中其他已经存在的 service/port 规则，所以要先读取完整 zone 状态。

### ② <span class="node-label">参数</span> 地址与 family 保持一致

包含 source/destination 地址时显式写 `family="ipv4"` 或 `family="ipv6"`。IPv4 family 不能配 IPv6 地址，反之亦然。无需地址条件的简单规则通常直接使用 service/port。

### ③ <span class="node-label">比较</span> service 或 port 表达通信目标

```text
service name="http"
```

适合复用已定义 service；

```text
port port="8088" protocol="tcp"
```

适合非标准端口。不要在同一最小规则中堆叠多个独立目标，使查询和删除变得难以复现。

### ④ <span class="node-label">知识点</span> accept、reject 与 drop 的观察差异

- `accept`：允许匹配的新连接；
- `reject`：拒绝并向对端返回错误，客户端通常较快得到失败；
- `drop`：静默丢弃，客户端常表现为等待或超时。

这些表现只是诊断线索，网络路径和客户端重试也会影响最终症状。

### ⑤ <span class="node-label">操作</span> 查询和删除复用同一规则文本

```bash
firewall-cmd --zone=public --query-rich-rule="$RULE"
firewall-cmd --permanent --zone=public --query-rich-rule="$RULE"
firewall-cmd --zone=public --remove-rich-rule="$RULE"
firewall-cmd --permanent --zone=public --remove-rich-rule="$RULE"
```

使用变量或从 `--list-rich-rules` 复制规范化文本，避免删除时因空格、引号或字段差异匹配失败。

### ⑥ <span class="node-label">边界</span> 简单需求不使用 rich rule

“允许所有来源访问 http”直接添加 `http` service；“允许所有来源访问 8088/tcp”直接添加 port。只有来源限制、动作差异或必要日志/限速时才进入 rich rule。

<div class="cheatsheet"><b>Cheatsheet</b> 简单需求用 service/port；来源限制再用 rich rule；地址配 family；查询和删除复用完整规则。</div>

</section>

<section class="topic operation" id="RHCSA-21-O04">

<div class="topic-heading"><span>操作专题</span><h2>从监听到远端请求的分层验收</h2></div>

完整验收从业务终态反推证据。每层失败时停在该层调查，不要在 listener 不存在时继续反复加防火墙规则。

### ① <span class="node-label">目标</span> 先把题意改写成五元组

```text
服务：httpd
地址：服务器外部地址（不是仅 127.0.0.1）
端口：8088
协议：TCP / HTTP
允许来源：题目指定客户端或网段
```

若这些信息不清楚，`firewall-cmd` 的 zone、service、port 和 source 选择都无法唯一确定。

### ② <span class="node-label">验证</span> 服务管理状态

```bash
systemctl is-active httpd
systemctl status httpd --no-pager
```

这一步只证明第 12 章中的服务当前状态。若失败，读取服务日志和配置语法；若 active，继续检查 socket，而不是直接宣布完成。

### ③ <span class="node-label">验证</span> 真实监听

```bash
ss -lntp '( sport = :8088 )'
```

重点读取：

- `LISTEN` 是否存在；
- local address 是 `127.0.0.1`、某个具体服务器地址，还是 `0.0.0.0`/`[::]`；
- 端口和协议是否符合题意；
- 进程是否属于目标服务。

### ④ <span class="node-label">验证</span> 本机协议路径

```bash
curl -I http://127.0.0.1:8088/
curl -I http://192.0.2.20:8088/
```

回环成功但服务器地址失败，优先检查监听地址、应用 virtual host 或本机策略；两者都成功后，才把重点转向实际 zone 和远端路径。

### ⑤ <span class="node-label">验证</span> 实际 zone 与双态规则

```bash
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --zone=internal --query-port=8088/tcp
firewall-cmd --permanent --zone=internal --query-port=8088/tcp
```

查询必须使用真实 zone。规则在 `public` 返回 yes，而请求实际进入 `internal`，并不能允许该请求。

### ⑥ <span class="node-label">验证</span> 独立远端协议请求

在题目指定客户端执行：

```bash
curl -I http://192.0.2.20:8088/
nc -vz 192.0.2.20 8088
```

`curl` 是最终 HTTP 功能证据；`nc` 仅辅助判断 TCP 是否建立。无法从服务器本机替代真正的远端验证，因为本机请求经过的路由和防火墙路径可能不同。

### ⑦ <span class="node-label">判断</span> 纵向验收矩阵

| 层 | 推荐证据 | 通过后能证明 | 仍不能证明 |
|---|---|---|---|
| 服务 | `systemctl is-active` | 当前服务状态 | listener 与协议 |
| Socket | `ss -lntp` | 地址/端口/进程 | HTTP 功能与防火墙 |
| 本机协议 | `curl` 本机地址 | 应用在本机路径响应 | 远端 zone 与持久性 |
| 分类 | zone/interface/source 查询 | 请求应使用的规则集合 | 规则是否允许 |
| Runtime | `query-*` | 当前规则允许 | reload 后仍允许 |
| Permanent | `--permanent query-*` | 下次加载配置包含规则 | 当前已经应用 |
| 远端协议 | 客户端 `curl` | 该客户端整条路径可用 | 其他来源和重启后状态 |

<div class="cheatsheet"><b>Cheatsheet</b> 服务 → listener → 本机协议 → 实际 zone → runtime → permanent → 远端协议；每层只证明自己的对象。</div>

</section>

<section class="topic diagnosis" id="RHCSA-21-D01">

<div class="topic-heading"><span>诊断专题</span><h2>从症状推进到下一条有区分度的证据</h2></div>

诊断不从“多运行几条命令”开始，而是遵循：症状 → 当前证据 → 假设 → 下一条最有区分度的证据 → 最小修复 → 再验证。

### ① <span class="node-label">诊断</span> `Connection refused`

**当前含义：** 对端快速拒绝，常见于目标地址没有 listener，或路径中有显式 reject。

**下一证据：**

```bash
ss -lntp '( sport = :8088 )'
```

listener 不存在时优先调查应用配置、服务日志、监听地址和 SELinux；listener 存在时再查 rich rule 是否 reject、客户端是否访问了错误地址。

### ② <span class="node-label">诊断</span> 连接超时

**当前含义：** 客户端长期得不到响应，可能是 drop、路由、中间设备、错误地址或服务器规则。

**下一证据：** 先确认服务器本机地址请求成功，再查询实际 zone 和 runtime；不要仅凭“超时”直接关闭防火墙。

```bash
curl -I http://192.0.2.20:8088/
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --zone=internal --query-port=8088/tcp
```

### ③ <span class="node-label">诊断</span> 服务 active，但 `ss` 没有目标 listener

**假设：** 服务配置未加载、绑定失败、监听在其他端口、进程已快速退出或 SELinux 阻止非标准端口。

**下一证据：** 服务状态详情、配置语法和日志。此时继续添加 firewalld 规则没有区分度。

### ④ <span class="node-label">诊断</span> 回环成功，服务器地址失败

**假设：** 应用只监听 `127.0.0.1`，或应用配置不接受目标地址。

**下一证据：** `ss` 的 local address。修复应用监听后，再重新做本机地址请求；firewalld 不会改变 listener 地址。

### ⑤ <span class="node-label">诊断</span> 本机服务器地址成功，远端失败

**假设：** 实际 zone 错误、runtime 未放行、来源 rich rule 不匹配、上游路由或中间设备问题。

**下一证据：** `--get-zone-of-interface/source` 与目标 zone 的 `--list-all`。若服务器规则正确，再向路由或中间设备层推进。

### ⑥ <span class="node-label">诊断</span> permanent 为 `yes`，runtime 为 `no`

说明持久配置存在，但当前尚未应用或后来被修改。最小修复可以是补等价 runtime；在确认没有重要 runtime-only 状态后，也可以 reload。不要把再次写 permanent 当作当前修复。

### ⑦ <span class="node-label">诊断</span> runtime 为 `yes`，permanent 为 `no`

说明当前可用但 reload/重启后丢失。若题目要求持久化，补 permanent 后再次查询两层；若只是临时测试，不要无条件保存整个 runtime。

### ⑧ <span class="node-label">诊断</span> 规则存在于错误 zone

命令成功只能证明“某个 zone 被修改”。下一证据是实际接口/来源绑定。最小修复是在正确 zone 建立目标规则；是否删除错误 zone 的遗留项，要先调查是否有其他业务依赖。

### ⑨ <span class="node-label">诊断</span> service 与非标准 listener 不匹配

若 `http` service 已允许，而应用监听 8088，读取 `--info-service=http` 和 `ss` 即可区分。修复是允许实际 `8088/tcp` 或建立合适自定义 service，不是继续重复添加 `http`。

### ⑩ <span class="node-label">诊断</span> TCP/UDP 写错

`8088/tcp` 与 `8088/udp` 是不同规则。使用 `ss -lntp`/`ss -lnup` 和应用协议确定真实传输层，不能仅按端口号判断。

<div class="diagnosis-flow"><b>标准模板</b><br>症状：远端请求超时<br>当前证据：本机 curl 成功，listener 正确<br>假设：请求进入的 zone 没有 runtime 规则<br>下一证据：查询接口/来源绑定和该 zone 的 query-port<br>最小修复：只在实际 zone 添加目标规则<br>再验证：双态查询 + 远端协议请求</div>

<div class="cheatsheet"><b>Cheatsheet</b> refused 先查 listener；timeout 先分本机/远端；本机成功再查实际 zone；双态漂移分别修复“现在”和“以后”。</div>

</section>

<section class="topic diagnosis" id="RHCSA-21-D02">

<div class="topic-heading"><span>诊断专题</span><h2>最小放行、远程变更与清理边界</h2></div>

防火墙排错的目标不是“让所有请求都能过”，而是在不破坏已有业务和安全边界的前提下，建立题目要求的最小终态。

### ① <span class="node-label">安全</span> 不关闭 firewalld 验证服务

关闭防火墙只能暂时绕过这一层，还会放大暴露面，并不能解释原规则为什么失败。正确做法是先证明 listener 和本机协议，再查询实际 zone 和目标规则。

### ② <span class="node-label">安全</span> 不把接口移入 `trusted` 作为默认修复

`trusted` 通常接受所有流量，可能掩盖错误 zone、错误协议和来源范围问题。题目只要求一个服务时，最小答案是目标 zone + 目标 service/port + 必要来源。

### ③ <span class="node-label">判断</span> 最小规则至少包含四个维度

```text
哪个 zone
允许哪个来源（若有要求）
哪个目标端口或 service
哪个协议
```

少一个维度都可能把规则写宽或写错。rich rule 只在简单规则不能表达来源限制时使用。

### ④ <span class="node-label">边界</span> reload 前审查 runtime-only 状态

```bash
firewall-cmd --zone=public --list-all
firewall-cmd --permanent --zone=public --list-all
```

重点比较 services、ports、sources、interfaces 和 rich rules。reload 会用 permanent 重建 runtime，因此不能把它当作无副作用的“刷新按钮”。

### ⑤ <span class="node-label">清理</span> 删除遗留规则前确认依赖

规则位于错误 zone 不代表一定可以立刻删除；它可能服务于另一接口或来源。先查绑定、服务清单和业务 owner，再对 runtime/permanent 做对称清理，最后验证现有业务。

### ⑥ <span class="node-label">恢复</span> 远程操作保留第二条管理路径

在有控制台/BMC 时记录恢复入口；没有控制台时，先在目标 zone 保留 SSH，再改变绑定。操作后不要只依赖当前会话，打开第二个连接确认新请求也可建立。

<div class="cheatsheet"><b>Cheatsheet</b> 不关防火墙、不进 trusted；只改目标 zone/来源/协议/端口；reload 前比对双态；远程操作先保住管理通道。</div>

</section>

<section class="classic-task pagebreak" id="RHCSA-21-T01">

<div class="task-heading"><span>经典任务</span><h2>发布非标准端口 Web 服务并完成全链验收</h2></div>

## 环境与当前状态

- 服务器：`servera.lab.example.com`，业务地址 `192.0.2.20`；
- 远端测试客户端：`clienta.lab.example.com`，来源地址位于 `192.0.2.0/24`；
- 接口：`enp1s0`，实际 zone 必须通过查询确定；
- 服务：`httpd` 已安装，配置目标端口为 `8088/tcp`；
- SELinux：保持 Enforcing。题目说明端口类型已由前置任务正确配置，但仍须把它视为独立核对边界；
- firewalld 正在运行，当前规则未知。

## 目标终态

1. `httpd` 当前运行，并在服务器外部地址可用的 `8088/tcp` 上真实监听；
2. 本机对回环地址和服务器业务地址的 HTTP 请求都能得到响应；
3. 只在处理 `enp1s0` 入站流量的实际 zone 中允许 `8088/tcp`；
4. runtime 与 permanent 均包含目标规则；
5. `clienta` 能取得 HTTP 响应；
6. 不开放无关端口或来源，不降低 SELinux，不关闭 firewalld，不使用 `trusted` 绕过调查。

## 验收矩阵

| 对象 | 必须提交的证据 |
|---|---|
| 服务 | `systemctl is-active httpd` |
| 监听 | `ss` 显示地址、8088/tcp 和目标进程 |
| 本机应用 | 两次 `curl -I`：回环地址、服务器业务地址 |
| Zone | interface/active zone 查询能说明实际分类 |
| Runtime | 实际 zone 的 `--query-port=8088/tcp` 返回 yes |
| Permanent | 同一查询带 `--permanent` 返回 yes |
| 远端应用 | `clienta` 上的 `curl -I` 成功 |

<div class="task-note">请先独立完成。参考解答从下一页开始。</div>

</section>

<section class="reference-answer pagebreak" id="RHCSA-21-A01">

<div class="answer-heading"><span>参考解答</span><h2>先证明 listener，再在实际 zone 建立双态规则</h2></div>

### ① <span class="node-label">调查</span> 读取服务状态与真实监听

```bash
systemctl is-active httpd
systemctl status httpd --no-pager
ss -lntp '( sport = :8088 )'
```

服务 active 后仍必须看到 8088 listener。若没有 listener，本题停在应用/SELinux 层，继续添加防火墙规则没有意义。若只监听 `127.0.0.1:8088`，先修复应用监听地址。

### ② <span class="node-label">验证</span> 完成本机协议证据

```bash
curl -I http://127.0.0.1:8088/
curl -I http://192.0.2.20:8088/
```

第一条证明回环路径；第二条证明服务在业务地址路径响应。两条都成功仍不能替代远端请求。

### ③ <span class="node-label">调查</span> 识别实际 zone

```bash
firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
```

假设查询显示 `enp1s0` 位于 `internal`。后续所有规则都显式使用 `--zone=internal`，不依赖 default zone。

### ④ <span class="node-label">操作</span> 建立 runtime 和 permanent

```bash
firewall-cmd --zone=internal --add-port=8088/tcp
firewall-cmd --permanent --zone=internal --add-port=8088/tcp
```

选择直接 port 规则，是因为服务使用非标准端口，内置 `http` service 不一定包含 8088。分别修改两层，避免为单条规则 reload 并覆盖未知 runtime-only 状态。

### ⑤ <span class="node-label">验证</span> 核对双态与 zone 全貌

```bash
firewall-cmd --zone=internal --query-port=8088/tcp
firewall-cmd --permanent --zone=internal --query-port=8088/tcp
firewall-cmd --zone=internal --list-all
firewall-cmd --permanent --zone=internal --list-all
```

期望得到 `yes/yes`，并确认没有无关来源、宽端口范围或 rich rule 冲突。此时只完成防火墙状态，仍需要远端应用验收。

### ⑥ <span class="node-label">验证</span> 从独立客户端完成协议访问

在 `clienta` 执行：

```bash
curl -I http://192.0.2.20:8088/
nc -vz 192.0.2.20 8088
```

`curl` 是最终 HTTP 证据；`nc` 只作为 TCP 辅助。成功后把证据记录为“clienta → 192.0.2.20:8088 HTTP 可用”，不要扩大为所有来源或所有协议均正确。

### ⑦ <span class="node-label">诊断</span> 典型错误分支

- `ss` 无 listener：回到服务配置、日志和 SELinux 端口边界；
- 回环成功、业务地址失败：检查监听地址；
- 本机业务地址成功、远端超时：检查实际 zone、runtime、rich rule 和上游路径；
- runtime yes、permanent no：补持久规则；
- permanent yes、runtime no：补 runtime，或审查后 reload；
- 只添加 `http` service：读取 service 定义，确认是否覆盖真实 8088。

<div class="cheatsheet"><b>答案主线</b> 服务 → listener → 本机协议 → 实际 zone → runtime/permanent → 远端协议。参数选择由真实对象决定，而不是从“Web 服务”三个字直接猜命令。</div>

</section>

<section class="classic-task pagebreak" id="RHCSA-21-T02">

<div class="task-heading"><span>经典任务</span><h2>修复“permanent 已配置但远端仍然超时”</h2></div>

## 预置场景

- `httpd` 正在 `0.0.0.0:8088` 监听；
- 在服务器本机访问 `http://192.0.2.20:8088/` 成功；
- `firewall-cmd --permanent --zone=public --query-port=8088/tcp` 返回 `yes`；
- `firewall-cmd --zone=public --query-port=8088/tcp` 返回 `no`；
- `clienta` 访问超时；
- 当前接口/来源绑定尚未调查。

## 要求

1. 解释为什么 permanent 中存在规则仍不足以证明当前放行；
2. 找出实际处理 `clienta` 请求的 zone；
3. 在不关闭 firewalld、不移动接口到 `trusted` 的条件下完成最小修复；
4. 使正确 zone 的 runtime 与 permanent 都满足目标；
5. 对 `public` 中的遗留规则先调查依赖，再决定是否删除；
6. 用远端 HTTP 请求完成最终验收。

<div class="task-note">请先独立完成。参考解答从下一页开始。</div>

</section>

<section class="reference-answer pagebreak" id="RHCSA-21-A02">

<div class="answer-heading"><span>参考解答</span><h2>区分“持久配置存在”和“实际 zone 当前允许”</h2></div>

### ① <span class="node-label">判断</span> 已知证据已经排除什么

服务 listener 和本机业务地址请求都正常，说明应用层至少在服务器本机成立。`public` permanent 为 yes 只证明下次加载时 `public` 包含规则；`public` runtime 为 no 说明当前 `public` 尚未允许。更关键的是，尚不知道请求是否进入 `public`。

### ② <span class="node-label">调查</span> 查询实际分类

```bash
firewall-cmd --get-active-zones
firewall-cmd --get-zone-of-interface=enp1s0
firewall-cmd --get-zone-of-source=192.0.2.0/24
```

假设结果显示 `clienta` 来源或 `enp1s0` 实际使用 `internal`。那么 `public` 中的规则与当前请求没有直接关系。

### ③ <span class="node-label">调查</span> 核对正确 zone 的两份状态

```bash
firewall-cmd --zone=internal --query-port=8088/tcp
firewall-cmd --permanent --zone=internal --query-port=8088/tcp
firewall-cmd --zone=internal --list-all
firewall-cmd --permanent --zone=internal --list-all
```

若得到 `no/no`，根因是目标规则写入了错误 zone，同时当前 runtime 未允许。

### ④ <span class="node-label">操作</span> 在正确 zone 建立最小终态

```bash
firewall-cmd --zone=internal --add-port=8088/tcp
firewall-cmd --permanent --zone=internal --add-port=8088/tcp
```

这里不需要 reload，因为分别修改两层即可完成目标，也不会覆盖其他 runtime-only 状态。

### ⑤ <span class="node-label">验证</span> 双态与远端协议

```bash
firewall-cmd --zone=internal --query-port=8088/tcp
firewall-cmd --permanent --zone=internal --query-port=8088/tcp
```

然后在 `clienta`：

```bash
curl -I http://192.0.2.20:8088/
```

只有远端 HTTP 成功，才完成本题业务终态。

### ⑥ <span class="node-label">清理</span> 处理 `public` 遗留规则

先确认 `public` 当前绑定的接口、来源和其他业务：

```bash
firewall-cmd --zone=public --list-all
firewall-cmd --permanent --zone=public --list-all
```

若确认 8088 不再被任何请求或业务需要，再删除持久遗留项：

```bash
firewall-cmd --permanent --zone=public --remove-port=8088/tcp
```

是否同时处理 runtime 取决于其当前状态；已知 runtime 为 no，无需为“对称”而执行无意义删除。最后再次查询两个 zone，并确认远端业务不受影响。

<div class="cheatsheet"><b>答案主线</b> permanent 存在 ≠ 当前生效；目标规则存在 ≠ 请求经过该 zone。先找实际分类，再修正确 zone，最后才清理错误位置。</div>

</section>

<section class="closure" id="RHCSA-21-S01">

<div class="topic-heading"><span>本章收束</span><h2>把“开放端口”改写为可验证的服务访问链</h2></div>

firewalld 的核心不是参数数量，而是三个判断：**请求进入哪里、当前允许什么、下次加载恢复什么。** zone 与绑定回答规则作用范围；service 和 port/protocol 回答允许对象；runtime 与 permanent 回答时间维度；rich rule 只在来源限制等必要条件下扩展表达。

真正的业务终态还在 firewalld 之外。服务 active、listener、本机协议、SELinux 端口边界、远端协议访问分别属于不同层。稳定操作始终遵循：先调查会改变决策的证据，做最小修改，立即验证局部状态，再推进到下一层。

## 主要判断表

| 看到的证据 | 正确解释 | 下一步 |
|---|---|---|
| 服务 `active` | systemd 当前管理状态成立 | 用 `ss` 查 listener |
| `ss` 监听 `127.0.0.1` | 仅回环可用 | 修复应用监听地址 |
| runtime `yes`、permanent `no` | 当前允许，reload 后丢失 | 需要持久时补 permanent |
| runtime `no`、permanent `yes` | 持久已有，当前未应用 | 补 runtime 或审查后 reload |
| 目标规则在 `public` | 只证明 `public` 被配置 | 查询实际接口/来源 zone |
| `curl 127.0.0.1` 成功 | 回环 HTTP 路径成立 | 测服务器地址，再测远端 |
| 远端超时 | 某处无响应，根因未定 | 本机协议 → zone → runtime → 上游路径 |
| `--check-config` 通过 | permanent 可解析 | reload/查询/业务验收仍需执行 |

## 工作方法

```text
1. 把任务写成服务、地址、端口、协议和来源
2. 证明服务与真实 listener
3. 用本机请求隔离应用问题
4. 查询实际 interface/source 绑定
5. 在实际 zone 中维护最小规则
6. 分别验证 runtime 和 permanent
7. 从独立客户端完成真实协议请求
8. 清理前调查依赖，reload 前审查双态差异
```

## 向下一章交接

本章结束后，读者已经能把网络服务访问拆成对象、状态和证据链。下一章进入块设备、分区表与设备签名：对象从“入站流量与规则”切换为“设备、分区和磁盘上的持久标识”，但方法保持一致——先确认对象身份，再修改状态，最后用独立证据验证终态。

<div class="final-boundary"><b>静态可信声明：</b>本章依据 RHEL 9 课程、正式项目规范和官方 firewalld 语义完成静态核对。当前会话未连接 RHEL 9 虚拟机，因此不声称命令已在真实环境跑通；需要实机确认的版本行为已记录在修订说明中。</div>

</section>
