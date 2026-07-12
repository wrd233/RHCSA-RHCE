---
title: "RHCSA 第 13 章 系统日志、Journal、rsyslog 与日志轮转"
chapter_id: RHCSA-13
slug: journald-rsyslog-logrotate
exam: RHCSA
part: "第三篇 进程、服务与系统运行"
status: integrated
validation: static
live_test: not_performed
sources:
  - RH124-RHEL9-Ch11
  - RHEL9-Configuring-Basic-System-Settings-Ch6
  - journalctl(1)
  - systemd.journal-fields(7)
  - journald.conf(5)
  - logger(1)
  - rsyslog.conf(5)
  - logrotate(8)
---

<!-- 维护元数据、来源与静态验证状态只属于候选包维护层，正式发布渲染时可隐藏。 -->

# 第 13 章　系统日志、Journal、rsyslog 与日志轮转

系统日志不是一个名为 `/var/log/messages` 的单一文件，而是一条从“事件产生”到“证据保留”的处理链。内核、systemd unit、传统 syslog 客户端和应用程序产生事件；`systemd-journald` 收集这些事件并附加结构化字段；`rsyslog` 根据 facility、severity 或其他属性执行本地写入与远端转发；`logrotate` 再管理文本日志文件的轮转、压缩和保留。

排错时如果把这些对象混在一起，常见误判会连续发生：`rsyslog.service` 为 active，却没有任何消息写入目标文件；`journalctl -b -1` 没有结果，便认定上一次启动没有故障；日志文件完成了轮转，却发现应用仍在向旧归档文件写入；客户端已经建立 TCP 连接，便声称远端日志已经落盘。

本章围绕一条可验证的证据链展开：

```text
事件产生者
→ journald 收集、索引与存储
→ journalctl 按字段检索
→ rsyslog 选择与执行 action
→ 本地文件或远端接收
→ logrotate 控制文本日志生命周期
→ 容量、保留和跨重启证据
```

**[概念]** journal entry 是结构化事件记录。消息正文只是其中一个字段；启动轮次、进程、用户、unit、优先级和可执行文件等元数据使其能够被精确筛选。

**[概念]** syslog facility 表示消息类别，severity 表示严重级别。传统 rsyslog selector 使用两者选择消息，再把消息交给文件、远端主机或其他 action。

**[概念]** journal 文件与文本日志不是同一种存储对象。journal 有自己的轮转、容量与 vacuum 机制；`logrotate` 主要管理普通文本日志文件。

**[操作语义]** `journalctl` 用于检索 journal；`logger` 用于生成可控测试事件；`rsyslogd -N1` 用于静态检查 rsyslog 配置；`logrotate -d` 用于解释轮转决策。

---

<section class="topic knowledge" id="RHCSA-13-K01" data-kind="knowledge-topic">

## [知识专题] 从事件产生到可审计证据：RHEL 9 日志链

最顺的切入方式不是先背命令，而是先识别当前正在证明哪一层事实：事件有没有产生、journal 有没有收集、rsyslog 规则有没有命中、action 有没有完成、文本日志有没有被正确轮转，以及证据是否跨重启仍然存在。每一层都有自己的状态和验证入口。

### ① [知识点] journald 收集多种来源，并把事件转成结构化记录

`systemd-journald` 可以收集内核消息、启动早期输出、服务标准输出与标准错误、通过 syslog 接口发送的消息，以及其他 journal 传输来源。它维护带索引的 journal 文件，使管理员能够按字段而不是只靠全文搜索定位记录。

常见字段包括：

| 字段 | 回答的问题 | 证据边界 |
|---|---|---|
| `MESSAGE` | 事件正文是什么 | 正文可能由客户端控制 |
| `PRIORITY` | syslog 严重级别是什么 | 数字越小越严重 |
| `SYSLOG_FACILITY` | syslog 类别是什么 | 常以数字存储 |
| `SYSLOG_IDENTIFIER` | 客户端标识是什么 | 可由客户端提供 |
| `_PID` / `_UID` / `_GID` | 哪个进程和身份发送 | 下划线字段由 journal 侧补充 |
| `_COMM` / `_EXE` | 进程名和可执行文件是什么 | 适合确认来源身份 |
| `_SYSTEMD_UNIT` | 进程归属于哪个 system unit | 并非所有记录都有此字段 |
| `_BOOT_ID` | 记录属于哪次启动 | 跨 boot 检索的核心字段 |
| `_HOSTNAME` | 记录关联的主机名是什么 | 主机名变化需结合时间判断 |

同一条消息可能同时存在于 journal 和 `/var/log` 文本文件中；应用也可能绕过 syslog，直接写自己的日志文件。因此：

```text
journal 中没有目标记录
不等于
系统绝对没有任何相关日志
```

### ② [知识点] rsyslog 读取消息并根据规则执行 action

在典型 RHEL 9 系统中，journald 负责前端收集，rsyslog 继续处理 syslog 消息。rsyslog 规则可以把消息写入 `/var/log/messages`、`/var/log/secure` 或自定义文件，也可以转发给远端日志服务器。

rsyslog 规则的核心模型是：

```text
input
→ filter / selector
→ action
```

传统 selector 适合 RHCSA 基础任务：

```text
facility.priority    action
```

现代 RainerScript 可表达更复杂的条件、模板、队列和规则集。本章以传统 selector 建立考试主线，同时用现代 action 说明远端队列和生产边界，不要求穷尽 rsyslog 全部语言。

### ③ [知识点] 文本日志与 journal 有独立的生命周期

journal 文件由 journald 自己轮转，并可通过容量、可用空间和保留时间限制长期占用。`journalctl --vacuum-*` 清理的是归档 journal 文件。

普通文本日志则通常由 `logrotate` 管理。`logrotate` 读取策略和状态文件，判断某个文件是否满足按时间或大小轮转的条件，然后执行重命名、压缩、保留、删除、创建新文件及脚本钩子。

不能把两者混为一谈：

```text
journalctl --vacuum-size=...
```

