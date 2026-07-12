---
chapter_title: "第 18 章 NetworkManager、IPv4 地址与路由"
chapter_id: RHCSA-18
chapter_slug: networkmanager-ipv4-routing
exam: RHCSA
validation: static
status: content_frozen_for_integration
content_version: "5.1"
base_commit: "961a29b3af4c07a828078a5de90c221a036546df"
sources:
  - RH124-RHEL9-Ch12
  - nmcli(1)
  - nm-settings-nmcli(5)
  - ip-address(8)
  - ip-route(8)
  - NetworkManager.conf(5)
---

<!-- 维护元数据、Section ID 与来源仅属于内容真源；阅读版不显示内部 ID。 -->

<div class="cover-page">
  <div class="cover-kicker">RHEL 9 · RHCSA 实操讲义</div>
  <div class="cover-number">18</div>
  <h1>NetworkManager、<br>IPv4 地址与路由</h1>
  <p class="cover-subtitle">从持久连接配置到内核选路：把 device、profile、地址、路由和验证放进同一条证据链。</p>
  <div class="cover-tags">对象模型　操作语义　验证　诊断　经典任务</div>
  <div class="cover-edition">大字号阅读版</div>
</div>

<section class="reading-nav">

# 本章阅读导航

先抓住一条主线：**NetworkManager 保存的是连接配置意图，内核承担的是当前地址与选路。** 配置、激活和当前状态必须分别取证，不能看到一条成功输出就把整个网络终态判为正确。

<div class="model-grid">
  <div><b>01</b><strong>识别设备</strong><span>确认 device、接口名、链路与管理状态</span></div>
  <div><b>02</b><strong>定位 profile</strong><span>区分 NAME、UUID、绑定设备和活动实例</span></div>
  <div><b>03</b><strong>读取持久属性</strong><span>地址、网关、路由、DNS 与 autoconnect</span></div>
  <div><b>04</b><strong>激活配置</strong><span>明确何时只是保存，何时真正应用到 device</span></div>
  <div><b>05</b><strong>核对内核状态</strong><span>使用 `ip address` 与 `ip route` 读取当前事实</span></div>
  <div><b>06</b><strong>验证具体目的</strong><span>用 `ip route get` 证明 via、dev 与 src</span></div>
</div>

<div class="nav-columns">
<div>

## 专题地图

- **知识专题**　从设备到内核：NetworkManager 管理的对象
- **知识专题**　从地址前缀到目的路径：IPv4 与路由
- **操作专题**　修改前建立 device/profile/当前状态基线
- **操作专题**　修改现有 profile 为静态 IPv4
- **操作专题**　创建新 profile 与管理 autoconnect
- **操作专题**　默认网关、静态路由与 DNS 属性
- **操作专题**　keyfile、reload 与重新激活边界
- **操作专题**　从配置到功能的分层验证
- **诊断专题**　链路、地址、路由、DNS 与监听分层定位
- **经典任务**　DHCP profile 改静态；修复目的选路

</div>
<div>

## 阅读时持续回答

1. 我现在操作的是 device，还是 connection profile？
2. profile 名称、UUID 与接口名分别是什么？
3. 看到的是持久配置，还是活动连接的当前状态？
4. 修改后是否已经激活到目标 device？
5. 地址的前缀是否产生了正确直连网络？
6. 默认路由和静态路由的下一跳是否可直连？
7. 对具体目的，`via`、`dev` 与 `src` 是什么？
8. 当前证据能证明什么，又不能证明什么？

<div class="boundary-note"><strong>章节边界</strong><br>主机名、NSS 与完整 DNS 解析留给第 19 章；SSH 留给第 20 章；firewalld 与完整服务访问链留给第 21 章。</div>

</div>
</div>

</section>

<div class="page-break"></div>

<section class="chapter-opening">

# 第 18 章 · 正文

一台主机“有网卡”并不等于“已经有可用网络”。一次 IPv4 通信至少经过四个状态层：系统先识别网络设备，NetworkManager 再选择并激活一个 connection profile，随后把地址和路由写入内核，最后内核针对具体目的决定出口、源地址和下一跳。任何一层错位，都可能让“配置看起来正确”与“实际路径正确”同时出现矛盾。

最常见的误判有三类。第一，修改 profile 后没有重新激活，却把保存成功当成当前状态已经变化；第二，接口确实有地址，但前缀、默认网关或静态路由让目标走错出口；第三，`ping` 一次成功就宣布 DNS、TCP 监听、firewalld 和应用全部正确。解决这些问题的关键不是背更多命令，而是知道每条命令观察或改变哪个对象。

本章沿着下面的主线推进：

```text
识别 device 与活动 profile
→ 读取持久配置并保存基线
→ 修改地址、网关、路由或 DNS 属性
→ 激活目标 profile
→ 读取内核地址和路由
→ 对具体目的执行选路验证
→ 进行受限的功能验证
```

## 核心概念

<div class="concept-card"><span class="concept-label">概念</span><p><strong>网络设备（device）</strong> 是内核能够发送或接收网络流量的物理或虚拟接口，例如 `enp1s0`。它具有接口名、类型、MAC、链路和管理状态，但它本身不等于一套持久 IP 配置。观察 device 时，重点回答“系统是否看见它、NetworkManager 是否管理它、链路是否可用、当前哪个连接使用它”。</p></div>

<div class="concept-card"><span class="concept-label">概念</span><p><strong>连接配置（connection profile）</strong> 是 NetworkManager 保存的一组配置意图，包含绑定设备、IPv4 方法、地址、网关、路由、DNS 和自动连接等属性。一个 device 可以保存多个 profile；profile 存在只证明配置对象存在，不证明它正在活动。名称、UUID 和接口名即使文字相同，也仍是不同身份维度。</p></div>

<div class="concept-card"><span class="concept-label">概念</span><p><strong>活动连接与当前内核状态</strong> 分属两个相关但不同的证据层。profile 激活后形成 active connection，NetworkManager 再把设置应用到 device；`ip address` 和 `ip route` 显示内核此刻真正采用的地址和路由。修改 profile 后，持久配置与当前状态可以暂时不一致，所以保存成功后仍要激活并复核。</p></div>

<div class="concept-card"><span class="concept-label">概念</span><p><strong>IPv4 地址与前缀</strong> 必须作为一个整体读取。地址标识本机，前缀决定本机认为什么是直连网络，并自然产生直连路由。接口上出现正确地址不代表前缀正确；前缀错误可能让网关看似存在，却无法作为正常下一跳被交付。</p></div>

<div class="concept-card"><span class="concept-label">概念</span><p><strong>默认路由</strong> 是当没有更具体路由时使用的兜底路径，通常由 `ipv4.gateway` 形成 `default via ...`。默认网关不是“能访问互联网”的保证；它首先必须能够通过当前连接直接到达，并且只在没有更长前缀匹配时才被选择。</p></div>

<div class="concept-card"><span class="concept-label">概念</span><p><strong>静态路由</strong> 为某个目的前缀指定下一跳、出口或 metric。它比默认路由更具体时会优先匹配。路由表中存在一条静态路由，只能证明条目被安装；对评分目标仍应使用 `ip route get`，确认该目的实际选中的 `via`、`dev` 和 `src`。</p></div>

<div class="concept-card"><span class="concept-label">概念</span><p><strong>DNS 属性</strong> 是 connection profile 向名称解析链提供的服务器和搜索域输入。本章负责设置 `ipv4.dns`、`ipv4.dns-search` 并观察当前连接是否采用；数字 IP 可达而名称失败时，完整的主机名、NSS、解析器和 DNS 记录调查交给第 19 章。</p></div>

