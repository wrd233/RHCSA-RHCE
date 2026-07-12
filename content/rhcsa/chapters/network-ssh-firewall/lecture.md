---
title: "第六章 网络、名称解析、SSH 与 firewalld"
chapter_id: RHCSA-NETWORK
exam: RHCSA
validation: static-verified
sources: [RH124-RHEL9, RHCSA-Course-10, RHCSA-Course-14, RHCSA-Course-26, RHCSA9-Mock]
---

# 第六章　网络、名称解析、SSH 与 firewalld

网络任务包含至少四类状态：NetworkManager 的持久连接配置、内核当前地址和路由、名称解析结果，以及服务监听和防火墙策略。能 ping 网关不能证明 DNS 正确，SSH 密钥存在不能证明服务端接受，runtime 防火墙放行也不能证明重载后保留。本章用逐层证据避免把连通性结论扩大。

**[概念]** NetworkManager device 是网卡等设备，connection 是可持久保存并激活到设备上的配置 profile。一个设备可有多个 profile，但通常只有一个处于活动状态；修改未激活 profile 不会立即改变内核网络。

**[概念]** IPv4 地址由地址和前缀构成，默认网关是 `0.0.0.0/0` 路由的下一跳；DNS server 与 search domain 影响名称解析。主机名、`/etc/hosts`、DNS 与 NSS 查询顺序是不同对象。

**[操作语义]** `nmcli device` 查询设备状态，`nmcli connection` 创建、修改、激活和查询 profile；`ip address/route` 观察内核当前状态；`getent hosts` 通过系统名称服务解析名称。

**[操作语义]** `ssh` 建立远程会话，`ssh-keygen` 生成密钥，`ssh-copy-id` 安装公钥；`firewall-cmd` 管理 zone 中的 runtime 或 permanent service/port 规则，reload 用持久配置重建 runtime。

<section class="topic knowledge" id="RHCSA-NETWORK-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> device、connection、地址、路由与 DNS

### ① <span class="point-label">[知识点]</span> profile 名称不一定等于接口名

`nmcli device status` 显示设备、类型、状态和活动 connection；`nmcli connection show` 显示所有 profile，`--active` 只显示已激活。操作时先从设备映射到活动 profile，不从 `ens160` 猜 profile 也叫 `ens160`。

```bash
nmcli device status
nmcli connection show --active
nmcli -f NAME,UUID,TYPE,DEVICE connection show
```

### ② <span class="point-label">[知识点]</span> 持久配置与内核当前状态需交叉查询

`nmcli connection show <CON>` 显示 profile 属性，`ip -br address` 和 `ip route` 显示当前内核状态，`resolvectl` 或 `/etc/resolv.conf` 显示当前 DNS 入口。profile 中写入地址但未重新激活时，这两组证据可能不同。

### ③ <span class="point-label">[知识点]</span> 前缀决定直连网络，不是地址装饰

`192.0.2.10/24` 的 `/24` 决定哪些目的地址通过本地链路到达。网关必须能通过某条路由到达；错误前缀会造成邻居或路由判断偏差。`ip route get <DEST>` 显示内核为特定目的选择的源地址、出口和下一跳，比只看 route 表更直接。

### ④ <span class="point-label">[验证点]</span> 每个网络结论选择对应证据

地址：`ip -br a`；默认路由：`ip route`；路径选择：`ip route get`；DNS：`getent hosts`；监听：`ss -lntup`；远端应用：协议客户端。ICMP 成功只能证明对应路径允许 ICMP，不证明 TCP 端口或应用层。

**[Cheatsheet]** 设备/profile 映射 `nmcli device status`；持久属性 `nmcli con show`；当前地址/路由 `ip -br a`/`ip route`；目的路径 `ip route get`；解析 `getent hosts`。

</section>

<section class="topic operation" id="RHCSA-NETWORK-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 创建并激活静态 IPv4 连接

### ① <span class="point-label">[操作点]</span> 先保存远程访问与当前基线

修改前记录设备、活动 profile、地址、路由和 DNS；远程考试环境中改变正在使用的连接可能立即断开会话。确认有控制台或恢复入口，并避免删除仍需使用的 profile。

```bash
nmcli device status
nmcli connection show --active
ip -br address
ip route
```