不会轮转 `/var/log/exam-audit.log`；而：

```text
logrotate /etc/logrotate.conf
```

也不会管理二进制 journal 数据库。

### ④ [知识点] 当前可读、跨重启持久、仍被保留是三个状态

一个事件当前能被 `journalctl` 查询，只能证明它仍存在于当前可读 journal 中。是否跨重启保留，要看有效 `Storage=` 和持久目录；是否长期保留，还取决于容量、保留时间、磁盘压力和 vacuum 操作。

```text
当前可读
≠ 重启后仍存在
≠ 永久不会被清理
```

同理，目标文本文件存在，只能证明文件对象存在；它不能证明新规则命中过，也不能证明文件还在持续接收新消息。

### ⑤ [知识点] 时间戳是证据坐标，但时间同步属于相邻章节

日志检索和跨主机关联依赖系统时间、时区和时钟一致性。本章只建立必要接口：当时间范围查询与已知事件不一致时，应检查当前时间和时区；跨主机排序异常时，应检查时间同步状态。

RTC、chronyd、时间源选择、offset 和 step/slew 机制归第 14 章《系统时间、时区、RTC 与 chrony》完整展开。

**[Cheatsheet]** journald 负责收集和结构化；rsyslog 负责选择和 action；journal 与文本文件生命周期不同；当前可读不等于跨重启持久；日志时间异常时把时间系统作为独立假设。

</section>

<section class="topic operation" id="RHCSA-13-O01" data-kind="operation-topic">

## [操作专题] 按 boot、unit、时间和优先级收缩 journal

`journalctl` 的价值不在于无参数输出全部记录，而在于把宽泛症状收缩到一组明确事件。稳定方法是先使用一个高区分度维度，再逐步增加条件。过早叠加 boot、unit、PID、priority 和时间范围，容易把真正证据过滤为空。

### ① [操作] 先确认可查询的启动轮次

**作用对象：** 当前 journal 中仍可读取的 boot 集合。
**基本语义：** `--list-boots` 列出 boot 序号、boot ID 和时间范围；`-b` 或 `--boot=` 选择其中一次启动。
**基本形式：**

```bash
journalctl --list-boots
journalctl -b
journalctl -b -1
journalctl --boot=<BOOT_ID>
```

`-b` 表示当前启动，`-b -1` 表示上一次可用启动。若 `--list-boots` 只显示当前 boot，不能直接得出“上一次启动没有日志”；应继续检查持久化、保留和权限。

```bash
journalctl -b -1 -p err --no-pager
journalctl -k -b --since today --no-pager
```

`-k` 选择内核消息。它常与 `-b` 组合，避免把不同启动的内核事件混在一起。

### ② [操作] 按 unit、标识和字段选择来源

**作用对象：** 指定 unit、syslog identifier、PID、UID 或其他结构化字段。
**基本形式：**

```bash
journalctl -u <UNIT> -b --no-pager
journalctl -t <TAG> --since today --no-pager
journalctl _PID=<PID> -b --no-pager
journalctl _SYSTEMD_UNIT=<UNIT> _UID=<UID> --since today --no-pager
```

`-u` 是按 systemd unit 选择的便捷形式；`-t` 对应 `SYSLOG_IDENTIFIER`。直接写 `FIELD=value` 可以使用任意已知字段。

PID 可能复用。跨较长时间调查时，应把 PID 与 boot、unit、时间和可执行文件结合，而不是长期保存一个裸 PID 当作唯一身份。

可先枚举字段值：

```bash
journalctl -F _SYSTEMD_UNIT
journalctl -F SYSLOG_IDENTIFIER
```

同一字段提供多个值时通常形成 OR；不同字段之间形成 AND。显式 `+` 可以把两组匹配表达式连接为 OR。复杂条件应分步验证每一个子条件。

### ③ [操作] 使用时间窗口限制事件范围

**基本形式：**

```bash
journalctl --since today --no-pager
journalctl --since '-15 min' --no-pager
journalctl --since '2026-07-12 13:00:00' \
  --until '2026-07-12 13:20:00' --no-pager
```

时间参数可使用绝对时间和相对表达式。查询空结果时，先去掉最窄的时间条件，再检查当前时间、时区和 boot 范围，不要立即认定事件不存在。

`--utc` 只改变时间显示方式，不会修改记录本身：

```bash
journalctl -u <UNIT> --since '-10 min' --utc --no-pager
```

### ④ [操作] 按 priority 选择严重级别

syslog severity 从严重到调试为：

```text
emerg(0) → alert(1) → crit(2) → err(3)
→ warning(4) → notice(5) → info(6) → debug(7)
```

数字越小越严重。以下命令选择 `warning` 以及更严重的记录：

```bash
journalctl -p warning --no-pager
```

第一轮调查只看 `err` 可能漏掉根因之前的 warning、notice 或 info。通常先查看近期完整上下文，再用 `-p` 缩小。

### ⑤ [操作] 控制条数、方向、跟随和分页

```bash
journalctl -u <UNIT> -b -n 80 --no-pager
journalctl -u <UNIT> -b -r -n 30 --no-pager
journalctl -u <UNIT> -f
journalctl -u <UNIT> -n 1 -o verbose
```

- `-n`：限制最近条数；
- `-r`：最新记录在前；
- `-f`：跟随新记录，适合重现问题；
- `--no-pager`：便于复制、重定向和脚本处理。

跟随模式能证明后续新事件是否到达 journal，但不能替代对历史范围的调查。

**[Cheatsheet]** 先 `--list-boots`；再选 `-b`、`-u`、`-t` 或字段；随后加时间；最后才加 priority 和输出限制。空结果时按相反顺序放宽条件。

</section>

<section class="topic operation" id="RHCSA-13-O02" data-kind="operation-topic">

## [操作专题] 用结构化字段和输出格式解释一条记录

当短格式只能看到时间、主机、标识和消息时，`-o verbose` 可以暴露完整字段。字段调查的目标不是“把所有字段背下来”，而是识别哪些字段能够证明来源、身份、boot 归属和 unit 关系。