</section>

<section class="quick-reference">

# 操作语义速查区

下面的命令组只建立接口地图。正文专题会继续解释对象选择、参数组合、验证层次和风险边界，不要求每个小操作重复整份手册页。

### `nmcli device`

**SYNOPSIS**

```bash
nmcli device { status | show [IFACE] | connect IFACE | disconnect IFACE }
```

以 device 为中心查看 NetworkManager 状态，或控制设备是否允许连接。

**重要参数 / 形式**

`nmcli device status`
: 列出 device、类型、状态和当前 connection，适合作为第一条基线证据。

`nmcli device show enp1s0`
: 显示设备的活动连接信息，包括当前 IP、网关和 DNS 输入。

`nmcli device disconnect enp1s0`
: 断开设备并阻止它立即自动重新连接；远程执行前必须有恢复通道。

### `nmcli connection show`

**SYNOPSIS**

```bash
nmcli connection show [--active] [ID]
```

以 connection profile 为中心读取全部配置、活动映射或某个 profile 的详细属性。

**重要参数 / 形式**

`nmcli connection show`
: 列出所有 profile 的 NAME、UUID、TYPE 和 DEVICE。

`--active`
: 只显示当前活动连接；它不列出所有持久 profile。

`-f <FIELDS>`
: 只显示目标字段，便于把配置证据收敛到 `ipv4.*` 和 `connection.*`。

### `nmcli connection add / modify`

**SYNOPSIS**

```bash
nmcli connection add type ethernet ifname IFACE con-name NAME [PROPERTY VALUE ...]
nmcli connection modify ID PROPERTY VALUE [PROPERTY VALUE ...]
```

创建新 profile，或修改现有 profile 的持久属性。

**重要参数 / 形式**

`ipv4.method manual`
: 使用静态 IPv4 目标；只写地址而不改 method，连接可能仍保留动态行为。

`ipv4.addresses 192.0.2.10/24`
: 地址与前缀作为一个值设置。

`+ipv4.routes` / `-ipv4.routes`
: 在多值属性中追加或删除指定路由；不带符号通常替换整个列表。

### `nmcli connection up / down`

**SYNOPSIS**

```bash
nmcli connection up ID [ifname IFACE]
nmcli connection down ID
```

激活或停用一个 profile。`up` 是把持久配置应用到 device 的关键动作。

**重要参数 / 形式**

`nmcli connection up office-lan`
: 激活目标 profile；远程修改当前管理接口时可能立即中断会话。

`nmcli connection down office-lan`
: 停用活动连接，但 autoconnect 候选可能再次被自动激活。

`connection.autoconnect yes|no`
: 控制后续自动激活资格，不代表当前连接已经 up 或 down。

### `ip address`

**SYNOPSIS**

```bash
ip [-br] address [show [dev IFACE]]
```

从内核角度读取当前接口地址、前缀、scope 和生命周期。

**重要参数 / 形式**

`-br`
: 使用紧凑输出建立全局基线。

`show dev enp1s0`
: 只查看一个 device，避免把其他接口地址混入判断。

`ip address` 的边界
: 它证明当前地址，不证明 profile 持久属性或重启后的结果。

### `ip route` / `ip route get`

**SYNOPSIS**

```bash
ip route [show]
ip route get DESTINATION
```

读取当前路由表，并计算一个具体目的将使用的出口、下一跳和源地址。

**重要参数 / 形式**

`ip route`
: 查看默认路由、直连路由、静态路由与 metric。

`ip route get 198.51.100.44`
: 验证该目的实际选择的 `via`、`dev` 和 `src`，是本章最关键的选路证据。

`ip route add ...`
: 只改变当前内核状态，不能作为持久 NetworkManager 任务的最终答案。

### `ping` / `ss`

**SYNOPSIS**

```bash
ping [-c COUNT] DESTINATION
ss [-lntup]
```

执行有限的 ICMP 连通测试，或查看本机 socket 监听状态。

**重要参数 / 形式**

`ping -c 3 192.0.2.1`
: 若对端回应，可证明这次 ICMP 往返；失败可能来自对端禁用 ICMP。

`ss -lntup`
: 证明本机是否存在 TCP/UDP 监听，不证明远端流量能穿过 firewalld 到达。

</section>

<section class="topic knowledge" id="RHCSA-18-K01" data-kind="knowledge-topic">

## [知识专题] 从设备到内核：NetworkManager 管理的是哪几个对象

最顺的切入方法不是先背命令，而是先回答四个问题：系统看见了哪个 device，保存了哪些 profile，当前激活的是哪个 profile，内核最终收到了什么地址和路由。NetworkManager 把“配置意图”与“当前运行状态”连接起来，但两者并非同一个对象。

### ① [知识点] device 是流量接口，profile 是可持久配置对象

设备可能是以太网接口、无线接口、桥、bond、VLAN 或其他虚拟接口。本章只以普通以太网 device 为主。device 具有接口名、类型、MAC 地址、carrier 和管理状态；profile 则具有连接名称、UUID、接口绑定、地址、路由、DNS 和 autoconnect 等属性。

```text
设备 enp1s0
├── profile office-dhcp
├── profile office-static
└── profile maintenance
```

同一个 device 可以保存多个 profile，但普通场景同一时刻只会有一个 profile 作为主要活动连接。创建第二个 profile 不会自动删除第一个，也不代表第二个已经被激活。

### ② [知识点] NAME、UUID 与 DEVICE 是三个不同标识

`nmcli connection show` 的 `NAME` 是 `connection.id`，便于人理解；`UUID` 是稳定的 profile 标识；`DEVICE` 表示该 profile 当前激活到哪个设备，没有激活时通常为空。接口名属于 device，例如 `enp1s0`。管理员可以把 profile 也命名为 `enp1s0`，但这只是名称相同，不是对象相同。

在脚本或有同名 profile 的环境中，UUID 更不易歧义；在考试和手工操作中，先用 `nmcli connection show` 确认唯一名称通常足够。

### ③ [知识点] active connection 是 profile 的运行实例

持久 profile 被激活后，NetworkManager 把其中的设置应用到 device，并建立 active connection。此时：

- `nmcli connection show --active` 显示活动 profile；
- `nmcli device status` 显示 device 与活动 connection 的映射；
- `nmcli connection show <CON>` 同时可看到小写的 profile 设置和活动连接的 `GENERAL`、`IP4` 等运行信息；
- `ip address` 与 `ip route` 从内核角度验证最终结果。

不要把“profile 存在”扩大解释为“profile 已激活”，也不要把“profile 已修改”扩大解释为“内核已立即采用全部修改”。

### ④ [知识点] 当前状态、持久状态和功能状态必须分开

| 维度 | 回答的问题 | 典型证据 |
|---|---|---|
| 持久 profile | 重连或启动时准备应用什么 | `nmcli connection show <CON>` |
| 激活映射 | 当前哪个 profile 用在哪个 device | `nmcli connection show --active` |
| 当前内核状态 | 现在有哪些地址和路由 | `ip -br address`、`ip route` |
| 目的路径 | 到某个目标实际怎样选路 | `ip route get <DEST>` |
| 局部功能 | 对端是否回应 ICMP、本机是否监听 | `ping`、`ss` |

一条证据只能证明它所处的层次。`nmcli` 命令返回成功不能证明远端可达；`ping` 成功不能证明 TCP 服务、DNS 解析或应用层正确。