### ② <span class="point-label">[参数点]</span> 创建与修改都要表达 method

创建 profile 时 `type ethernet`、`ifname`、`con-name` 明确对象；静态 IPv4 需要 `ipv4.method manual`、地址/前缀、gateway 和 DNS。禁用 IPv6 只有题目明确要求时做，不把它当作解决 IPv4 问题的默认步骤。

```bash
nmcli connection add type ethernet ifname enp1s0 con-name exam-static \
  ipv4.method manual ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 ipv4.dns '192.0.2.53 192.0.2.54'
nmcli connection modify exam-static connection.autoconnect yes
```

修改现有 profile 使用 `nmcli con mod`。多值属性前缀 `+` 表示追加，`-` 表示删除指定值；不带前缀通常替换整个属性，修改 DNS 等列表前先查询当前值。

### ③ <span class="point-label">[操作点]</span> 激活并处理旧 profile

```bash
nmcli connection up exam-static                  # 把 profile 应用到设备
nmcli connection show --active
```

如果另一 profile 会自动抢占设备，先理解优先级和 autoconnect，再禁用或删除旧项。`nmcli con down` 会立即中断该连接，远程操作必须评估风险。

### ④ <span class="point-label">[验证点]</span> 配置、当前状态与功能三层

```bash
nmcli -f ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.dns con show exam-static
ip -br address show enp1s0
ip route
getent hosts serverb.example.com
ping -c 2 192.0.2.1
```

ping 网关失败时先查接口、前缀和路由；DNS 失败不应通过反复修改地址掩盖。持久性由 profile 与 autoconnect 证明，必要的重启验证应在恢复路径存在时进行。

**[Cheatsheet]** 基线 → `nmcli con add/mod` 明确 manual/address/gateway/DNS → `con up` → profile 属性 + `ip` 当前状态 + DNS/连通功能；多值属性修改前先查。

</section>

<section class="topic operation" id="RHCSA-NETWORK-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 配置主机名、hosts 与名称解析

### ① <span class="point-label">[操作点]</span> 主机名与地址映射分开配置

`hostnamectl set-hostname <FQDN>` 设置静态主机名。`/etc/hosts` 条目典型顺序为地址、规范名、别名：

```hosts
192.0.2.10  servera.example.com  servera
```

修改 hosts 前检查是否已有同名或同地址冲突。它是本地解析来源，不会发布到 DNS，也不会自动改变远端客户端。

### ② <span class="point-label">[知识点]</span> 查询工具走的解析路径不同

`getent hosts <NAME>` 走 NSS 配置，适合验证应用常用的系统解析；`dig`/`host` 直接查询 DNS，不会同样反映 `/etc/hosts`。`ping` 混合了名称解析和 ICMP，失败时不够精确。

### ③ <span class="point-label">[验证点]</span> 分别证明短名、FQDN 与反向需求

```bash
hostnamectl status
getent hosts servera.example.com
getent hosts servera
```

正向解析正确不自动证明反向 PTR；只有题目或服务明确要求反向解析时才验证。`hostname -f` 的结果依赖主机名和解析配置，应作为组合结果而非唯一真相。

**[Cheatsheet]** 主机名 `hostnamectl`；本地映射 `/etc/hosts`；系统解析 `getent hosts`；DNS 专查 `dig/host`；短名、FQDN、反向解析按题意分别验收。

</section>

<section class="topic operation" id="RHCSA-NETWORK-O03" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 建立 SSH 密钥认证并验证服务端边界

### ① <span class="point-label">[知识点]</span> 私钥留在客户端，公钥进入服务端账号