### ① [操作] 使用 `-o verbose` 发现字段

```bash
journalctl -u <UNIT> -n 1 -o verbose
journalctl -t <TAG> -n 1 -o verbose
```

重点观察：

```text
MESSAGE
PRIORITY
SYSLOG_FACILITY
SYSLOG_IDENTIFIER
_PID / _UID / _GID
_COMM / _EXE / _CMDLINE
_SYSTEMD_UNIT
_BOOT_ID
_SOURCE_REALTIME_TIMESTAMP
```

下划线开头的 trusted fields 通常由 journal 根据接收上下文补充，客户端不能简单伪造为同名可信字段；普通字段则可能由发送者直接提供。做审计判断时，应优先使用可信字段确认身份，再把消息正文作为业务线索。

### ② [操作] 根据阅读目的选择输出格式

| 输出格式 | 适合场景 | 边界 |
|---|---|---|
| 默认 short | 交互阅读 | 时间格式和字段较简化 |
| `short-iso` / `short-iso-precise` | 需要稳定、精确时间 | 仍不是机器结构化输出 |
| `verbose` | 发现全部字段 | 输出很长，不适合大范围 |
| `cat` | 只需要 `MESSAGE` | 丢失来源和时间上下文 |
| `json` / `json-pretty` | 机器处理与检查 | 下游必须正确解析 JSON |
| `export` | journal 原生导出场景 | 不适合作为普通文本阅读 |

示例：

```bash
journalctl -t <TAG> --since '-5 min' -o short-iso --no-pager
journalctl -t <TAG> --since '-5 min' -o cat --no-pager
journalctl -t <TAG> -n 1 -o json-pretty --no-pager
```

输出格式改变呈现，不改变底层记录，也不会让原本不存在的字段出现。

### ③ [操作] 组合字段时明确 AND 与 OR

```bash
# 同时满足 unit 和 UID
journalctl _SYSTEMD_UNIT=sshd.service _UID=0 --since today

# 同一字段的两个 unit 值，选择任一 unit
journalctl _SYSTEMD_UNIT=sshd.service \
  _SYSTEMD_UNIT=rsyslog.service --since today

# 两组表达式之间显式 OR
journalctl _SYSTEMD_UNIT=sshd.service _UID=0 + \
  _SYSTEMD_UNIT=rsyslog.service --since today
```

复杂表达式必须先分别运行每个分支。若最终结果为空，最有区分度的下一步不是改写更多条件，而是删除 OR/AND 组合，确认每个字段值是否真实存在。

### ④ [边界] journal 字段不能替代业务功能验证

`_SYSTEMD_UNIT=example.service` 能证明记录归属于该 unit 的上下文，但不能证明应用已经监听端口、正确响应请求或写入目标数据。日志是证据的一层，不是业务终态本身。

同样，某条错误记录没有出现，不等于故障已经修复。应在修改后触发一次可控业务动作，并检查新时间窗口内的日志与外部功能。

**[Cheatsheet]** 用 `verbose` 发现字段，用短格式阅读，用 JSON 做机器处理；可信字段优先确认身份；复杂匹配先拆开；日志归属不等于业务功能正确。

</section>

<section class="topic operation" id="RHCSA-13-O03" data-kind="operation-topic">

## [操作专题] 建立 persistent journal，并控制磁盘占用和保留

RHEL 9 常见默认状态是 `Storage=auto`，而系统未建立可用的 `/var/log/journal`，因此 journal 实际只位于 `/run/log/journal`，重启后丢失。持久化任务的目标不是机械创建目录，而是确认有效配置、存储位置、容量边界和跨 boot 证据。

### ① [操作] 建立变更前基线

```bash
journalctl --list-boots
journalctl --disk-usage
ls -ld /run/log/journal /var/log/journal 2>/dev/null

grep -R '^[[:space:]]*\(Storage\|SystemMaxUse\|RuntimeMaxUse\|MaxRetentionSec\)=' \
  /etc/systemd/journald.conf \
  /etc/systemd/journald.conf.d \
  /run/systemd/journald.conf.d \
  /usr/lib/systemd/journald.conf.d 2>/dev/null
```

在支持的系统上，可以使用：

```bash
systemd-analyze cat-config systemd/journald.conf
```

观察主配置与 drop-in 合并结果。管理员配置优先放在 `/etc/systemd/journald.conf.d/*.conf`，避免直接修改软件包提供的 vendor 文件。

### ② [知识点] `Storage=` 四种模式

| 值 | 主要含义 |
|---|---|
| `volatile` | 只写 `/run/log/journal`，重启后丢失 |
| `persistent` | 尝试写 `/var/log/journal`，不可用时可能退回运行时存储 |
| `auto` | 有可用持久目录时持久，否则使用运行时存储 |
| `none` | 丢弃所有需要存储的记录；转发行为另受配置控制 |

不能仅凭配置文件中的注释判断有效值，也不能把目录存在直接扩大为“跨重启已经验证”。

### ③ [操作] 使用 drop-in 明确持久化与容量边界

```ini
# /etc/systemd/journald.conf.d/60-persistent.conf
[Journal]
Storage=persistent
SystemMaxUse=512M
MaxRetentionSec=30day
```

这里的数字是经典任务中的明确要求，不是所有服务器的通用推荐值。生产系统应根据磁盘容量、审计要求、故障调查窗口和集中日志能力决定。

应用配置：

```bash
mkdir -p /etc/systemd/journald.conf.d
systemctl restart systemd-journald.service
journalctl --flush
```

`--flush` 请求把 `/run/log/journal` 中尚未转移的记录刷新到持久存储。它不能恢复已经因重启丢失的历史。

### ④ [知识点] 容量配置的对象不能混淆

- `SystemMaxUse=`：持久 journal 的最大使用量；
- `RuntimeMaxUse=`：运行时 journal 的最大使用量；
- `SystemKeepFree=` / `RuntimeKeepFree=`：希望给其他用途保留的空间；
- `MaxRetentionSec=`：按记录年龄限制保留；
- 单个文件大小和文件数量还受其他 journald 配置影响。