### ⑤ [知识点] managed、connected 与 carrier 不是同一个状态

NetworkManager 可能看见一个 device，却不负责管理它；也可能管理 device，但当前没有活动连接；还可能 profile 已激活，而物理链路没有 carrier。诊断时应区分：

```text
设备是否存在
→ NetworkManager 是否管理
→ 链路是否有 carrier
→ 是否有活动 profile
→ 是否获得或配置地址
```

`nmcli device status` 适合快速看 `STATE` 与 `CONNECTION`；`ip -br link` 适合从内核角度查看接口是否 `UP` 以及是否有 `LOWER_UP`。

### ⑥ [知识点] NetworkManager 服务是配置管理者，不是数据平面

NetworkManager 决定何时把 profile 应用到设备，并维护连接状态；真正的数据包转发、地址和路由匹配由内核网络栈完成。因此排错时既要看 NetworkManager 的对象，也要看内核状态。只看一侧容易遗漏“配置正确但未应用”或“当前状态被其他来源改变”等差异。

**[Cheatsheet]** device 是接口，profile 是配置，active connection 是激活实例；`NAME`、`UUID`、接口名分开识别；profile 证持久意图，`ip` 证当前内核状态。

</section>

<section class="topic knowledge" id="RHCSA-18-K02" data-kind="knowledge-topic">

## [知识专题] 从地址前缀到目的路径：IPv4 和路由如何共同决定通信

IPv4 配置不是“地址、掩码、网关”三个互不相关的输入框。地址和前缀先形成直连网络，内核据此判断哪些目标可直接交付；不在直连网络中的目标再匹配路由表。排错时最有区分度的问题不是“有没有默认网关”，而是“针对这个具体目的，内核选择了哪条路由”。

### ① [知识点] 地址必须连同前缀长度读取

`192.0.2.10/24` 中，`192.0.2.10` 是主机地址，`/24` 表示前 24 位属于网络前缀。该配置通常产生到 `192.0.2.0/24` 的直连路由。若把前缀误写成 `/32`，本机可能不再把网关视为同一链路上的普通邻居；若误写成过大的网络范围，本机可能尝试直接解析本应交给路由器的目标。

地址存在只能证明接口上配置了该地址，不能证明前缀正确。

### ② [知识点] 直连路由由地址和前缀自然产生

接口获得 `192.0.2.10/24` 后，内核通常出现类似路由：

```text
192.0.2.0/24 dev enp1s0 proto kernel scope link src 192.0.2.10
```

它表示目的位于该前缀时直接通过 `enp1s0` 发送，默认使用 `192.0.2.10` 作为源地址。普通考试任务不需要手工再添加同一条直连路由。

### ③ [知识点] 默认网关最终表现为默认路由

`ipv4.gateway 192.0.2.1` 在 profile 激活后通常形成：

```text
default via 192.0.2.1 dev enp1s0
```

默认路由匹配没有更具体路由可用的 IPv4 目的。网关地址原则上应能通过该连接直接到达；如果网关不在直连网络中，普通配置通常无法完成邻居解析和下一跳交付。

### ④ [知识点] 静态路由为特定目的指定更合适的下一跳

例如目标网络 `198.51.100.0/24` 应经过 `192.0.2.254`，可在 profile 中保存一条静态路由。其逻辑是：

```text
目的前缀 198.51.100.0/24
→ 下一跳 192.0.2.254
→ 下一跳可由 enp1s0 的直连网络到达
```

静态路由的目的前缀应描述一组目标，而不是随意填入某个主机地址；若只需要单个主机路由，可使用 `/32`。

### ⑤ [知识点] 路由选择优先采用更长的前缀

若同时存在：

```text
default via 192.0.2.1
198.51.100.0/24 via 192.0.2.254
```

访问 `198.51.100.44` 时，`/24` 比默认路由 `/0` 更具体，因此静态路由优先。只有在相同目的前缀存在多个候选时，metric 等属性才参与进一步选择。本章不展开策略路由和多路由表。

### ⑥ [知识点] metric 是候选路由的成本，不是带宽测速结果

较低 metric 通常代表更优先的候选。`ipv4.route-metric` 可影响由连接产生的路由，包括默认路由。多网卡主机若产生多条默认路由，应明确哪条是主路径，并避免无意识地让多条同协议路由使用相同 metric。

metric 只参与选路，不证明链路质量、延迟或带宽。

### ⑦ [知识点] `ip route get` 回答具体目的的真实选择

```bash
ip route get 198.51.100.44
```

典型字段：

- `via`：下一跳；
- `dev`：出口设备；
- `src`：建议源地址；
- `uid`：执行查询的用户上下文，部分系统会显示；
- `cache`：可能出现的缓存标记，不是持久配置。

`ip route` 适合看全表，`ip route get` 适合验证一个具体目的。路由表中“存在正确条目”与“该目的实际匹配正确条目”是两层证据。

**[Cheatsheet]** 地址加前缀产生直连路由；网关产生默认路由；更长前缀优先；metric 处理同类候选；具体目的用 `ip route get` 看 `via`、`dev`、`src`。

</section>

<section class="topic operation" id="RHCSA-18-O01" data-kind="operation-topic">

## [操作专题] 修改前建立基线：把 device、profile 和当前状态对应起来

网络变更最危险的不是命令不会写，而是改错对象或失去原始状态。开始前先形成一份最小基线：设备是谁，活动 profile 是谁，当前地址和路由是什么，DNS 输入来自哪里。这样才能判断修改后的差异，也能在远程会话中评估回退路径。

### ① [操作] 查看 device 状态与活动 connection

**作用对象：** NetworkManager 管理的设备及其当前连接映射。
**基本形式：**

```bash
nmcli device status
nmcli connection show --active
```

第一条以 device 为中心，第二条以活动 profile 为中心。重点读取 `DEVICE`、`TYPE`、`STATE`、`CONNECTION`、`NAME` 和 `UUID`。

**边界：** `connected` 表示 NetworkManager 认为连接已经激活，不等于所有业务目标都可达。

### ② [操作] 列出全部 profile 并确认准确目标

```bash
nmcli connection show
nmcli -f connection.id,connection.uuid,connection.interface-name,connection.type,connection.autoconnect connection show office-lan
```

先确认活动连接的 `NAME` 或 `UUID`，再修改。不要凭接口名猜 profile 名称，也不要因为看见默认生成的 `Wired connection 1` 就先删除它。

### ③ [操作] 从内核角度查看 link 和地址

```bash
ip -br link
ip -br address
ip -br address show dev enp1s0
```

`-br` 适合快速基线；需要地址生命周期、scope 等细节时使用：

```bash
ip address show dev enp1s0
```

### ④ [操作] 查看路由表和具体目的路径

```bash
ip route
ip route get 198.51.100.44
```

先看默认路由、直连路由和静态路由，再用具体目的验证实际匹配。记录 `via`、`dev` 和 `src`。

### ⑤ [操作] 查看当前连接提供的 DNS 属性

```bash
nmcli -f IP4.DNS,IP4.DOMAIN device show enp1s0
nmcli -f ipv4.dns,ipv4.dns-search connection show office-lan
```

第一条偏当前连接，第二条偏持久 profile。名称解析完整链路属于下一章，本章只验证 NetworkManager profile 和当前连接贡献的 DNS server/search。

### ⑥ [操作] 保存可比较的基线

在考试中可直接阅读输出；在工作变更中建议保存：

```bash
nmcli device status
nmcli connection show --active
nmcli connection show office-lan
ip -br address
ip route
ip route get 198.51.100.44
```