`ssh-keygen` 生成密钥对，私钥必须受保护，`.pub` 才可分发。`ssh-copy-id user@host` 把公钥追加到远端用户的 `~/.ssh/authorized_keys`，但执行时通常仍需要一次现有认证。

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519
ssh-copy-id -i ~/.ssh/id_ed25519.pub alice@serverb
ssh -i ~/.ssh/id_ed25519 alice@serverb
```

### ② <span class="point-label">[知识点]</span> 客户端与服务端配置分别影响连接

客户端 `~/.ssh/config` 可设置 Host、Hostname、User、IdentityFile；服务端 `/etc/ssh/sshd_config` 与 drop-in 决定监听、认证和账号限制。修改服务端前用 `sshd -t` 校验，再 reload；不要在尚未验证密钥时关闭口令认证，避免锁死访问。

权限通常要求 `~/.ssh` 仅用户可写、`authorized_keys` 不允许其他人写。SELinux 上下文错误可用 `restorecon -Rv ~/.ssh` 恢复默认规则，不能只靠 chmod 解释所有拒绝。

### ③ <span class="point-label">[知识点]</span> known_hosts 验证服务器身份

首次连接记录主机密钥。主机密钥改变可能是系统重装或攻击，不能无条件删除条目继续；先核对可信指纹，再使用 `ssh-keygen -R <HOST>` 移除旧记录并重新接受。

### ④ <span class="point-label">[验证点]</span> 用详细输出定位连接层

`ssh -v` 显示配置选择、密钥尝试和认证结果；服务端查 `journalctl -u sshd`。成功登录后运行 `id` 和 `hostname` 证明实际远端身份，不能只看到连接命令退出 0。

**[Cheatsheet]** 生成 `ssh-keygen` → 公钥 `ssh-copy-id` → `ssh -i`；服务端改前 `sshd -t`；失败用客户端 `-v` + 服务端 journal；主机密钥变化先核指纹。

</section>

<section class="topic operation" id="RHCSA-NETWORK-O04" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 管理 firewalld zone、service 与端口

### ① <span class="point-label">[知识点]</span> zone 通过接口或源选择规则集合

先查 active zones 和接口归属：

```bash
firewall-cmd --get-active-zones
firewall-cmd --get-default-zone
firewall-cmd --zone=public --list-all
```

默认 zone 只用于没有显式绑定的连接/源。向错误 zone 添加规则会显示成功却不影响实际流量，因此每次修改显式写 zone 更清晰。

### ② <span class="point-label">[操作点]</span> service 与 port 表达层次不同

service 是 `/usr/lib/firewalld/services` 或 `/etc/firewalld/services` 中定义的一组端口/协议；port 是直接的 `PORT/PROTOCOL`。已存在准确 service 时优先 service；非标准端口或无 service 定义时使用 port。

```bash
firewall-cmd --zone=public --add-service=http
firewall-cmd --zone=public --add-service=http --permanent
firewall-cmd --zone=public --add-port=8080/tcp --permanent
```

不带 `--permanent` 修改 runtime，立即生效但 reload 后消失；带 permanent 只写持久配置，不立即改变 runtime。可以分别执行两条，或先写 permanent 后 reload，但 reload 会用全部持久配置替换 runtime，可能丢弃其他未持久变化。

### ③ <span class="point-label">[验证点]</span> runtime、permanent、监听和外部访问

```bash
firewall-cmd --zone=public --query-service=http
firewall-cmd --zone=public --query-service=http --permanent
ss -lntp | grep ':80'
curl -I http://servera.example.com/
```

防火墙规则只允许流量，不创建监听。localhost 访问可能不经过与远端相同的 zone/路径，外部访问验证应从题目指定客户端执行。

**[Cheatsheet]** 先查 active zone；优先 service，非标准用 `port/protocol`；runtime 与 permanent 分别查询；reload 会重建 runtime；最终仍查监听和外部协议访问。

</section>

<section class="topic diagnosis" id="RHCSA-NETWORK-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 按链路定位地址、路由、解析、监听或过滤失败

### ① <span class="point-label">[诊断点]</span> 地址正确但目标不可达

用 `ip route get <DEST>` 看出口、源地址和下一跳，检查前缀、默认路由和邻居；不要先改 DNS，因为数字 IP 路径尚未成立。

### ② <span class="point-label">[诊断点]</span> IP 可达但名称失败

用 `getent hosts` 区分系统解析，查 DNS server/search 和 `/etc/hosts` 冲突；`dig` 可进一步检查 DNS。不要把 IP 写入应用配置绕过题目要求的名称解析。

### ③ <span class="point-label">[诊断点]</span> 服务 active 但远端连接拒绝或超时

拒绝通常优先查是否监听目标地址/端口；超时再查路由、防火墙和中间路径，但两者不能绝对等同根因。依次验证 `ss`、本机协议请求、firewalld zone/runtime/permanent、远端请求和 SELinux 端口类型。

### ④ <span class="point-label">[诊断点]</span> SSH 公钥被拒绝

客户端 `ssh -v` 看是否选择并提供目标 key，服务端 journal 看拒绝原因；检查远端用户、家目录、`.ssh`/authorized_keys 所有者权限和 SELinux 标签，再检查 sshd 的有效配置。

**[Cheatsheet]** 数字 IP 不通查地址/路由；IP 通名称不通查 NSS/DNS；服务问题查监听→本机→防火墙→远端→SELinux；SSH 用双端日志与身份/权限证据。

</section>

<section class="classic-task task-page" id="RHCSA-NETWORK-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 配置静态网络、SSH 密钥与 Web 访问

将接口 `enp1s0` 配置为持久静态地址 `192.0.2.10/24`，网关 `192.0.2.1`，DNS `192.0.2.53`，profile 名为 `exam-static` 且开机自动连接。主机名为 `servera.example.com`，本机能解析 `serverb.example.com` 到题目地址。

为用户 `alice` 建立到 serverb 的 ed25519 密钥认证，不泄露私钥。使 servera 的 httpd 可从外部通过标准 HTTP service 访问，firewalld 规则当前和持久配置都正确。

不得删除未确认用途的连接 profile，不得在密钥验证前关闭口令认证。验收包括 profile、当前地址/路由/DNS、主机名解析、SSH 实际远端身份、httpd active/enabled/监听、正确 zone 的 runtime/permanent 以及外部 HTTP 请求。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-NETWORK-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 从 profile 激活推进到外部服务链

### ① <span class="point-label">[操作点]</span> 记录基线并创建连接

```bash
nmcli device status
nmcli connection show --active
ip -br address; ip route
nmcli con add type ethernet ifname enp1s0 con-name exam-static \
  ipv4.method manual ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 ipv4.dns 192.0.2.53 \
  connection.autoconnect yes