journald 会在容量和可用空间约束下轮转与删除旧归档。配置上限不是预分配，也不保证所有日志恰好保存指定天数。

### ⑤ [操作] 用唯一事件建立跨重启验证路径

```bash
TEST_ID="rhcsa13-persist-$(date +%s)"
logger -p local0.notice -t rhcsa13-persist "$TEST_ID"

journalctl -t rhcsa13-persist --since '-2 min' --no-pager
journalctl --disk-usage
journalctl --list-boots
```

当前阶段可验证事件已经进入 journal。严格的持久性验证要求在安全重启后执行：

```bash
journalctl --list-boots
journalctl -b -1 -t rhcsa13-persist --no-pager
```

本候选章没有 RHEL 9 live VM，因此只给出验证路径，不声称已完成真实重启测试。

### ⑥ [操作] 调查占用后再执行 vacuum

```bash
journalctl --disk-usage
journalctl --rotate
journalctl --vacuum-time=14days
journalctl --disk-usage
```

也可以按容量或归档文件数量清理：

```bash
journalctl --vacuum-size=500M
journalctl --vacuum-files=20
```

vacuum 会删除旧证据。执行前必须确认保留要求、调查窗口和集中存储状态。`--rotate` 先把当前活动文件变为归档，使 vacuum 的目标更明确，但仍不应作为无调查的日常“清理命令”。

**[Cheatsheet]** 基线看 boots、目录、有效配置和 disk usage；用 `/etc/...conf.d` 明确 `Storage=persistent`；重启 journald 后 `--flush`；唯一事件只能建立验证点，跨重启还要 `-b -1`；vacuum 之前确认审计边界。

</section>

<section class="topic operation" id="RHCSA-13-O04" data-kind="operation-topic">

## [操作专题] 用 `logger` 构造可重复的验证事件

等待业务“恰好产生日志”会让验证不可重复。`logger` 可以明确指定 facility、severity、tag 和唯一正文，使管理员能够在 journal、rsyslog 本地文件和远端服务器之间追踪同一事件。

### ① [操作] 使用 facility、severity 和 tag

```bash
TEST_ID="rhcsa13-route-$(date +%s)"
logger -p local0.notice -t exam-audit "$TEST_ID"
```

- `-p local0.notice`：指定 facility 和 severity；
- `-t exam-audit`：设置 `SYSLOG_IDENTIFIER`；
- 唯一正文：避免把历史旧消息误判为本次结果。

验证 journal：

```bash
journalctl -t exam-audit --since '-2 min' --no-pager
```

### ② [知识点] facility 与 severity 的职责不同

facility 是消息类别，例如：

```text
kern daemon authpriv cron mail user local0 ... local7
```

severity 是严重级别：

```text
emerg alert crit err warning notice info debug
```

`local0` 到 `local7` 适合为自定义脚本或应用建立专用路由，但使用前应检查现有配置，避免与其他系统或应用冲突。

### ③ [操作] 使用其他常用参数

```bash
logger -i -p local0.info -t exam-audit 'message with logger PID'
logger -s -p user.warning -t manual-check 'also print to stderr'
logger -f /path/to/input.txt -p local1.notice -t batch-test
```

- `-i`：在消息中加入 logger 的 PID 标识；
- `-s`：同时写标准错误，便于交互确认；
- `-f`：从文件读取并逐行发送。

`logger` 命令成功退出只能证明本地发送调用没有立即失败，不能单独证明 rsyslog 规则命中，更不能证明远端最终落盘。

### ④ [验证点] 同一事件必须跨层追踪

```text
唯一 TEST_ID
→ journalctl 按 tag/正文找到
→ 本地目标文件按 TEST_ID 找到
→ 远端接收端按 TEST_ID 找到
```

只有每一层都出现同一测试 ID，才形成端到端证据。不要使用通用正文如 `test`，因为历史记录和其他管理员测试可能产生同名内容。

**[Cheatsheet]** `logger -p` 定 facility/severity，`-t` 定标识，正文带唯一 ID；命令退出成功不等于规则命中；相同 TEST_ID 必须在目标层出现。

</section>

<section class="topic operation" id="RHCSA-13-O05" data-kind="operation-topic">

## [操作专题] 配置 rsyslog selector 与本地文件 action

本地路由任务通常要求“把指定 facility 的指定级别写入一个新文件”。稳定顺序是：检查现有规则、写最小配置、静态检查、应用配置、生成唯一事件、同时验证 journal 和目标文件。

### ① [知识点] 传统 selector 的阈值语义

```text
local0.notice     local0 的 notice 以及更严重消息
local0.=notice    仅 local0 的 notice
local0.!notice    排除 notice 以及更严重范围的相关语义，实际使用需谨慎核对
*.info            所有 facility 的 info 以及更严重消息
cron.none         在组合 selector 中排除 cron
```

最重要的考试边界是：普通 priority 名称表示“该级别及更严重”，不是“只等于该级别”。需要精确匹配时使用 `=`。

### ② [操作] 建立最小本地文件规则

```conf
# /etc/rsyslog.d/60-exam-audit.conf
local0.notice    /var/log/exam-audit.log
```

先检查整个配置集：

```bash
rsyslogd -N1
```

`-N1` 能证明配置可被解析，但不能证明目标目录可写、selector 会命中、远端可达或 action 成功。

应用配置：

```bash
systemctl restart rsyslog.service
systemctl is-active rsyslog.service
```

本章只轻量使用 systemd 状态接口；active/enabled 和 unit 生命周期归第 12 章。

### ③ [验证点] 用唯一事件证明规则命中

```bash
TEST_ID="rhcsa13-local-$(date +%s)"
logger -p local0.notice -t exam-audit "$TEST_ID"

journalctl -t exam-audit --since '-2 min' --no-pager
grep -F "$TEST_ID" /var/log/exam-audit.log
stat /var/log/exam-audit.log
```

分层判断：