不要把含密码、私钥或企业敏感地址的完整输出随意外发。基线的价值在于比较对象和状态，不是收集越多越好。

**[Cheatsheet]** 先用 `nmcli device status` 找映射，再用 `nmcli connection show` 找 profile；用 `ip -br address`、`ip route`、`ip route get` 固化当前内核基线。

</section>

<section class="topic operation" id="RHCSA-18-O02" data-kind="operation-topic">

## [操作专题] 把现有连接修改为持久静态 IPv4 配置

如果设备只连接一个固定网络，修改 NetworkManager 自动创建或现有活动 profile 通常比“删除后重建”更安全：可以保留 profile 身份、已有 IPv6 设置、MTU、MAC 绑定和其他未要求改变的属性。核心是确认准确对象、一次写入完整 IPv4 终态，然后重新激活并逐层验证。

### ① [操作] 确认活动 profile，而不是按接口名猜测

```bash
nmcli device status
nmcli connection show --active
```

假设确认活动 profile 为 `office-lan`，设备为 `enp1s0`，后续所有 `connection modify` 均应作用于 `office-lan`。

### ② [操作] 把 IPv4 方法改为 manual 并设置地址

```bash
nmcli connection modify office-lan \
  ipv4.method manual \
  ipv4.addresses 192.0.2.10/24
```

从 DHCP 转为静态配置时，`ipv4.method manual` 是关键状态。只设置 `ipv4.addresses` 而保留 `auto`，可能继续获得动态属性或造成不符合目标的混合状态。

### ③ [操作] 设置默认网关

```bash
nmcli connection modify office-lan ipv4.gateway 192.0.2.1
```

网关应能够从 `192.0.2.10/24` 的直连网络到达。激活后验证默认路由，而不是只读回 profile 字段。

若该连接明确不应提供默认路由，可使用：

```bash
nmcli connection modify office-lan ipv4.never-default yes
```

这不是普通静态地址任务的默认设置，只在多连接设计明确要求时使用。

### ④ [操作] 设置 DNS server 和搜索域

```bash
nmcli connection modify office-lan \
  ipv4.dns "192.0.2.53 192.0.2.54" \
  ipv4.dns-search example.test
```

`ipv4.dns` 和 `ipv4.dns-search` 都是多值属性。命令中的空格列表应整体引用，避免 Shell 把后续值当成新的参数。

### ⑤ [操作] 理解替换、追加和删除多值属性

```bash
# 替换整个 DNS 列表
nmcli con mod office-lan ipv4.dns "192.0.2.53 192.0.2.54"

# 追加一个 DNS server
nmcli con mod office-lan +ipv4.dns 192.0.2.55

# 删除指定 DNS server
nmcli con mod office-lan -ipv4.dns 192.0.2.55
```

不带 `+` 或 `-` 通常替换整个属性。先明确目标是“最终只有这些值”还是“在现有列表上增加一项”。

### ⑥ [操作] 设置 autoconnect，但不把它误当成当前激活

```bash
nmcli connection modify office-lan connection.autoconnect yes
```

`autoconnect yes` 表示设备满足条件时允许 NetworkManager 自动激活该 profile；它不证明 profile 此刻已经活动，也不证明重启后一定没有其他候选 profile 抢先被选择。

### ⑦ [操作] 激活修改后的 profile

```bash
nmcli connection up office-lan
```

这一步可能改变当前地址、默认路由和远程会话路径。通过 SSH 修改远端主机时，优先使用控制台、带外管理或确认过的回退路径。不要在没有调查的情况下先 `connection delete` 当前唯一可用 profile。

### ⑧ [操作] 使用一条完整命令表达目标终态

```bash
nmcli connection modify office-lan \
  ipv4.method manual \
  ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 \
  ipv4.dns "192.0.2.53 192.0.2.54" \
  ipv4.dns-search example.test \
  connection.autoconnect yes

nmcli connection up office-lan
```

这不是“执行后就完成”。下一专题必须分别验证 profile、活动映射、当前地址、路由、目的路径和必要功能。

**[Cheatsheet]** 修改现有 profile：`method manual` + 地址/前缀 + gateway + DNS/search + autoconnect；多值属性不带前缀为替换；`con up` 后再验证当前状态。

</section>

<section class="topic operation" id="RHCSA-18-O03" data-kind="operation-topic">

## [操作专题] 创建新 profile，并管理多 profile 与 autoconnect

需要保留原配置作为回退，或同一设备会接入不同网络时，应创建独立 profile。多 profile 的关键不在“会创建”，而在明确绑定设备、激活对象和自动选择规则，避免重启后激活了意外的旧配置。

### ① [操作] 创建绑定指定 device 的以太网 profile

```bash
nmcli connection add \
  type ethernet \
  ifname enp1s0 \
  con-name office-static
```

`type` 说明连接类型，`ifname` 绑定设备，`con-name` 设置 profile 名称。创建成功只表示 profile 已保存，不代表它已经激活。

### ② [操作] 创建时直接写入完整静态 IPv4 目标

```bash
nmcli connection add \
  type ethernet \
  ifname enp1s0 \
  con-name office-static \
  ipv4.method manual \
  ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 \
  ipv4.dns "192.0.2.53 192.0.2.54" \
  ipv4.dns-search example.test \
  connection.autoconnect yes
```

创建后仍要读取 profile，确认命令没有因拼写或引用错误留下缺失属性。

### ③ [操作] 显式激活目标 profile

```bash
nmcli connection up office-static
```

一个 device 上已有其他活动 profile 时，激活新 profile 会切换当前连接。应立即核对：

```bash
nmcli device status
nmcli connection show --active
```

### ④ [知识点] autoconnect 只参与候选 profile 的自动选择

`connection.autoconnect yes` 使 profile 成为自动连接候选。存在多个候选时，可使用：

```bash
nmcli connection modify office-static connection.autoconnect-priority 100
nmcli connection modify office-dhcp connection.autoconnect-priority 0
```

数值更高的 profile 优先。该属性只在同一设备有多个可用候选时有意义；它不改变路由 metric，也不等于“当前强制切换到该 profile”。

### ⑤ [知识点] `connection.autoconnect-priority` 只在多个候选都可自动连接时参与选择

同一 device 上若存在多个 `connection.autoconnect yes` 的 profile，NetworkManager 需要从候选中选择一个。`connection.autoconnect-priority` 的数值越高，通常越优先；它不是链路带宽、路由 metric，也不会强制一个当前不可用的 profile 成功激活。

```bash
nmcli -f connection.id,connection.autoconnect,connection.autoconnect-priority \
  connection show office-static
```

考试环境通常不必主动制造多个自动连接候选。已有多 profile 时，先确认题目要求的目标 profile，再决定是否需要调整优先级；不要用删除其他 profile 代替对象判断。

### ⑥ [操作] 区分停用 profile 与断开 device

```bash
nmcli connection down office-static
nmcli device disconnect enp1s0
```

前者停用指定活动 connection，但 device 仍可能自动激活其他候选 profile；后者把 device 置为断开状态，阻止其继续自动连接，直到手工重新连接。远程执行任何一种命令都可能立即断线。

恢复 device：

```bash
nmcli device connect enp1s0
```

### ⑦ [操作] 删除 profile 前先证明它不再需要

```bash
nmcli connection delete office-dhcp
```

删除会移除持久 profile，若它当前活动还会影响连接。考试题没有要求清理旧 profile 时，不要把删除当成默认步骤。先确认：