nmcli con up exam-static
```

### ② <span class="point-label">[操作点]</span> 配置名称和密钥

```bash
hostnamectl set-hostname servera.example.com
ssh-keygen -t ed25519 -f /home/alice/.ssh/id_ed25519
ssh-copy-id -i /home/alice/.ssh/id_ed25519.pub alice@serverb.example.com
```

按题目真实地址维护 serverb 的解析，并确保密钥文件由 alice 所有；不要把私钥复制到远端。

### ③ <span class="point-label">[操作点]</span> 开放正确 zone 的 HTTP

```bash
systemctl enable --now httpd
firewall-cmd --get-active-zones
firewall-cmd --zone=public --add-service=http
firewall-cmd --zone=public --add-service=http --permanent
```

若活动接口不在 public，应把命令中的 zone 换成真实归属，而不是把接口随意移动到 public。

### ④ <span class="point-label">[验证点]</span> 完成多层验收

```bash
nmcli con show exam-static
ip -br address show enp1s0; ip route
getent hosts servera.example.com serverb.example.com
sudo -u alice ssh serverb.example.com 'hostname; id'
systemctl is-active httpd; systemctl is-enabled httpd
ss -lntp | grep ':80'
firewall-cmd --zone=public --query-service=http
firewall-cmd --zone=public --query-service=http --permanent
```

最后从外部客户端执行 HTTP 请求。任何失败都停在对应层调查，不回滚已经正确的 profile 或密钥。

**[Cheatsheet]** 基线 → 静态 profile + `con up` → 地址/路由/DNS → 主机名/hosts → 密钥双端验证 → 服务监听 → 正确 zone runtime/permanent → 外部 HTTP。

</section>

<section class="topic closing" id="RHCSA-NETWORK-K02" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 连通性是多层证据的交集

持久 profile、内核当前网络、名称解析、服务监听、SSH 认证和 firewalld 各自回答不同问题。修改 connection 后必须激活并核对当前状态；修改防火墙时必须确认实际 zone，并分别检查 runtime 与 permanent。

排错先用数字 IP 验证路由，再进入名称解析；服务从监听、本机访问推进到过滤和外部访问；SSH 同时读取客户端详细输出和服务端日志。只要每一层都用对应工具证明，网络题就不会被一个 ping 或 active 状态过早结束。

</section>