| 证据 | 说明 |
|---|---|
| journal 有，文件无 | 事件产生和 journal 收集正常，继续查 rsyslog |
| journal 无，文件无 | 先查 `logger` 参数、时间范围和 journal |
| 文件有 | 该测试事件命中了某条写入该文件的规则 |
| 文件存在但无 TEST_ID | 不能证明本次变更成功 |

### ④ [知识点] 规则可能重复命中

rsyslog 通常继续处理后续规则，同一消息可能写入多个文件。若题目只要求增加自定义文件，重复进入默认日志不一定是错误；若明确要求排除后续处理，则要使用适合当前语法的 `stop` 逻辑，并静态检查其位置。

不要在不理解现有规则链时加入全局 stop，否则可能意外阻断安全、审计或远端转发。

### ⑤ [诊断] 语法正确但目标文件没有新消息

按区分度排序：

```text
1. journal 是否出现同一 TEST_ID
2. facility/severity 是否与 selector 相符
3. 规则文件是否位于被 include 的路径且后缀正确
4. rsyslog 是否读取了新配置
5. 目标目录、文件权限和 SELinux 是否允许写入
6. 后续规则或条件是否改变流程
```

非标准路径的 SELinux 文件类型归第 29 章完整展开；本章只要求把 AVC 或权限拒绝作为独立证据，不使用关闭 SELinux 作为修复。

**[Cheatsheet]** selector 是 facility + severity 阈值；配置放 `/etc/rsyslog.d/*.conf`；先 `rsyslogd -N1`；再 restart；用唯一 logger 消息；journal 有而文件无时进入 rsyslog 层。

</section>

<section class="topic operation" id="RHCSA-13-O06" data-kind="operation-topic">

## [操作专题] 配置远端转发，并按层证明消息到达

远端转发至少涉及发送端规则、名称解析、网络路径、协议、接收端监听、接收端规则和最终存储。客户端服务 active 或 TCP 连接成功，只能证明链路中的一小段。

### ① [知识点] 传统 UDP/TCP 语法

```conf
# UDP
local1.notice    @loghost.example.com:514

# TCP
local1.notice    @@loghost.example.com:514
```

单个 `@` 表示 UDP，双 `@@` 表示 TCP。UDP 无连接、开销低，但无法从传输层确认交付；TCP 提供连接和重传基础，但仍不能证明接收端规则已经把消息写入目标文件。

### ② [操作] 现代 forwarding action 与队列边界

生产环境更适合显式 action：

```conf
action(
    type="omfwd"
    protocol="tcp"
    target="loghost.example.com"
    port="514"
    queue.type="linkedList"
)
```

队列可以在远端暂时不可用时降低对本地日志处理的阻塞，并为重试提供缓冲。磁盘队列、TLS、证书和大规模集中日志策略属于工作扩展，不作为 RHCSA 最小答案冒充已经完成。

### ③ [操作] 发送端逐层检查

```bash
rsyslogd -N1
getent hosts loghost.example.com
systemctl is-active rsyslog.service
```

网络端口测试只能证明对应传输层状态，具体工具和防火墙规则归第 18、21 章：

```bash
# TCP 场景的示意检查，具体工具按环境选择
nc -vz loghost.example.com 514
```

随后生成唯一事件：

```bash
TEST_ID="rhcsa13-remote-$(date +%s)"
logger -p local1.notice -t remote-check "$TEST_ID"
journalctl -t remote-check --since '-2 min' --no-pager
```

### ④ [验证点] 最终证据必须在接收端

接收端应按同一 TEST_ID 验证：

```bash
journalctl -t remote-check --since '-5 min' --no-pager
grep -R -F "$TEST_ID" /var/log 2>/dev/null
```

具体验收取决于接收端规则。正确结论必须明确层次：

```text
客户端生成了消息
客户端 rsyslog 接受了配置
传输层可达
接收端进程监听
接收端收到消息
接收端目标文件出现消息
```

其中任意前一层都不能替代后一层。

### ⑤ [边界] 接收端与非标准端口

配置接收端通常要加载 `imudp` 或 `imtcp` 并建立 input；防火墙要放行正确协议；非标准端口还可能涉及 SELinux 端口类型。完整网络、防火墙和 SELinux 配置分别归第 18、21、29 章。本章只提供日志链中的接口和验收位置。

**[Cheatsheet]** `@` UDP，`@@` TCP；生产 TCP 建议显式 action 和队列；发送端 active 不等于远端落盘；最终用接收端同一 TEST_ID 验收。

</section>

<section class="topic operation" id="RHCSA-13-O07" data-kind="operation-topic">

## [操作专题] 用 logrotate 管理文本日志的状态、轮转与保留

logrotate 不是常驻写日志服务。它在被 timer 或其他调度入口调用时读取配置和状态文件，判断每个文件是否满足条件，再执行轮转。排错必须区分“配置被读取”“本次到期”“轮转完成”“写入进程已切到新文件”四个状态。

### ① [知识点] 配置来源与状态文件

主要配置入口：

```text
/etc/logrotate.conf
/etc/logrotate.d/*
```

全局配置通常 include `/etc/logrotate.d`。状态文件保存上次轮转时间，使 daily、weekly、monthly 等条件能够跨调用判断。RHEL 9 的具体默认状态路径应在 live 系统用包配置或命令输出确认；测试时可通过 `-s` 指定独立状态文件，避免污染系统状态。

### ② [知识点] 时间条件与大小条件

常见触发项：

- `daily`、`weekly`、`monthly`、`yearly`：按时间周期；
- `size 100M`：达到大小时轮转，通常独立于时间条件；
- `minsize 100M`：达到时间条件并且至少达到该大小；
- `maxsize 100M`：即使时间尚未到，也在超过该大小时轮转。

“文件已经很大”不必然表示本次应轮转。必须同时查看策略、上次状态和选项组合。

### ③ [知识点] 结果和保留选项

```conf
/var/log/exam-audit.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
```