- 当前活动 profile 已正确；
- 重启后不会选择旧 profile；
- 旧 profile 不承担恢复或其他网络用途；
- 删除不会让远程主机失去唯一可用配置。

**[Cheatsheet]** 新建用 `type`、`ifname`、`con-name` 明确对象；创建不等于激活；autoconnect priority 选择候选，route metric 选择路由；删 profile 不是静态配置的必需步骤。

</section>

<section class="topic operation" id="RHCSA-18-O04" data-kind="operation-topic">

## [操作专题] 配置默认网关、静态路由与 DNS 属性

地址解决“我是谁、哪些目标在本地链路”，路由解决“其他目标从哪里走”，DNS 属性解决“当前连接向系统提供哪些名称服务器和搜索域”。三者可以在同一个 profile 中配置，但验证方法不同。

### ① [操作] 读取 profile 的默认网关与路由属性

```bash
nmcli -f ipv4.gateway,ipv4.never-default,ipv4.route-metric,ipv4.routes \
  connection show office-lan
```

不要只看 `ipv4.gateway`。若 `ipv4.never-default yes`，该连接可能不生成默认路由；若多连接产生默认路由，metric 会影响候选优先级。

### ② [操作] 向 profile 追加一条静态路由

```bash
nmcli connection modify office-lan \
  +ipv4.routes "198.51.100.0/24 192.0.2.254"
```

其中 `198.51.100.0/24` 是目的前缀，`192.0.2.254` 是下一跳。下一跳应能通过该连接的直连网络到达。

### ③ [操作] 替换整个静态路由列表

```bash
nmcli connection modify office-lan \
  ipv4.routes "198.51.100.0/24 192.0.2.254, 203.0.113.44/32 192.0.2.253"
```

不带 `+` 会把目标属性改为给定列表。已有生产路由较多时，先读取现状，避免无意清空其他条目。

### ④ [操作] 删除指定静态路由

```bash
nmcli connection modify office-lan \
  -ipv4.routes "198.51.100.0/24 192.0.2.254"
```

删除时应与已存属性的目的、下一跳等内容匹配。删除后重新读取 `ipv4.routes`，再激活并检查当前路由表。

### ⑤ [操作] 为连接设置 route metric

```bash
nmcli connection modify office-lan ipv4.route-metric 100
```

多网卡或多默认路由环境中，可让主连接使用更低 metric，备用连接使用更高 metric。不要把多个同协议默认路由无意识地设置成相同 metric。

### ⑥ [知识点] `ipv4.never-default` 与静态路由可以同时存在

备用或仅访问专用网络的连接可能设置：

```bash
nmcli connection modify backup-lan ipv4.never-default yes
nmcli connection modify backup-lan +ipv4.routes "203.0.113.0/24 192.0.2.254"
```

这表示该连接不成为默认出口，但仍可为特定目的提供路由。该模式属于多连接设计，不应在普通单网卡静态地址题中随意套用。

### ⑦ [知识点] `ignore-auto-dns` 和 `ignore-auto-routes` 主要约束动态来源

当 `ipv4.method auto` 时，DHCP 可能提供 DNS 和路由。若需要保留 DHCP 地址但忽略 DHCP DNS，可设置：

```bash
nmcli connection modify office-dhcp \
  ipv4.ignore-auto-dns yes \
  ipv4.dns "192.0.2.53 192.0.2.54"
```

类似地，`ipv4.ignore-auto-routes yes` 可忽略自动路由。若 profile 已改为纯 `manual`，这些属性通常不是完成静态地址任务的关键项。

### ⑧ [操作] 激活后分别验证路由和 DNS 输入

```bash
nmcli connection up office-lan
ip route
ip route get 198.51.100.44
nmcli -f IP4.DNS,IP4.DOMAIN device show enp1s0
```

看到静态路由条目后仍要验证具体目的。看到 DNS server 后只说明连接输入正确；名称记录、NSS 顺序和实际解析属于第 19 章。

**[Cheatsheet]** `gateway` 看默认路由，`routes` 看特定目的，`route-metric` 选候选；`never-default` 禁止该 profile 提供默认路由；DNS 属性只证明连接提供了哪些 server/search。

</section>

<section class="topic operation" id="RHCSA-18-O05" data-kind="operation-topic">

## [操作专题] 理解 keyfile、重新加载与重新激活的边界

RHEL 9 默认把新 NetworkManager profile 保存为 keyfile。日常操作优先使用 `nmcli`，因为它既修改 NetworkManager 的配置对象，也负责持久保存。手工编辑文件只适合迁移、审计或明确需要批量生成配置的场景，并且必须理解“磁盘文件、NetworkManager 已加载对象、活动连接”是三个层次。

### ① [知识点] RHEL 9 新 profile 默认使用 keyfile

持久 profile 通常位于：

```text
/etc/NetworkManager/system-connections/*.nmconnection
```

旧系统遗留的 ifcfg profile 仍可能被读取，但本章以 keyfile 为主，不把 `/etc/sysconfig/network-scripts/` 当作新配置的默认位置。

### ② [知识点] keyfile 权限属于安全边界

连接配置可能包含 Wi-Fi 密钥、VPN 密钥或其他敏感数据。keyfile 应由 root 所有，并限制为 root 可读写。常见要求：

```bash
chown root:root /etc/NetworkManager/system-connections/office-lan.nmconnection
chmod 600 /etc/NetworkManager/system-connections/office-lan.nmconnection
```

本章不建议为了“让文件生效”放宽权限。

### ③ [操作] 使用 `nmcli connection reload` 重新读取连接文件

手工新增或修改 keyfile 后：

```bash
nmcli connection reload
```

也可加载指定文件：

```bash
nmcli connection load \
  /etc/NetworkManager/system-connections/office-lan.nmconnection
```

通过 `nmcli connection modify` 完成的修改已经直接通知 NetworkManager，通常不需要额外 reload。

### ④ [边界] reload 不等于把新设置应用到活动 device

`connection reload` 只让 NetworkManager 重新读取 profile。活动连接可能仍使用旧地址或旧路由，需要：

```bash
nmcli connection up office-lan
```

然后用 `ip` 验证当前状态。不要把“文件已加载”扩大为“网络已切换”。

### ⑤ [边界] `general reload` 与 `connection reload` 作用对象不同

- `nmcli connection reload`：重新读取连接 profile；
- `nmcli general reload`：重新加载 NetworkManager 的全局配置和相关状态，具体范围由参数决定。

修改 `.nmconnection` 文件时，首选前者；不要用重启整个 NetworkManager 服务替代精确的 profile 加载和激活。

### ⑥ [操作] 用 `nmcli` 反向检查文件编辑结果

```bash
nmcli connection show
nmcli -f connection.id,connection.uuid,connection.interface-name,ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.routes \
  connection show office-lan
```

若 profile 没出现，优先检查文件路径、后缀、所有者、权限和语法，而不是反复重启系统。

**[Cheatsheet]** 文件在磁盘、profile 已加载、profile 已激活是三层状态；手工改 keyfile 后 `con reload`，随后按需 `con up`；权限保持 root:root 0600。

</section>

<section class="topic operation" id="RHCSA-18-O06" data-kind="operation-topic">

## [操作专题] 从配置到功能完成分层验证

网络题的验收不能只靠一条 `ping`，也不能只靠 `nmcli` 返回成功。一个稳定的最小证据链应从持久配置开始，逐步走到当前内核状态、目的路径和必要功能。前一层失败时，不要跳到后面随机修改。

### ① [验证] 核对持久 profile 属性

```bash
nmcli -f \
connection.id,connection.uuid,connection.interface-name,connection.autoconnect,connection.autoconnect-priority,\
ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.routes,ipv4.route-metric,ipv4.dns,ipv4.dns-search \
connection show office-lan
```

重点确认目标值和未要求改变的边界，例如是否意外修改了 IPv6。

### ② [验证] 核对活动 profile 与 device 映射

```bash
nmcli device status
nmcli connection show --active
```

profile 正确但 `DEVICE` 为空，说明它没有活动；device 上活动的是另一 profile，则当前状态不会按目标 profile 工作。

### ③ [验证] 核对当前 IPv4 地址和前缀

```bash
ip -br address show dev enp1s0
ip address show dev enp1s0
```

检查目标地址、前缀、重复或遗留地址。只看到目标地址不代表路由和 DNS 正确。

### ④ [验证] 核对当前路由表

```bash
ip route
```

检查：

- 直连网络是否符合前缀；
- 默认路由是否存在且下一跳正确；
- 静态路由是否存在；
- 多条候选路由的 metric 是否符合设计。

### ⑤ [验证] 对评分目标执行具体选路查询

```bash
ip route get 198.51.100.44
```

检查 `via`、`dev`、`src`。这条命令不发送数据包，因此它证明内核的本地选路决定，不证明下一跳或远端一定可达。

### ⑥ [验证] 核对当前 DNS 输入

```bash
nmcli -f IP4.DNS,IP4.DOMAIN device show enp1s0
```

若数字 IP 路径正常但名称失败，应停止修改地址和路由，把问题交给第 19 章的主机名、NSS 与 DNS 名称解析链路。

### ⑦ [验证] 使用 `ping` 做受限的连通测试

```bash
ping -c 3 192.0.2.1
ping -c 3 198.51.100.44
```

先测直连下一跳，再测远端数字 IP。失败可能由目标不回应 ICMP、防火墙、回程路由或中间网络造成；成功也不能证明 TCP 端口和应用协议正确。

### ⑧ [验证] 使用 `ss` 判断本机监听，而不是推断远端可达

```bash
ss -lntup
ss -lnt sport = :22
```

`ss` 能证明本机是否有进程监听指定地址和端口。它不能证明 firewalld 已放行、远端路径可达或客户端认证成功；这些内容分别属于第 21 章和第 20 章。

### ⑨ [验证] 将重连或重启持久性单独列项

本会话没有 live VM，不声称执行了重启验证。在真实环境应在保留恢复入口的前提下验证：

```text
连接重新激活后仍正确
→ device 重新连接后仍选择目标 profile
→ 系统重启后地址、路由、DNS 和 autoconnect 仍正确
```

**[Cheatsheet]** profile → active mapping → address → route table → route get → DNS input → limited function → reboot persistence。每层证据只证明自己的范围。

</section>

<section class="topic diagnosis" id="RHCSA-18-D01" data-kind="diagnosis-topic">

## [诊断专题] 按链路定位：链路、地址、路由、DNS 还是监听

网络故障最容易被“从头重配一遍”掩盖。更稳定的方法是先把症状放到正确层次，再选择一条最能区分假设的证据。每一步只解决当前已经证明的问题，不用后续章节的工具替代本章调查。

<div class="diagnostic-chain">
  <div><strong>症状</strong><span>先写清楚失败的是链路、地址、目的路径、名称还是端口</span></div>
  <div><strong>当前证据</strong><span>读取 device、active profile、address、route 和 route get</span></div>
  <div><strong>假设</strong><span>一次只保留少量可被下一条命令区分的原因</span></div>
  <div><strong>下一条证据</strong><span>优先选择能直接排除一半假设的命令</span></div>
  <div><strong>最小修复</strong><span>只改已证明错误的 profile 属性或活动状态</span></div>
  <div><strong>再验证</strong><span>重新检查持久配置、当前状态、目的路径和必要功能</span></div>
</div>

网络故障最容易出现“反复改同一层”的无效操作。稳定的诊断顺序是：先判断设备和链路，再判断活动 profile 与地址，然后判断具体目的路由，最后进入 DNS、监听、防火墙或应用层。每一步选择最能区分假设的证据。

### ① [诊断] device 不存在或没有 carrier

**症状：** `nmcli device status` 没有目标接口，或 device 为 unavailable/disconnected。
**当前证据：**

```bash
nmcli device status
ip -br link
```

**假设：** 设备未被系统识别、接口名判断错误、虚拟网卡未连接、物理链路无 carrier。
**下一条证据：** 对照 MAC 地址、虚拟机配置或硬件链路；确认 `LOWER_UP`。
**最小修复：** 连接正确设备或链路，不要先改 IPv4 profile。
**再验证：** device 出现并具备可用链路后，继续检查活动 profile。

### ② [诊断] profile 正确，但当前仍是旧地址

**症状：** `nmcli connection show office-lan` 已显示新地址，`ip -br address` 仍是旧地址。
**假设：** profile 尚未重新激活，或另一 profile 仍活动。
**区分证据：**

```bash
nmcli connection show --active
nmcli device status
```

**最小修复：** 激活准确 profile：

```bash
nmcli connection up office-lan
```

**再验证：** 重新检查当前地址和路由，不要只看命令成功消息。

### ③ [诊断] 有地址，但直连网关不可达

**症状：** 目标地址存在，`ping` 网关失败。
**假设：** 前缀错误、网关不在直连网络、链路/VLAN 错误、地址冲突、对端不回应 ICMP。
**下一条证据：**

```bash
ip address show dev enp1s0
ip route get 192.0.2.1
ip neigh show dev enp1s0
```

本章只轻量引用邻居表。若选路认为网关应直连但邻居解析失败，应调查二层链路和对端，而不是继续添加默认路由。

### ④ [诊断] 有地址、有默认路由，但访问特定网络走错网关

**症状：** `ip route get 198.51.100.44` 显示走默认网关，而设计要求走专用下一跳。
**假设：** 缺少更具体静态路由、路由未激活、目的前缀写错。
**区分证据：**

```bash
nmcli -f ipv4.routes connection show office-lan
ip route
ip route get 198.51.100.44
```

**最小修复：** 向准确 profile 添加正确目的前缀和可直达下一跳，激活后再次执行 `route get`。

### ⑤ [诊断] 多条默认路由导致出口不符合预期

**症状：** 多网卡主机有两条 default，实际流量从备用接口离开。
**假设：** route metric 设计错误，或不应提供默认路由的 profile 未设置 `never-default`。
**下一条证据：**

```bash
ip route show default
nmcli -f ipv4.gateway,ipv4.never-default,ipv4.route-metric connection show primary-lan
nmcli -f ipv4.gateway,ipv4.never-default,ipv4.route-metric connection show backup-lan
```

**最小修复：** 调整 metric 或禁止专用连接产生默认路由，不要无调查删除接口配置。

### ⑥ [诊断] 数字 IP 可达，但名称失败

**症状：** `ping -c 1 198.51.100.44` 成功，使用主机名失败。
**当前结论：** 地址和数字目的路径至少局部可用。
**下一条证据：** 检查当前 DNS server/search，然后转入第 19 章：

```bash
nmcli -f IP4.DNS,IP4.DOMAIN device show enp1s0
```

不要继续改 IP 地址、默认网关或静态路由。

### ⑦ [诊断] 路由正确，但 TCP 连接被拒绝或超时

**症状：** `ip route get` 正确，TCP 客户端仍失败。
**下一条证据：** 本机服务端先检查监听：