- `rotate 7`：保留七个旧版本；
- `compress`：压缩旧版本；
- `delaycompress`：把最近一次归档的压缩推迟到下次轮转；
- `missingok`：文件不存在不报致命错误；
- `notifempty`：空文件不轮转；
- `create`：轮转后立即创建新活动文件，并设置模式和所有权。

`create` 的权限必须根据实际写入进程确定。不能机械使用 `root root` 或宽松权限。

### ④ [操作] 使用 debug 解释决策

检查整个配置集：

```bash
logrotate -d /etc/logrotate.conf
```

`-d` 输出调试信息而不实际修改日志和状态。关注：

```text
配置是否命中目标文件
读取了哪个状态
上次何时轮转
本次为什么需要或不需要轮转
将执行哪些 rename/create/compress/script 动作
```

`-v` 提供详细运行信息，但若不加 `-d` 可能执行真实操作。

### ⑤ [操作] 在专用测试对象上隔离强制轮转

`-f` 会真实轮转。只在已确认的测试对象上使用，并用独立状态文件降低对系统状态的影响：

```bash
logrotate -s /tmp/rhcsa13-logrotate.status \
  -f /etc/logrotate.d/exam-audit
```

调用单个 snippet 时，全局配置中的默认选项可能不会参与。测试前应确认该 snippet 自包含，或准备一份专用测试配置。

轮转后检查：

```bash
ls -l /var/log/exam-audit.log*
stat /var/log/exam-audit.log
```

### ⑥ [知识点] rename/create 后写入者必须重新打开文件

典型轮转会把活动文件重命名，然后创建一个同名新文件。已打开旧文件描述符的进程可能继续写入旧 inode。此时目录中虽然出现新文件，应用却仍向归档文件写入。

首选方法是让写入进程执行文档支持的 reopen 或 reload。对于由 rsyslog 写入的文件，应参考系统已安装的 rsyslog logrotate 策略，使用一致的 HUP/reload 方式，而不是随意重启所有业务。

`copytruncate` 在原文件上复制后截断，适合无法重新打开日志的程序，但复制与截断之间存在丢失少量日志的窗口，应作为有风险的兼容方案，而不是默认答案。

### ⑦ [验证点] 轮转后必须再发送一条新消息

```bash
TEST_ID="rhcsa13-after-rotate-$(date +%s)"
logger -p local0.notice -t exam-audit "$TEST_ID"
grep -F "$TEST_ID" /var/log/exam-audit.log
```

这一步证明写入者已经切换到新的活动文件。仅看到 `.1` 或 `.gz` 文件不能证明后续写入正确。

### ⑧ [操作] 检查调度入口

RHEL 9 通常由 systemd timer 周期调用 logrotate。可检查：

```bash
systemctl status logrotate.timer
systemctl list-timers logrotate.timer
journalctl -u logrotate.service --since today --no-pager
```

timer 的完整状态模型和日历表达式归第 15 章。本章只确认 logrotate 是否被实际调用，以及其服务日志是否报告错误。

**[Cheatsheet]** 配置决定策略，state 决定上次时间，调用入口决定何时检查；`-d` 只解释，`-f` 真轮转；rename/create 后必须让写入者 reopen；最后用新 TEST_ID 验证新活动文件。

</section>

<section class="topic diagnosis" id="RHCSA-13-D01" data-kind="diagnosis-topic">

## [诊断专题] 日志查不到、写不到、转不到和轮不动

诊断不从“重启所有服务”开始，而从症状和当前证据开始。每一步选择最能区分两个假设的下一条证据，再做最小修复。

### ① [诊断] `journalctl -b -1` 没有结果

```text
症状：只能看到当前 boot。
当前证据：--list-boots 是否只列一条？
假设 A：journal 实际为 volatile。
假设 B：曾经持久，但旧 boot 已被容量/时间策略清理。
假设 C：当前用户没有读取所需记录的权限。
```

下一条证据：

```bash
journalctl --list-boots
journalctl --disk-usage
ls -ld /run/log/journal /var/log/journal 2>/dev/null
systemd-analyze cat-config systemd/journald.conf
```

最小修复是明确持久化与容量边界。不能声称修改后能恢复此前已经丢失的 boot。

### ② [诊断] 时间范围内查不到已知事件

```text
症状：业务确认在某时刻失败，但 --since/--until 为空。
```

调查链：

```bash
journalctl -b -n 100 --no-pager
journalctl -t <TAG> --since today --no-pager
journalctl --list-boots
date
timedatectl
```

先放宽时间，再确认 tag/unit/boot，最后把时区和系统时间作为独立假设。不要在查询为空时直接改 chrony 配置；时间同步完整诊断归第 14 章。

### ③ [诊断] journal 有 TEST_ID，但自定义文件没有

```text
已证明：事件产生并进入 journal。
尚未证明：rsyslog selector 命中和 file action 成功。
```

下一条证据：

```bash
rsyslogd -N1
grep -R -n 'exam-audit\|local0' /etc/rsyslog.conf /etc/rsyslog.d
systemctl status rsyslog.service --no-pager
journalctl -u rsyslog.service --since '-10 min' --no-pager
ls -ld /var/log
ls -l /var/log/exam-audit.log 2>/dev/null
```

检查 facility、severity 阈值、include 路径、配置顺序、权限和 SELinux。最小修复后重新生成新的 TEST_ID，不能用旧事件证明新规则。

### ④ [诊断] rsyslog 配置检查失败

`rsyslogd -N1` 报错时，先定位文件和行号，备份后做最小语法修复。不要把整个 `/etc/rsyslog.d` 清空，也不要删除自己暂时看不懂的 vendor 配置。

```bash
rsyslogd -N1
nl -ba /etc/rsyslog.d/<FILE>.conf
```

修复后再次运行 `-N1`，再应用配置。服务 restart 成功不能替代静态检查记录。

### ⑤ [诊断] 客户端看似发送，远端没有记录

从发送到接收分层：

```text
唯一事件是否在客户端 journal
→ 客户端规则是否命中
→ 名称解析是否正确
→ 协议和端口是否一致
→ 网络和防火墙是否允许
→ 服务端是否监听
→ 服务端 input 是否绑定正确 ruleset
→ 服务端 action 是否落盘
```

TCP 可连接只排除部分网络问题；UDP 发送成功几乎不提供交付确认。最终仍需接收端同一 TEST_ID。

### ⑥ [诊断] logrotate 显示“不需要轮转”

下一条证据：

```bash
logrotate -d /etc/logrotate.conf
```

重点检查：

- 是否匹配目标路径；
- time/size/minsize/maxsize 组合；
- state 中的上次轮转时间；
- 文件是否为空且设置 `notifempty`；
- 文件是否不存在且设置 `missingok`；
- 调度入口是否按预期调用。

不要因为文件大就直接 `-f`。先解释“不需要轮转”的决策。

### ⑦ [诊断] 已生成归档，但新活动文件不增长

```text
症状：.1 或日期归档存在，新同名文件存在，但新消息进入旧归档。
假设：写入进程仍持有旧 inode。
```

下一条证据可包括进程打开文件描述符和轮转脚本，但具体工具需按环境选择。最小修复是使用写入进程支持的 reopen/reload，再发送新 TEST_ID 验证新文件。

### ⑧ [诊断] journal 磁盘占用过高

```text
症状：journal 占用增加或文件系统空间紧张。
```

稳定顺序：

```text
确认真实占用
→ 确认增长速度和异常来源
→ 确认审计/保留要求
→ 检查持久与运行时配置
→ 必要时 rotate + vacuum
→ 再观察占用和新日志流
```

不得把删除全部 journal、关闭持久化或停止 journald 作为默认解决方案。

**[Cheatsheet]** 空结果先放宽过滤；journal 有而文件无查 rsyslog；远端问题按发送、网络、接收、落盘分层；logrotate 不动作先读 debug 和 state；轮转后不写新文件查 reopen。

</section>

<section class="topic classic" id="RHCSA-13-C01" data-kind="classic-task">

<div class="page-break"></div>

## [经典任务] 为指定 facility 建立本地日志路由和轮转

### 任务环境

系统已有 `/etc/rsyslog.conf` 和多个 `/etc/rsyslog.d/*.conf` 文件。不得删除、覆盖或停用其他规则。应用脚本通过以下形式发送审计事件：

```bash
logger -p local0.notice -t exam-audit '<MESSAGE>'
```

当前 `/var/log/exam-audit.log` 尚未稳定接收消息，也没有专用 logrotate 策略。

### 目标终态

1. `local0` facility 的 `notice` 以及更严重消息写入 `/var/log/exam-audit.log`；
2. 规则放在 `/etc/rsyslog.d/60-exam-audit.conf`；
3. 文本日志每天轮转，保留 7 份，压缩旧日志；
4. 空文件不轮转，文件缺失不导致任务失败；
5. 新活动文件模式为 `0640`，所有者和组为 `root:root`；
6. 轮转后 rsyslog 能继续向新的活动文件写入。

### 限制条件

- 不清空现有日志；
- 不使用 `chmod 777`；
- 不关闭 SELinux；
- 不在未知生产日志上无调查运行全局 `logrotate -f`；
- 不能以 `rsyslog.service` active 作为最终验收。

### 验收证据

```text
rsyslogd -N1 通过
→ 唯一 TEST_ID 出现在 journal
→ 同一 TEST_ID 出现在目标文件
→ 目标文件权限正确
→ logrotate debug 能解释策略
→ 专用测试状态下完成轮转
→ 轮转后新 TEST_ID 进入新的活动文件
```

</section>

<section class="topic classic" id="RHCSA-13-C02" data-kind="classic-task">

<div class="page-break"></div>

## [经典任务] 调查只能看到当前 boot、看不到上一次启动日志

### 任务环境

服务器刚完成一次计划外重启。当前执行：

```bash
journalctl --list-boots
journalctl -b -1
```

只能读取当前 boot。不得再次重启服务器，直到业务窗口批准。

### 目标终态

1. 区分以下可能：从未启用持久 journal、旧记录已被保留策略清理、读取权限不足；
2. 在 `/etc/systemd/journald.conf.d/60-persistent.conf` 中明确持久存储；
3. 限制持久 journal 最大使用量为 `512M`，最长保留 `30day`；
4. 建立一个唯一验证事件；
5. 给出当前可完成的验证和下一次安全重启后的跨 boot 验证；
6. 明确此前已丢失的历史不能通过新配置恢复。

### 限制条件

- 不删除 `/var/log/journal`；
- 不执行 vacuum 破坏当前证据；
- 不声称已经完成跨重启 live test；
- 时间同步问题只记录接口，留给第 14 章。

</section>

<section class="topic answer" id="RHCSA-13-A01" data-kind="answer-topic">

<div class="page-break"></div>

## [参考解答] 任务一：本地路由、轮转与写入者重新打开

### ① 建立基线并检查冲突

```bash
grep -R -n 'local0\|exam-audit' /etc/rsyslog.conf /etc/rsyslog.d 2>/dev/null
rsyslogd -N1
ls -l /var/log/exam-audit.log* 2>/dev/null
```

若已有 local0 规则，先判断是否允许同一消息进入多个目标。不要直接删除现有规则。

### ② 写入最小 rsyslog 配置

```conf
# /etc/rsyslog.d/60-exam-audit.conf
local0.notice    /var/log/exam-audit.log
```

静态检查并应用：

```bash
rsyslogd -N1
systemctl restart rsyslog.service
systemctl is-active rsyslog.service
```

### ③ 用唯一事件验证路由

```bash
TEST_ID="rhcsa13-local-$(date +%s)"
logger -p local0.notice -t exam-audit "$TEST_ID"

journalctl -t exam-audit --since '-2 min' --no-pager
grep -F "$TEST_ID" /var/log/exam-audit.log
stat -c '%U %G %a %n' /var/log/exam-audit.log
```

若 journal 有而文件无，继续查 selector、配置加载和文件写入层；不要重复发送相同正文。