```bash
ss -lntup
```

无监听转入服务管理；有监听但远端失败，进入第 21 章的 firewalld 与完整服务访问链。SSH 认证细节属于第 20 章。

### ⑧ [诊断] `nmcli connection down` 后连接又出现

**症状：** 停用一个 profile 后 device 又连接。
**假设：** device 自动激活了另一个候选 profile，或该 profile 再次符合自动连接条件。
**区分证据：**

```bash
nmcli connection show --active
nmcli device status
nmcli connection show
```

若目标是让 device 保持断开，使用 `nmcli device disconnect <IFACE>`，但远程执行前必须评估断连。

**[Cheatsheet]** 链路问题先看 device/link；配置与当前不一致先看 active profile；具体路径错误用 `route get`；数字 IP 通而名称失败转 DNS；有路由但 TCP 失败再看监听、防火墙和应用。

</section>

<section class="topic knowledge" id="RHCSA-18-W01" data-kind="knowledge-topic">

## [知识专题] 远程网络变更的最小风险与工作迁移

考试环境常有控制台，真实服务器却经常通过 SSH 管理。网络变更可能在命令执行成功的瞬间切断管理通道，因此工作中的“正确答案”还必须包含风险控制、基线和恢复能力。

### ① [边界] 远程会话不能作为唯一恢复通道

在修改当前管理接口的地址、路由或活动 profile 前，应确认至少一种恢复方式：虚拟机控制台、BMC/iBMC/iDRAC、云控制台、现场人员或预先验证的第二管理链路。

### ② [操作] 最小化修改范围

题目只要求把现有 profile 改为静态地址时，优先修改准确属性；不要顺便删除其他 profile、禁用 IPv6、重启 NetworkManager 或清理未知路由。每个额外变化都扩大故障面。

### ③ [操作] 保存对象级基线和目标终态

工作变更记录至少包括：

```text
目标 device 与 MAC
活动 profile 名称和 UUID
变更前地址、默认路由和目的路径
目标地址、前缀、网关、DNS、静态路由
激活方法和回退 profile
分层验收命令
```

### ④ [边界] 命令成功不等于业务终态正确

`nmcli` 返回 0 只能说明请求被接受或执行完成。必须继续证明：profile 正确、当前状态正确、目标路径正确、必要服务可用。反之，远端不回应 `ping` 也不必然说明本机配置错误。

### ⑤ [工作迁移] 为后续自动化准备稳定状态模型

手工理解应能自然转换为自动化变量：接口、profile 名称、地址/前缀、网关、DNS、路由和 autoconnect。自动化不应依赖“删除所有旧配置后重建”，而应声明目标状态、保留未管理边界并提供幂等验证。

**[Cheatsheet]** 远程改网先有恢复入口；保存 NAME/UUID/device 和路由基线；只改评分对象；命令成功、当前正确、业务正确分别验收。

</section>

<section class="topic task force-new-page" id="RHCSA-18-T01" data-kind="classic-task">

## [经典任务] 把现有 DHCP profile 改为静态地址并验证重连状态

### 环境

训练环境使用文档保留地址，不代表真实考试环境。

```text
主机：node18.example.test
设备：enp1s0
当前活动 profile：office-lan
当前 IPv4 方法：auto
控制台恢复入口：可用
```

### 当前状态

`office-lan` 由 DHCP 获得地址和 DNS。设备上还保存一个未激活的 `maintenance` profile。不得删除任何 profile，也不得改变 IPv6 设置。

### 目标终态

```text
profile：office-lan
IPv4 method：manual
地址：192.0.2.10/24
默认网关：192.0.2.1
DNS server：192.0.2.53、192.0.2.54
DNS search：example.test
autoconnect：yes
```

### 限制条件

- 必须修改现有活动 profile；
- 不得删除 `office-lan` 后重建；
- 不得修改 `/etc/resolv.conf` 作为最终配置；
- 不得禁用 IPv6；
- 不得把 `ping` 成功作为唯一验收；
- 当前会话不执行真实重启，但必须给出重连和重启后的验收项。

### 验收证据

1. 持久 profile 的 IPv4 属性；
2. 活动 profile 与 `enp1s0` 的映射；
3. 当前地址和前缀；
4. 默认路由和源地址；
5. 当前 DNS server/search 输入；
6. 到网关的有限 ICMP 验证；
7. autoconnect；
8. 真实环境后续重启验证清单。

</section>

<section class="topic answer force-new-page" id="RHCSA-18-A01" data-kind="reference-answer">

## [参考解答] 经典任务一

### 1. 调查并保存基线

```bash
nmcli device status
nmcli connection show --active
nmcli connection show
nmcli -f connection.id,connection.uuid,connection.interface-name,connection.autoconnect,\
ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.dns,ipv4.dns-search \
connection show office-lan

ip -br address show dev enp1s0
ip route
ip route get 192.0.2.1
nmcli -f IP4.DNS,IP4.DOMAIN device show enp1s0
```

调查目的：确认 `office-lan` 确实活动在 `enp1s0`，并记录变更前地址、路由和 DNS。若活动 profile 不是题目所述对象，应先解决对象识别差异，不能继续盲改。

### 2. 修改准确 profile

```bash
nmcli connection modify office-lan \
  ipv4.method manual \
  ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 \
  ipv4.dns "192.0.2.53 192.0.2.54" \
  ipv4.dns-search example.test \
  connection.autoconnect yes
```

参数解释：

- `ipv4.method manual`：停止依赖 DHCP 生成 IPv4 终态；
- `ipv4.addresses`：地址和前缀必须同时正确；
- `ipv4.gateway`：为普通外部目的提供默认路由下一跳；
- `ipv4.dns`：不带 `+`，因此把最终 DNS 列表替换为题目指定值；
- `ipv4.dns-search`：设置搜索域；
- `connection.autoconnect yes`：允许启动或 device 可用时自动激活。

没有修改 IPv6 属性，也没有删除 `maintenance`。

### 3. 读取持久配置后再激活

```bash
nmcli -f connection.id,connection.interface-name,connection.autoconnect,\
ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.dns,ipv4.dns-search \
connection show office-lan

nmcli connection up office-lan
```

远程环境中执行 `connection up` 前应确认控制台或其他恢复通道。当前任务已明确控制台可用。

### 4. 分层验证

```bash
# 活动映射
nmcli device status
nmcli connection show --active

# 当前地址
ip -br address show dev enp1s0

# 当前路由与具体目的
ip route
ip route get 192.0.2.1
ip route get 198.51.100.44

# 当前 DNS 输入
nmcli -f IP4.DNS,IP4.DOMAIN device show enp1s0

# 有限功能验证
ping -c 3 192.0.2.1
```

预期判断：

- `office-lan` 活动在 `enp1s0`；
- 当前地址包含 `192.0.2.10/24`；
- 默认路由经 `192.0.2.1`；
- 对外目的的 `route get` 使用 `enp1s0`，源地址为 `192.0.2.10`；
- DNS 输入包含两个服务器和 `example.test`；
- 网关若回应 ICMP，可作为直连路径的附加证据。

### 5. 持久性清单

本章未连接 RHEL 9 VM，不声称已执行以下项目。真实环境应在保留恢复通道时验证：

```text
nmcli device disconnect/connect 后目标 profile 再次激活
系统重启后 office-lan 仍活动
重启后地址、默认路由、DNS 输入仍为目标值
maintenance 未被意外激活
```

### 6. 典型错误

- 按接口名猜 profile 名并改错对象；
- 忘记把 `ipv4.method` 改为 `manual`；
- 使用 `+ipv4.dns` 导致旧 DHCP DNS 被保留；
- 修改完成后未激活；
- 为“清理环境”删除所有旧 profile；
- 直接编辑 `/etc/resolv.conf`，却没有修改连接 profile；
- 只执行一次 `ping` 就宣布全部网络终态正确。

</section>

<section class="topic task force-new-page" id="RHCSA-18-T02" data-kind="classic-task">

## [经典任务] 本机有地址，但到目标网络的选路错误

### 环境

```text
设备：enp1s0
活动 profile：office-lan
当前地址：192.0.2.20/24
默认网关：192.0.2.1
目标网络：198.51.100.0/24
正确下一跳：192.0.2.254
测试目的：198.51.100.44
```

### 当前证据

```text
本机已有 192.0.2.20/24
默认路由存在
ip route get 198.51.100.44 显示 via 192.0.2.1
```

### 目标终态

- `198.51.100.0/24` 经 `192.0.2.254`；
- 路由持久写入 `office-lan`；
- 激活后 `ip route get 198.51.100.44` 选择正确下一跳、device 和源地址。

### 限制条件

- 不改变 `192.0.2.20/24`、默认网关和 DNS；
- 不修改 firewalld 或 SSH 配置；
- 不删除或重建 `office-lan`；
- 不把临时 `ip route add` 作为最终答案；
- 添加路由前必须确认 `192.0.2.254` 从本机选路角度属于直连下一跳；
- 已有其他静态路由时不得无调查地替换整个 `ipv4.routes` 列表。

### 验收证据

| 层次 | 验收命令 | 目标判断 |
|---|---|---|
| 对象 | `nmcli connection show --active` | `office-lan` 活动在 `enp1s0` |
| 持久配置 | `nmcli -f ipv4.routes connection show office-lan` | 包含目标前缀和下一跳 |
| 当前路由 | `ip route` | 内核已安装更具体的 `/24` 路由 |
| 目的选路 | `ip route get 198.51.100.44` | `via 192.0.2.254 dev enp1s0 src 192.0.2.20` |
| 边界 | `ping`（可选） | 只作为对端允许 ICMP 时的附加证据 |

</section>

<section class="topic answer force-new-page" id="RHCSA-18-A02" data-kind="reference-answer">

## [参考解答] 经典任务二

### 1. 证明当前对象和问题层次

```bash
nmcli device status
nmcli connection show --active
ip -br address show dev enp1s0
ip route
ip route get 198.51.100.44
```

已知地址存在且目的走默认网关，因此问题集中在“缺少更具体路由”或“正确 route 未应用”，而不是先修改地址、DNS 或 firewalld。

### 2. 确认下一跳可以直连

```bash
ip route get 192.0.2.254
```

预期应显示 `dev enp1s0`，通常不需要 `via`，源地址为 `192.0.2.20`。这证明从本机选路角度，下一跳属于直连网络；它仍不证明下一跳设备一定在线。

### 3. 读取现有持久路由

```bash
nmcli -f ipv4.routes connection show office-lan
```

先看现状，避免替换整个列表时删除其他业务路由。本任务要求追加一条，因此使用 `+ipv4.routes`。

### 4. 添加持久静态路由并激活

```bash
nmcli connection modify office-lan \
  +ipv4.routes "198.51.100.0/24 192.0.2.254"

nmcli -f ipv4.routes connection show office-lan
nmcli connection up office-lan
```

没有使用 `ip route add` 作为最终方案，因为后者只改变当前内核路由，重连或重启后通常丢失。

### 5. 验证当前路由和具体目的

```bash
ip route
ip route get 198.51.100.44
```

预期选路包含：

```text
198.51.100.44 via 192.0.2.254 dev enp1s0 src 192.0.2.20
```

输出细节可能含 `uid` 或缓存字段，验收重点是 `via`、`dev`、`src`。

### 6. 可选连通验证与边界

```bash
ping -c 3 192.0.2.254
ping -c 3 198.51.100.44
```

下一跳或远端可能禁用 ICMP，因此 `ping` 失败不能推翻已经正确的本地选路证据。若评分要求具体 TCP 服务，应进入监听、firewalld 和应用协议的相邻章节验证。

### 7. 典型错误

- 使用 `ip route add` 完成当前状态，却没有写入 profile；
- 把目的写成 `198.51.100.44/24`，没有按网络边界表达目的前缀；
- 下一跳不在本机直连网络；
- 使用不带 `+` 的 `ipv4.routes`，无意替换其他路由；
- 只在 `ip route` 中看见条目，没有执行 `ip route get`；
- 因远端不回应 `ping` 而继续修改已经正确的地址和路由。

</section>

<section class="topic summary" id="RHCSA-18-S01" data-kind="summary">

## [本章收束] 把“网络正确”拆成可以逐项证明的结论

NetworkManager 题目的难点通常不在命令长度，而在对象和证据错位。一个稳定的完成顺序是：先识别 device 和活动 profile，再读取持久属性；修改后明确触发激活；随后从内核角度检查地址、路由和具体目的路径；最后才做受限的连通或监听验证。

### 工作方法：每次网络变更都保留四份证据

```text
对象证据：device、profile NAME、UUID、活动映射
配置证据：ipv4.method、addresses、gateway、routes、dns、autoconnect
当前证据：ip address、ip route、ip route get
功能证据：ping 或 ss 所能证明的局部结果
```

这四份证据不能互相替代。profile 写对但未激活，当前状态仍可能是旧值；当前路径正确但远端不回应 ICMP，也不能直接反推本机配置错误；本机存在监听，同样不能证明 firewalld 和远端访问链已经正确。

### 主要判断表

| 看到的证据 | 可以得出的结论 | 不能据此断言 | 下一步 |
|---|---|---|---|
| `nmcli connection show <CON>` 属性正确 | 持久 profile 已保存目标值 | 内核已经采用这些值 | 核对 active connection，再看 `ip` |
| `nmcli connection show --active` 显示目标 profile | 目标 profile 当前处于活动状态 | 地址、路由和业务一定正确 | 查看 address、route 和 route get |
| `ip -br address` 地址正确 | 内核当前已配置该地址和前缀 | 默认路由、DNS 或远端可达 | 查看 `ip route` |
| `ip route` 中存在目标路由 | 路由表包含该条目 | 具体目的实际选中它 | 执行 `ip route get <DEST>` |
| `ip route get` 的 `via/dev/src` 正确 | 本地内核对该目的的选路正确 | 下一跳或远端一定在线 | 按要求做受限功能验证 |
| `ping` 成功 | 该次 ICMP 往返成功 | TCP、DNS、应用和所有路径都正确 | 根据评分对象继续验证 |
| `ss -lntup` 显示监听 | 本机存在对应 socket | 远端流量可穿过防火墙到达 | 转第 21 章检查完整访问链 |

### 向下一章交接

本章只把 DNS server 和 search domain 当作 connection profile 的属性，并观察它们是否进入当前连接。若数字 IP 路径正确而名称仍失败，下一步不应继续重写地址和路由，而应进入第 19 章《主机名、NSS 与 DNS 名称解析》，检查主机名、`/etc/hosts`、NSS 顺序、解析器状态和 DNS 记录。

SSH 的客户端、服务端和密钥认证属于第 20 章；端口放行、zone、runtime/permanent 与完整服务访问链属于第 21 章。本章到此只负责把数据包送到正确的本地出口，并提供清楚的网络层证据。

</section>