### ④ 写入 logrotate 策略

```conf
# /etc/logrotate.d/exam-audit
/var/log/exam-audit.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0640 root root
    postrotate
        /usr/bin/systemctl kill -s HUP --kill-whom=main rsyslog.service >/dev/null 2>&1 || true
    endscript
}
```

这里用 HUP 请求 rsyslog 重新打开文件。集成到真实 RHEL 9 主机前，应与系统自带 `/etc/logrotate.d/rsyslog` 的 reopen 方式核对。

### ⑤ 静态解释轮转决策

```bash
logrotate -d /etc/logrotate.conf
```

确认目标文件被匹配、策略被读取，并解释本次是否到期。debug 模式不执行实际轮转。

### ⑥ 在专用状态下测试真实轮转

该步骤会改变目标测试文件，仅在已确认的任务环境执行：

```bash
logrotate -s /tmp/rhcsa13-exam-audit.status \
  -f /etc/logrotate.d/exam-audit

ls -l /var/log/exam-audit.log*
stat -c '%U %G %a %n' /var/log/exam-audit.log
```

### ⑦ 验证轮转后的新写入

```bash
POST_ID="rhcsa13-postrotate-$(date +%s)"
logger -p local0.notice -t exam-audit "$POST_ID"
grep -F "$POST_ID" /var/log/exam-audit.log
```

只有新 TEST_ID 进入新活动文件，才证明写入者已切换。归档文件存在不是充分证据。

### 典型错误

- 写成 `local0.=notice`，导致更严重消息不进入；
- 未运行 `rsyslogd -N1` 就 restart；
- 使用旧消息证明新规则；
- 对整个 `/etc/logrotate.conf` 直接 `-f`；
- 轮转后只检查 `.1`，不检查新消息；
- 用 `copytruncate` 掩盖不会 reopen 的问题，却忽略潜在日志丢失窗口。

</section>

<section class="topic answer" id="RHCSA-13-A02" data-kind="answer-topic">

<div class="page-break"></div>

## [参考解答] 任务二：持久 journal 与跨 boot 验证计划

### ① 调查当前状态

```bash
journalctl --list-boots
journalctl --disk-usage
ls -ld /run/log/journal /var/log/journal 2>/dev/null
systemd-analyze cat-config systemd/journald.conf
```

若 `systemd-analyze cat-config` 在目标版本不可用，则直接读取主配置和各级 drop-in。当前只列一条 boot，可能是从未持久、旧记录已清理或权限不足，不能仅凭一条命令决定。

### ② 建立配置基线

```bash
mkdir -p /etc/systemd/journald.conf.d
cp -a /etc/systemd/journald.conf.d/60-persistent.conf \
  /etc/systemd/journald.conf.d/60-persistent.conf.bak 2>/dev/null || true
```

备份存在的管理员文件，不修改 `/usr/lib` vendor 配置。

### ③ 写入明确持久化策略

```ini
# /etc/systemd/journald.conf.d/60-persistent.conf
[Journal]
Storage=persistent
SystemMaxUse=512M
MaxRetentionSec=30day
```

应用：

```bash
systemctl restart systemd-journald.service
journalctl --flush
journalctl --disk-usage
```

### ④ 建立当前验证事件

```bash
TEST_ID="rhcsa13-persist-$(date +%s)"
logger -p local0.notice -t rhcsa13-persist "$TEST_ID"

journalctl -t rhcsa13-persist --since '-2 min' --no-pager
journalctl --list-boots
```

当前可以证明：新配置已被应用到运行中的 journald 流程、唯一事件当前可读、磁盘占用可观察。仍不能证明它已跨重启保留。

### ⑤ 记录下一次安全重启后的验收

业务窗口重启后执行：

```bash
journalctl --list-boots
journalctl -b -1 -t rhcsa13-persist --no-pager
```

预期证据是：boot 列表包含上一次启动，且 `-b -1` 中能够找到重启前记录的 TEST_ID。

### ⑥ 明确不可恢复边界

若旧记录此前只存于 `/run/log/journal` 并已随重启消失，或已被容量/vacuum 清理，新配置无法恢复它们。正确结论应写为“已为后续启动建立持久化”，而不是“恢复了上次启动日志”。

### 典型错误

- 只创建 `/var/log/journal`，未检查有效 `Storage=`；
- 修改配置后未让 journald 读取；
- 看到当前事件就声称跨重启成功；
- 为腾空间在调查期间执行 vacuum；
- 把时间查询异常直接归咎于 chrony，而未先放宽 journal 过滤。

</section>

<section class="topic wrap" id="RHCSA-13-S01" data-kind="chapter-wrap">

## [本章收束] 从“看到日志”迁移到“维护证据链”

本章的核心不是记住更多日志路径，而是让每条结论都落在明确对象上：

```text
journalctl 证明 journal 中当前可读的记录
logger 生成受控测试事件
rsyslogd -N1 证明配置可解析
目标文件中的 TEST_ID 证明 file action 命中
接收端 TEST_ID 证明远端到达
logrotate -d 解释轮转决策
轮转后的新 TEST_ID 证明写入者切到新文件
-b -1 的 TEST_ID 证明跨重启持久
```

最终验收应形成证据矩阵，而不是一条“命令执行成功”。真实工作中还要把日志保留与磁盘预算、审计要求、集中存储、权限和时间同步结合；这些扩展都应建立在本章对象与状态模型上。

**最终 Cheatsheet**

```text
查询：--list-boots / -b / -u / -t / --since / --until / -p
字段：-o verbose / FIELD=value / -F FIELD
持久：Storage=persistent / --flush / --disk-usage
测试：logger -p facility.level -t TAG UNIQUE_ID
rsyslog：selector action / rsyslogd -N1 / 目标层 TEST_ID
远端：@ UDP / @@ TCP / 接收端最终验收
轮转：配置 + state + 调度入口 / -d 解释 / -f 真操作
闭环：修改后生成新事件，不能复用旧证据
```

</section>
