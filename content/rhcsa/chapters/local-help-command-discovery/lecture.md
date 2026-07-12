---
title: "RHCSA 第 03 章 本地帮助、命令发现与软件能力查询"
chapter_id: RHCSA-03
exam: RHCSA
part: "第一篇 命令行与本地信息处理"
slug: local-help-command-discovery
status: content_frozen_for_integration
validation: static
live_test: not_performed
base_commit: "961a29b3af4c07a828078a5de90c221a036546df"
sources:
  - RH124-RHEL9-Ch4
  - RH124-RHEL9-Ch14-query-scope
  - RHEL9-RHCSA-02-运行命令和获取帮助
  - RHEL9-RHCSA-17-软件包的管理
  - bash(1)
  - man(1)
  - apropos(1)
  - whatis(1)
  - info(1)
  - whereis(1)
  - rpm(8)
  - dnf(8)
---

<div class="cover-page">
<div class="cover-kicker">RHEL 9 · RHCSA 实操讲义</div>
<div class="cover-number">03</div>
<h1>本地帮助、命令发现与<br>软件能力查询</h1>
<p class="cover-subtitle">从一个陌生名称开始，沿着当前 Shell、帮助索引、RPM 数据库与 DNF 元数据建立可复核的本机证据链。</p>
<div class="cover-tags">
<span>对象模型</span><span>操作语义</span><span>证据边界</span><span>诊断</span><span>经典任务</span>
</div>
<div class="cover-note">大字号阅读版</div>
</div>

<div class="nav-page">

# 本章阅读导航

先抓住一条主线：**先确认当前系统把名称解释成什么，再决定去哪里查语法；已有路径查询本地所有权，缺失路径查询仓库提供能力。**

<div class="model-grid">
<div class="model-step"><b>01</b><strong>确认问题层</strong><span>名称、对象、位置、所有权还是提供能力</span></div>
<div class="model-step"><b>02</b><strong>确认当前对象</strong><span>alias、function、builtin 或外部命令</span></div>
<div class="model-step"><b>03</b><strong>选择帮助源</strong><span>help、--help、man 或 info</span></div>
<div class="model-step"><b>04</b><strong>发现未知能力</strong><span>whatis、apropos 与 man 索引</span></div>
<div class="model-step"><b>05</b><strong>定位软件来源</strong><span>rpm -qf 与 dnf provides</span></div>
<div class="model-step"><b>06</b><strong>限制证据结论</strong><span>说明能证明什么、不能证明什么</span></div>
</div>

<div class="nav-columns">
<div class="nav-col nav-left">

## 专题地图

- **知识专题**　名称、对象、位置和软件来源为何必须分层
- **操作专题**　让当前 Bash 说明一个名称会怎样解析
- **操作专题**　按对象选择 `help`、`--help`、`man` 与 `info`
- **操作专题**　从 man section 和标准标题提取操作依据
- **操作专题**　不知道命令名时按关键字发现本地能力
- **操作专题**　用 `rpm -qf` 证明已安装文件归属
- **操作专题**　用 `dnf provides` 查询缺失路径的候选提供者
- **诊断专题**　让互相矛盾的查询结果回到各自证据层
- **经典任务**　无互联网、禁止安装时完成一份本地调查记录

</div>
<div class="nav-col nav-right">

## 阅读时持续回答

1. 我现在调查的是名称、文件还是软件包能力？
2. 当前 Bash 会优先执行哪个对象？
3. 这个对象的第一帮助入口是什么？
4. 打开的 man page 属于哪个 section？
5. 查询结果来自当前会话、本机数据库还是仓库元数据？
6. 空结果意味着对象不存在，还是帮助/索引/仓库不可见？
7. 这条证据能证明到哪一层？
8. 下一条最有区分度的证据是什么？

<div class="boundary-note"><b>章节边界：</b>RPM 安装、升级、删除和验证事务留给第 16 章；DNF 仓库、模块流和包组留给第 17 章；互联网搜索不作为第一证据。</div>

</div>
</div>
</div>

<div class="main-start"></div>

# 第 03 章 · 正文

面对陌生命令，最常见的误判不是“少记了一个参数”，而是还没有确认调查对象，就直接复制一个看似相关的答案。相同名称在当前 Bash 中可能是 alias、function、builtin，也可能是磁盘中的外部程序；一个路径可以由本机已安装 RPM 包拥有，也可以只是管理员手工创建；仓库中某个软件包能够提供一个文件，也不代表它已经安装，更不代表当前 Shell 已经能够调用它。

本章以“**名称解析 → 帮助路由 → 能力发现 → 软件来源 → 证据边界**”为主线。它不把十几个查询工具堆成命令清单，而是训练你从当前证据决定下一条查询：先用 Bash 自己确认名称如何解析，再为该对象选择合适的本地帮助；不知道准确名称时，从 man 索引按功能查找；已经存在的路径交给 RPM 数据库；缺失命令或路径交给 DNF 可见的软件包元数据。每一步都必须说明结论的观察范围。

后续第 04 章会完整解释路径、文件类型和链接；本章只把“路径”当作查询键。第 16、17 章会处理软件事务和仓库配置；本章只做只读调查，不通过安装或改仓库来制造答案。

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>Shell 名称解析</strong> 是当前 Bash 把命令位置上的名称映射为可执行对象的过程。解析结果受 alias、function、builtin、`PATH`、命令哈希缓存和当前会话状态影响，因此“系统里有这个文件”与“当前 Shell 会执行这个文件”不是同一个结论。观察入口是 `type` 与 `command -V/-v`。</p>
</div>

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>命令类型</strong> 描述名称最终指向的对象类别：alias 是解析阶段的文本替换，function 是当前 Shell 中保存的命令体，builtin 由 Bash 进程内部实现，外部命令则对应文件系统中的程序或脚本。同名对象可以并存，优先级和帮助入口也不同。</p>
</div>

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>当前环境证据</strong> 是“在这个用户、这个 Bash 会话、这个 `PATH` 与这些启动配置下”的观察结果。更换用户、非交互 Shell、登录方式或环境变量后，`type`、`command -v` 甚至可用帮助文档都可能变化。结论必须连同作用范围记录，不能写成永远不变的系统事实。</p>
</div>

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>帮助入口层次</strong> 反映文档由谁维护以及信息深度。Bash builtin 优先查 `help`；外部程序常用 `--help` 快速确认形式；完整本地参考进入 `man`；部分 GNU 工具有节点式 `info` 文档。入口之间是分工关系，不是“哪个命令更高级”。</p>
</div>

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>man section 与关键字索引</strong> 解决两个不同问题。section 用来区分同名但对象不同的页面，例如命令 `passwd(1)` 与文件格式 `passwd(5)`；`whatis` 和 `apropos` 使用手册索引，在已知名称或只知道功能时发现页面。索引空结果不自动等于系统没有该能力。</p>
</div>

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>已安装文件归属</strong> 是本机 RPM 数据库记录的路径与已安装包之间的关系。`rpm -qf /path` 证明的是“这台主机的 RPM 数据库认为谁拥有该路径”，不是仓库中唯一的提供者，也不自动证明文件内容没有被修改。</p>
</div>

<div class="concept-block">
<span class="concept-label">概念</span>
<p><strong>仓库能力查询</strong> 是从 DNF 当前可见的软件包集合中查找能够提供某个路径或 capability 的候选。`dnf provides` 的结果受启用仓库、架构和元数据状态影响；它只能建立候选提供关系，不能替代安装状态、Shell 解析和最终功能验证。</p>
</div>

<section class="quick-reference">

## 操作语义速查

<div class="quick-intro"><span>操作语义</span>先建立关键入口地图。下面每组只给出最常用形式；完整判断、输出和诊断在后续专题展开。</div>

<div class="command-card">

### `type` / `command`

**SYNOPSIS**

```bash
type [-afptP] name [name ...]
command [-pVv] command [argument ...]
```

从当前 Bash 的解析环境确认一个名称是 alias、function、builtin 还是外部命令。

**重要参数 / 形式**

`type name`
: 显示当前优先解析结果。

`type -a name`
: 尽可能列出当前环境可见的所有同名入口。

`command -V name`
: 输出适合人工阅读的详细解析说明。

`command -v name`
: 输出简洁表示并提供可用于脚本判断的退出状态；结果不一定是路径。

</div>

<div class="command-card">

### `help` / `COMMAND --help`

**SYNOPSIS**

```bash
help [-dms] [pattern ...]
COMMAND --help
```

`help` 查询当前 Bash 版本的 builtin 和语法主题；`--help` 是外部程序常见的快速帮助约定。

**重要参数 / 形式**

`help builtin`
: 显示 builtin 的完整 Bash 帮助。

`help -s builtin`
: 只看简短使用形式。

`COMMAND --help`
: 快速确认 Usage、常用选项和参数形式；并非所有程序都实现完全相同的接口。

</div>

<div class="command-card">

### `man` / `whatis` / `apropos`

**SYNOPSIS**

```bash
man [section] page
whatis name ...
apropos keyword ...
```

`man` 阅读本地手册页；`whatis` 查已知名称的一行描述；`apropos` 按名称与描述中的关键字发现页面。

**重要参数 / 形式**

`man 5 passwd`
: 显式选择 section 5，读取文件格式而不是命令页。

`man -f name`
: 与 `whatis name` 对应。

`man -k keyword`
: 与 `apropos keyword` 对应。

</div>

<div class="command-card">

### `info`

**SYNOPSIS**

```bash
info [option ...] [menu-item ...]
```

阅读以节点和菜单组织的 GNU 长文档，适合跨主题说明和教程式材料。

**重要参数 / 形式**

`info topic`
: 打开指定主题或菜单项。

`n` / `p` / `u`
: 前往下一节点、上一节点或上一级。

`q`
: 退出。最小安装不保证每个工具都有 Info 文档。

</div>

<div class="command-card">

### `whereis`

**SYNOPSIS**

```bash
whereis [options] name ...
```

在已知的标准位置中查找二进制、源代码和手册线索；它不模拟当前 Bash 的完整名称解析。

**重要参数 / 形式**

`whereis name`
: 同时显示可见的二进制、源码和手册位置线索。

`-b`
: 只查二进制。

`-m`
: 只查手册。

</div>

<div class="command-card">

### `rpm -qf`

**SYNOPSIS**

```bash
rpm -qf FILE [FILE ...]
```

查询本机 RPM 数据库，确定已有路径由哪个已安装软件包拥有。

**重要参数 / 形式**

`-q`
: 进入查询模式。

`-f FILE`
: 以文件路径选择拥有它的已安装包。

`rpm -ql PACKAGE`
: 反向列出某个已安装包记录的文件清单；软件验证事务留给第 16 章。

</div>

<div class="command-card">

### `dnf provides`

**SYNOPSIS**

```bash
dnf provides PROVIDE-SPEC [PROVIDE-SPEC ...]
```

从 DNF 当前可见的软件包数据中查询能够提供某个路径或 capability 的候选。

**重要参数 / 形式**

`dnf provides /usr/sbin/name`
: 已知准确路径时进行精确查询。

`dnf provides '*/name'`
: 只知道 basename 时查询路径尾部；引号防止当前 Shell 提前展开 `*`。

结果来源
: 记录候选包、架构、仓库/安装来源与匹配路径；命中不等于已经安装。

</div>

</section>

<section class="topic knowledge" id="RHCSA-03-K01">

## <span class="topic-label">知识专题</span> 名称、对象、位置和软件来源为何必须分层

一个命令名背后至少存在四个问题：当前 Shell 会执行什么、磁盘上有哪些候选位置、本机哪个包拥有目标路径、仓库中哪个包能够提供目标。四个问题分别由不同数据源回答。真正稳定的调查不是追求所有命令输出一致，而是让每条结果回到自己的证据层。

### ① <span class="point-label">知识点</span> 当前 Shell 可调用对象不只有外部文件

| 对象 | 本质 | 常见作用范围 | 身份入口 | 第一帮助入口 |
|---|---|---|---|---|
| alias | 解析阶段的名称替换 | 当前 Shell，常来自启动文件 | `type` | 先看展开，再查真实命令 |
| function | Shell 中保存的命令体 | 当前 Shell 或导出的函数环境 | `type`、`declare -f` | 读函数定义，再查内部对象 |
| builtin | Bash 进程内部实现 | 当前 Bash | `type`、`command -V` | `help` |
| 外部命令 | 文件系统中的程序或脚本 | `PATH`、权限和文件状态共同决定 | `type`、`command -v` | `--help`、`man`、`info` |

同名对象可以并存。`test` 可能既是 builtin，也有 `/usr/bin/test`；alias 可能给外部命令预置参数；function 可能完全覆盖同名文件。只知道文件路径，仍不能直接推断当前命令位置会调用它。

### ② <span class="point-label">知识点</span> 四层证据可以不同，而且这种不同通常是正常的

```text
当前 Bash 会执行什么
→ type / command -V / command -v

标准位置中有哪些相关二进制或手册线索
→ whereis；which 只作外部路径线索

本机某个路径由哪个已安装包拥有
→ rpm -qf /absolute/path

DNF 当前可见的软件包中谁能提供该路径
→ dnf provides /path 或 '*/basename'
```

例如，`type` 可以显示 alias，`whereis` 同时显示 `/usr/bin/name` 与手册路径，`rpm -qf` 证明 `/usr/bin/name` 属于已安装包，`dnf provides` 又列出多个不同架构或仓库版本。它们回答的问题不同，不能选一条覆盖全部事实。

### ③ <span class="point-label">知识点</span> 证据有会话、主机和元数据边界

`type` 与 `command` 是当前 Bash 会话证据。切换用户、改变 `PATH`、进入非交互 Shell 或载入不同启动文件后，解析结果可能变化。Bash 还可能缓存外部命令路径；文件移动或软件更新后，必要时用 `hash -r` 清理当前会话缓存再复查。

`rpm -qf` 依赖本机 RPM 数据库；`dnf provides` 依赖 DNF 当前能看到的软件包集合。仓库启停、订阅、架构和元数据更新时间都会影响候选。调查记录应保留“在哪台主机、哪个用户、哪个会话、哪个仓库范围”这些上下文。

### ④ <span class="point-label">边界</span> 帮助文本是操作依据，不是目标状态证明

在 man page 中找到参数，只能证明写法有本地依据；`command -v` 成功只能证明当前 Shell 能解析名称；`dnf provides` 命中只能证明存在候选提供关系。它们都不能替代后续业务对象上的当前状态、持久状态和功能验收。

<div class="cheatsheet"><b>判断口诀：</b>名称先问 Bash；位置只作线索；已有路径问 RPM；缺失路径问 DNF；每条结论都写明观察范围。</div>

</section>

<section class="topic operation" id="RHCSA-03-O01">

## <span class="topic-label">操作专题</span> 让当前 Bash 说明一个名称会怎样解析

当现象是“这个名称执行的不是我以为的程序”或“脚本中找不到命令”，最有区分度的第一条证据是当前 Shell 自己的解析结果。`type` 适合人工调查，`command -V` 给详细说明，`command -v` 给简洁结果和退出状态；`which` 与 `whereis` 只能补充位置线索。

### ① <span class="point-label">查询</span> 用 `type` 建立当前优先对象与同名候选

```bash
type name
type -a name
type -t name
```

- `type name`：报告当前优先解析结果；
- `type -a name`：尽可能列出 alias、function、builtin 和外部路径等所有可见候选；
- `type -t name`：只输出稳定类别词，如 `alias`、`function`、`builtin`、`file`，适合机器判断。

输出文案会受 Bash 版本与 locale 影响。复习时应识别对象类别，不背完整英文句子。若 `type -a` 同时显示 builtin 与外部路径，当前优先项由普通 `type name` 证明。

### ② <span class="point-label">查询</span> 用 `command -V/-v` 区分人工说明与简洁判断

```bash
command -V name
command -v name
```

`command -V` 输出较详细、适合人工阅读的说明。`command -v` 返回简洁表示：外部命令常返回路径，builtin 常只返回名称，alias 可能返回定义文本。因此不能把所有成功结果当成文件路径。

脚本只需要判断当前环境能否解析名称时，可使用：

```bash
if command -v name >/dev/null 2>&1; then
    printf '%s\n' 'name is resolvable in this shell'
fi
```

这只证明“可解析”，不证明程序具备权限、依赖、配置或业务功能。

### ③ <span class="point-label">边界</span> `which` 只能降级为外部路径线索

`which name` 通常按当前 `PATH` 寻找外部可执行文件，但实现、alias 包装和初始化环境可能不同。若 `type name` 显示 alias，而 `which name` 显示 `/usr/bin/name`，应得出：

```text
当前 Bash 优先使用 alias
/usr/bin/name 是同名外部候选
```

不要为了让两条输出一致而删除 alias。先确认题目或工单要调查的是当前行为，还是外部文件本身。

### ④ <span class="point-label">查询</span> 用 `whereis` 补充二进制、源码和手册位置

```bash
whereis name
whereis -b name
whereis -m name
```

`whereis` 根据其已知的常用搜索目录以及显式指定的范围查找；`-b` 只看二进制，`-m` 只看手册。它不读取当前 Shell 的 alias、function 和 builtin 优先级，也不证明路径由哪个包拥有。

### ⑤ <span class="point-label">诊断</span> 更新后仍指向旧路径时先区分缓存与对象遮蔽

先重新取证：

```bash
type -a name
command -V name
```

若结果证明只是 Bash 的外部命令哈希缓存，再执行：

```bash
hash -r
```

随后用相同查询复查。`hash -r` 不会修改 `PATH`、alias、function 或软件安装状态；若文件确实不存在，应转到软件包层继续调查。

<div class="evidence-box"><b>验证：</b>`type`/`command` 能证明当前 Bash 怎样解析。<b>不能证明：</b>文件归属、仓库提供者、程序运行成功或业务终态。</div>

</section>

<section class="topic operation" id="RHCSA-03-O02">

## <span class="topic-label">操作专题</span> 按对象选择 `help`、`--help`、`man` 与 `info`

帮助入口的选择由对象类型决定。最常见的低效路径是：对 builtin 机械尝试 `--help`，对外部程序只读一屏短帮助，或在命令名未知时逐个猜测。稳定方法是先用 `type` 确认对象，再进入由对象维护者提供的本地文档。

### ① <span class="point-label">操作</span> Bash builtin 优先使用 `help`

```bash
type cd
help cd
help -s cd
help -d cd
```

`help cd` 读取当前 Bash 版本的完整 builtin 说明；`-s` 只看简短语法，`-d` 只看短描述。`cd`、`read`、`export`、`type`、`command` 等应优先从这里开始。

同名 builtin 与外部命令并存时，帮助源也必须分开：

```bash
help test
man 1 test
```

前者解释 Bash builtin，后者解释外部 `test(1)`；功能相似不代表是同一个对象。

### ② <span class="point-label">操作</span> `COMMAND --help` 用于快速确认常用形式

```bash
command-name --help
```

短帮助通常适合在几十秒内确认 Usage、常用选项、参数是否带值和子命令入口。它是广泛使用的约定，不是每个程序都完全一致的强制接口；有些程序使用 `subcommand --help`，有些把详细文件、环境变量和退出状态留在 man 或 Info 中。

```text
快速确认常用写法
→ --help

需要完整语义、文件、退出状态和关联主题
→ man

需要节点式长文档或教程式说明
→ info
```

### ③ <span class="point-label">操作</span> `man` 是完整本地参考的主入口

```bash
man page
man section page
```

手册页随相关软件包或文档包安装。`man page` 查不到时，先检查对象是否为 builtin、主题名称和 section 是否正确，再考虑手册是否未安装；不能立即推出系统没有该命令或能力。

分页器中的高频导航：

| 键 | 用途 |
|---|---|
| `/pattern` | 向后搜索 |
| `n` / `N` | 下一个 / 上一个匹配 |
| `g` / `G` | 页首 / 页尾 |
| `q` | 退出 |

### ④ <span class="point-label">操作</span> `info` 是可选的节点式补充

```bash
info topic
```

Info 以节点、菜单和交叉引用组织内容。`n`、`p`、`u` 分别进入下一节点、上一节点和上一级，`Enter` 跟随菜单或链接。最小化系统不保证所有 Info 文档存在；缺少节点时回到 `--help` 和 `man`，而不是把它解释为命令不存在。

### ⑤ <span class="point-label">流程</span> 建立可重复的本地帮助路由

```text
type / command -V
│
├─ alias       → 看展开内容，再查真实命令
├─ function    → 查看函数定义，再查内部调用对象
├─ builtin     → help name
└─ external    → name --help → man [section] name → info name

只知道功能，不知道名称
└─ apropos keyword / man -k keyword
```

互联网文档可能更新更快，但考试环境可能无外网，且本地文档与当前安装版本直接对应，所以本地帮助应是第一证据。

<div class="evidence-box"><b>验证：</b>找到与当前对象匹配的帮助入口，并能从中定位语法。<b>不能证明：</b>命令已安装到所有环境、配置正确或操作终态成立。</div>

</section>

<section class="topic operation" id="RHCSA-03-O03">

## <span class="topic-label">操作专题</span> 从 man section 和标准标题提取操作依据

打开 man page 只是起点。真正要训练的是快速回答四个问题：页面描述的对象是谁、命令骨架怎样读、关键参数改变什么、相关文件和下一张手册在哪里。section 是对象分类，不是难度等级。

### ① <span class="point-label">知识点</span> 用 section 区分同名对象

| Section | 主要对象 | RHCSA 常见用途 |
|---:|---|---|
| 1 | 用户命令与 Shell 命令 | 普通命令调用形式 |
| 2 | 系统调用 | 深度排错或编程接口 |
| 3 | 库函数 | 程序库接口 |
| 4 | 特殊文件与设备 | 设备和内核接口文件 |
| 5 | 文件格式与配置文件 | 字段、配置语法、文件结构 |
| 6 | 游戏 | 本考试很少使用 |
| 7 | 约定、协议与杂项 | 信号、协议、正则等整体主题 |
| 8 | 系统管理命令 | 管理员常用工具 |
| 9 | 内核例程 | 内核开发接口 |

引用手册时常写作 `passwd(1)`、`passwd(5)`。括号中的数字是 section，不是版本号。

### ② <span class="point-label">操作</span> 显式 section 消除歧义

```bash
man passwd
man 1 passwd
man 5 passwd
```

默认 `man passwd` 按系统配置的 section 顺序选择匹配页，通常先进入命令页。任务要求读取 `/etc/passwd` 字段时，必须显式进入 `man 5 passwd`。同理，文件格式通常看 section 5，管理命令常见于 section 8，但最终仍以页面对象为准。

### ③ <span class="point-label">知识点</span> 正确读取 `SYNOPSIS` 的形式符号

`SYNOPSIS` 是形式语法，不是必须原样复制的一条固定命令：

- 固定命令名和选项按原样输入；
- `FILE`、`NAME` 等占位词替换成实际值；
- `[ ... ]` 表示可选部分；
- `...` 表示前一项可以重复；
- `A | B` 表示替代形式；
- 多行 Synopsis 往往表示多种调用模式，不应拼成一行执行。

读完后应能写出目标命令骨架，并解释哪些部分是固定语法、哪些需要替换。

### ④ <span class="point-label">查询</span> 用标准标题定位所需证据

| 标题 | 主要问题 |
|---|---|
| `NAME` | 页面对象及一句话用途是什么 |
| `SYNOPSIS` | 命令或接口的形式怎样写 |
| `DESCRIPTION` | 对象机制和默认行为是什么 |
| `OPTIONS` | 参数如何改变语义、是否带值 |
| `EXIT STATUS` | 返回码怎样解释 |
| `ENVIRONMENT` | 哪些环境变量影响行为 |
| `FILES` | 相关配置、数据或状态路径在哪里 |
| `EXAMPLES` | 维护者给出的典型组合是什么 |
| `SEE ALSO` | 下一张关联手册是什么 |

页面不一定包含全部标题。查参数先搜 `OPTIONS` 或具体选项，查配置路径看 `FILES`，查同名对象与关联页看 `SEE ALSO`。

### ⑤ <span class="point-label">验证</span> 把帮助内容转成可核对的命令计划

在执行真实变更前，至少写清：

```text
作用对象
→ 命令骨架
→ 关键参数及取值
→ 相关文件或前置状态
→ 操作后验证入口
→ 帮助页没有证明的部分
```

例如 man page 说明 `-f FILE` 选择文件，只能证明参数语义；目标文件存在、权限允许、结果内容正确仍需要后续证据。

<div class="cheatsheet"><b>man 快读：</b>先看 NAME 确认对象，再看 SYNOPSIS 还原骨架；OPTIONS 找参数，FILES 找路径，SEE ALSO 找下一跳；同名页面显式指定 section。</div>

</section>

<section class="topic operation" id="RHCSA-03-O04">

## <span class="topic-label">操作专题</span> 不知道命令名时按关键字发现本地能力

有时题目只描述“修改密码过期时间”或“查找压缩归档工具”，并没有给出命令名。此时不应随机尝试名字，而应把任务语言压缩成稳定名词，从 man 索引发现候选主题，再打开具体页面确认。

### ① <span class="point-label">查询</span> `whatis` 适合已知准确名称

```bash
whatis passwd
man -f passwd
```

`whatis` 从索引中返回与名称匹配的一行描述，通常包含主题、section 和短说明。它适合确认同名页面有哪些，不适合用模糊的自然语言问题搜索全部内容。

### ② <span class="point-label">查询</span> `apropos` 与 `man -k` 按关键字发现主题

```bash
apropos password
man -k password
```

输出通常由三部分组成：

```text
主题名称 (section) - 一行描述
```

筛选时先看 section，再看描述是否对应任务对象。例如“password aging”可尝试 `password`、`aging`、`expiry` 等稳定名词；过窄的整句搜索反而容易漏掉页面。

### ③ <span class="point-label">操作</span> 从候选列表回到具体 man page

```bash
apropos password
man 1 chage
man 5 login.defs
```

发现只是候选阶段。必须打开页面确认 `NAME`、`SYNOPSIS`、相关文件和参数边界，不能只凭一行描述执行命令。

### ④ <span class="point-label">诊断</span> 空结果先区分关键词、文档与索引

```text
症状：apropos 没有结果
│
├─ 关键词过窄或语言不匹配
├─ 本机没有对应 man page
└─ whatis 索引缺失或陈旧
```

下一条证据应是：

```bash
whatis known-command
man known-command
```

若已知页面能打开但索引查询异常，再由有权限的管理员检查：

```bash
mandb
```

然后重复原查询。只有重建索引后同一关键字恢复，才足以把问题归到索引层。`mandb` 维护手册索引，不安装目标业务软件。

### ⑤ <span class="point-label">边界</span> 索引搜索不是全文互联网搜索

`apropos` 主要匹配手册名称和短描述，结果受本地语言、已安装手册和索引影响。未命中不代表整个 Linux 生态没有该工具；命中也不代表命令已在当前 `PATH` 可调用。后续仍需 `type`、`man` 和软件包证据。

<div class="evidence-box"><b>验证：</b>从关键词得到候选主题，并通过具体 man page 复核。<b>不能证明：</b>候选命令已安装、当前 Shell 可调用或任务已经完成。</div>

</section>

<section class="topic operation" id="RHCSA-03-O05">

## <span class="topic-label">操作专题</span> 用 `rpm -qf` 证明已安装文件归属

当问题是“本机 RPM 数据库把这个路径记录给哪个已安装包”，首选 `rpm -qf`，而不是仓库搜索。查询键应使用准确路径；该查询读取包数据库，即使文件后来缺失，数据库中的所有权记录仍可能存在，因此还要把“数据库所有权”与“文件当前存在”分开验证。

### ① <span class="point-label">操作</span> 以绝对路径查询本机所有者

```bash
rpm -qf /usr/bin/chage
```

合格结论应写成：

> 本机 RPM 数据库记录 `/usr/bin/chage` 由查询结果中的已安装包拥有。

不要只写“`chage` 来自某包”，因为同名文件可能位于不同目录，且其他主机的安装状态可能不同。

### ② <span class="point-label">输出</span> 区分三种状态

| 现象 | 允许判断 | 下一条证据 |
|---|---|---|
| 返回包名/NEVRA | 本机 RPM 数据库存在该路径的所有权记录 | 用 `rpm -ql package` 反向核对；另查路径是否实际存在 |
| 提示文件不属于任何包 | 该输入路径没有匹配的本地 RPM 所有权记录 | 核对路径拼写；若文件存在，判断是否为手工或运行时内容 |
| 路径当前不存在，但查询仍返回包名 | 数据库仍记录该包应拥有此路径 | 第 16 章再做包完整性与恢复验证 |

“无所有者”不自动等于恶意文件，也不自动等于应删除。管理员脚本、编译安装内容和运行时生成文件都可能不属于 RPM 包；反过来，数据库有所有权记录也不证明文件此刻仍存在。

### ③ <span class="point-label">查询</span> 用 `rpm -ql` 做反向核对

```bash
rpm -ql package-name
```

如果 `rpm -qf` 返回包名，可以从包到文件清单反向确认路径。此处仍是只读查询；包签名、完整性验证、安装、升级和删除留给第 16 章。

### ④ <span class="point-label">边界</span> 所有权不等于内容完整和命令可用

`rpm -qf` 不证明：

- 文件当前实际存在；
- 文件内容与软件包原始内容一致；
- 当前用户有执行权限；
- 路径位于当前 `PATH`；
- 程序依赖与配置正常；
- 仓库中只有这一个提供者。

需要确认当前 Shell 是否能调用时，回到 `type`；需要查询缺失路径的候选包时，使用 `dnf provides`。

<div class="cheatsheet"><b>本地归属：</b>准确路径 → `rpm -qf` → 记录数据库所有权 → `rpm -ql` 反向核对；文件是否存在、是否完整和是否可用仍要另行验证。</div>

</section>

<section class="topic operation" id="RHCSA-03-O06">

## <span class="topic-label">操作专题</span> 用 `dnf provides` 查询缺失路径的候选提供者

命令不存在时，先用 `type` 或 `command -v` 证明当前 Shell 无法解析；随后需要从可靠文档或路径约定得到尽可能准确的目标路径，再让 DNF 查询谁能够提供它。`dnf provides` 是能力发现，不是安装动作。

### ① <span class="point-label">操作</span> 已知准确路径时优先精确查询

```bash
dnf provides /usr/sbin/semanage
```

精确路径能减少误匹配。输出中至少记录：候选包名、版本/发行号、架构、来源仓库或安装状态，以及实际匹配的路径或 capability。

### ② <span class="point-label">操作</span> 只知道 basename 时使用受保护的路径模式

```bash
dnf provides '*/semanage'
```

引号非常重要：它把 `*` 原样交给 DNF，而不是让当前 Shell 先按工作目录文件名展开。模式越宽，候选越多；拿到结果后应检查真实匹配路径，而不是只看第一个包名。

### ③ <span class="point-label">输出</span> 多个候选时按目标环境筛选

多个结果可能来自不同架构、版本、仓库或已安装/可用状态。筛选顺序：

```text
匹配路径是否正确
→ 架构是否符合主机
→ 来源仓库是否为当前允许范围
→ 版本与模块/系统约束是否匹配
→ 是否已经安装（若输出明确显示）
```

本章不执行安装。真正选择、安装和事务验收转第 16、17 章。

### ④ <span class="point-label">诊断</span> 无结果时不要立刻猜包名

```text
症状：dnf provides 无候选
│
├─ 文件名或路径拼写错误
├─ 查询模式过窄或过宽
├─ 目标文件属于未启用仓库
├─ 元数据不可用或陈旧
└─ 当前架构/版本确实没有提供者
```

下一条最有区分度的证据依次是：确认准确路径、调整受保护模式、查看 DNF 是否能读取当前仓库元数据。仓库创建、启停和修复属于第 17 章，本章只记录阻断位置。

### ⑤ <span class="point-label">验证</span> 把“可提供”与“已可调用”分开

即使以后完成安装，仍需分层复查：

```text
dnf/rpm 安装状态
→ rpm -qf 实际路径的本地所有权
→ type / command -v 当前 Shell 解析
→ command --help / man 语法依据
→ 真实任务的功能验证
```

`dnf provides` 只完成第一步之前的候选发现。

<div class="evidence-box"><b>验证：</b>当前 DNF 可见数据中存在与目标路径匹配的候选提供者。<b>不能证明：</b>候选已安装、命令在 PATH 中、配置正确或业务功能成立。</div>

</section>

<section class="topic diagnosis" id="RHCSA-03-D01">

## <span class="topic-label">诊断专题</span> 让互相矛盾的查询结果回到各自证据层

本章的高频故障并不是某个命令“坏了”，而是把不同层的输出当作同一种事实。诊断时先写清症状和当前证据，再选择一条能够排除一类假设的查询；最小修复后必须回到原层复查。

### ① <span class="point-label">诊断</span> `command not found`

```text
症状
→ 当前 Shell 无法解析名称

当前证据
→ type name
→ command -v name

假设
├─ 拼写错误
├─ alias/function 只在另一个会话存在
├─ 外部文件不在 PATH
├─ Bash 仍缓存旧路径
└─ 目标软件尚未安装

下一条证据
→ type -a / command -V
→ 确认预期路径
→ 必要时 hash -r
→ dnf provides 准确路径或受保护模式
```

最小处理由证据决定。不要在未确认包和仓库范围前直接安装相似名称的软件。

### ② <span class="point-label">诊断</span> `type` 与 `which` 不一致

```text
若 type 显示 alias/function/builtin
而 which 显示 /usr/bin/name
```

下一条证据是 `type -a name`。它能证明当前优先对象及同名外部候选。结论应写“当前 Bash 先使用前者，外部文件仍存在”，而不是挑一条输出宣布另一条错误。

### ③ <span class="point-label">诊断</span> 命令可执行但 `man name` 查不到

```text
当前证据
→ type name

假设
├─ 对象是 builtin，应使用 help
├─ 手册主题名不同
├─ 需要显式 section
└─ 本地手册未安装

下一条证据
→ help name
→ name --help
→ whatis / apropos
→ man section topic
```

先确认对象和主题，再决定是否存在文档缺口。

### ④ <span class="point-label">诊断</span> `apropos` 空结果

先用已知页面验证两层：

```bash
man ls
whatis ls
```

- `man ls` 也失败：优先调查手册是否安装；
- `man ls` 成功但 `whatis ls` 异常：索引层更可疑；
- 已知查询正常：调整关键字、语言和 section 预期。

需要重建索引时执行 `mandb`，再重复原查询。不能只因空结果就宣布系统没有相关能力。

### ⑤ <span class="point-label">诊断</span> `rpm -qf` 无所有者，但 `dnf provides` 有候选

这两条结果完全可以同时成立：本机路径可能未安装、路径不存在、由管理员手工创建，或查询路径与候选匹配路径不同；仓库仍可声明某包能够提供它。

下一条证据：

```text
确认输入路径是否真实存在
→ 核对 rpm 查询使用的绝对路径
→ 记录 dnf 实际匹配路径
→ 不把仓库候选倒推成本机所有权
```

### ⑥ <span class="point-label">安全边界</span> 找到强制选项不等于应当使用

本地帮助可能显示 `--force`、`--nodeps`、`--allowerasing` 等绕过机制。找到它们只能证明工具支持这些形式，不能证明题目允许破坏依赖、覆盖文件或扩大变更范围。本章默认只读调查；软件事务和高风险修改必须回到相应章节的对象、约束与验收链。

### ⑦ <span class="point-label">工作迁移</span> 工单中保留可重建判断的最小证据

建议记录：

```text
原始症状、名称或路径
当前用户、Shell 和 PATH 范围
关键 type / command 结果
实际帮助主题与 section
rpm 所有权或 dnf 候选提供者
未证明的层次与后续功能验证入口
```

这使同事或自动化 Agent 可以复核判断，而不是只看到一句“安装某包即可”。

<div class="cheatsheet"><b>诊断链：</b>症状 → 当前证据 → 分层假设 → 一条高区分度查询 → 最小修复 → 回到原层复查。</div>

</section>


<section class="topic task" id="RHCSA-03-T01">

## <span class="topic-label task-label">经典任务</span> 在无互联网、禁止安装软件的条件下完成本地能力调查

### 环境

你以普通用户登录一台 RHEL 9 主机，当前交互 Shell 为 Bash。本机能够读取已安装 man page、RPM 数据库和 DNF 当前可见的软件包元数据。任务期间不允许访问互联网，不允许安装、删除或升级软件包，也不允许修改仓库配置。

### 当前状态

管理员准备进行账号维护，但遇到以下未知项：

1. 不确定 `test` 在当前 Shell 中是 builtin、外部命令，还是同时存在多个候选；
2. 不知道 `cd` 的准确语法应从哪里查询；
3. 需要阅读 `/etc/passwd` 的文件格式，而不是执行修改密码的 `passwd` 命令；
4. 只知道要调查 “password aging”，不知道准确命令名；
5. 需要证明 `/usr/bin/chage` 由哪个已安装软件包拥有；
6. 当前无法调用 `semanage`，需要确定 DNF 当前可见数据中哪个包能够提供该命令文件。

### 目标终态

提交一份调查记录。每个对象必须写明：

- 使用的查询命令；
- 为什么选择该入口；
- 从输出中提取的字段或结论；
- 该证据不能证明什么；
- 查询无结果时，下一条最有区分度的证据。

### 限制条件

- 不把 `which` 作为最终命令类型证据；
- 不凭记忆直接写 `semanage` 的包名；
- 不写死具体包版本、架构或仓库名称；
- `apropos` 无结果时必须调查关键词、man page 与索引；
- `dnf provides` 命中后不得声称软件已安装；
- 不使用互联网搜索作为第一证据；
- 不通过改 `PATH`、删除 alias 或安装软件来让输出“看起来一致”。

### 验收矩阵

| 评分对象 | 必须出现的证据 | 合格判断 | 明确边界 |
|---|---|---|---|
| `test` 对象类型 | `type` / `type -a`，辅以 `command -V/-v` | 能区分当前优先对象与同名候选 | 不证明外部文件归属 |
| `cd` 帮助 | `type cd`、`help cd` | 明确 `cd` 是 Bash builtin | 不把结果当外部程序路径 |
| `/etc/passwd` 格式 | `man 5 passwd` | 明确 section 5 为文件格式 | 不证明当前文件内容正确 |
| password aging 发现 | `apropos` 或 `man -k` | 从名称、section 与描述识别候选 | 仍需打开具体页面 |
| `/usr/bin/chage` 归属 | `rpm -qf /usr/bin/chage` | 只声明本机已安装包所有权 | 不证明文件完整或仓库唯一 |
| `semanage` 提供者 | `dnf provides '*/semanage'` 或准确路径查询 | 记录候选包、架构、来源与匹配路径 | 不声明已安装或可调用 |
| 失败诊断 | 对空结果给出下一条证据 | 不把空结果直接解释为能力不存在 | 不越权修改仓库或安装软件 |

</section>


<section class="topic answer" id="RHCSA-03-A01">

## <span class="topic-label answer-label">参考解答</span> 先确认对象，再沿证据层推进

以下是调查骨架。本章未连接受控 RHEL 9 虚拟机，因此不编造固定版本、locale、仓库或完整输出；实际环境应记录主机返回的真实内容。

### ① 确认 `test` 的当前解析对象与所有候选

```bash
type test
type -a test
command -V test
command -v test
```

参数选择：

- 普通 `type` 证明当前优先对象；
- `-a` 展开同名候选，便于识别 builtin 与外部文件并存；
- `command -V` 提供人工可读说明；
- `command -v` 提供简洁结果和退出状态，但 builtin 可能只返回名称。

分层验收：只声明当前 Bash 如何解析。若要证明外部候选的包归属，把 `type -a` 返回的真实路径交给 `rpm -qf`。

### ② 为 builtin `cd` 选择帮助入口

```bash
type cd
help cd
help -s cd
```

`type` 先确认对象，`help cd` 再读取当前 Bash 的完整说明；只需快速看形式时使用 `help -s cd`。不以 `cd --help` 代替 builtin 的标准帮助入口。

### ③ 显式选择 `/etc/passwd` 的文件格式页

```bash
whatis passwd
man 5 passwd
```

`whatis` 用来观察同名主题和 section，`man 5 passwd` 明确进入文件格式页。阅读时至少定位：

```text
NAME        页面对象
DESCRIPTION 文件用途与字段
FILES       相关路径
SEE ALSO    passwd(1)、shadow(5) 等下一跳
```

若只执行 `man passwd`，必须额外证明实际打开的是 section 5，否则不满足题目要求。

### ④ 按功能描述发现 password aging 相关主题

```bash
apropos password
man -k password
```

两条是同一类索引查询入口。根据输出的主题名称、section 与描述筛选候选，再打开具体页面，例如：

```bash
man 1 chage
```

若结果过多，换用 `aging`、`expiry` 等稳定名词；若完全无结果，先检查已知页面与索引：

```bash
man passwd
whatis passwd
```

确认手册可读而索引异常后，才由有权限用户考虑：

```bash
sudo mandb
apropos password
```

修复后必须重复原查询，才能证明索引层已恢复。

### ⑤ 查询 `/usr/bin/chage` 的本地 RPM 所有权

```bash
rpm -qf /usr/bin/chage
```

记录真实返回包。结论必须限定为：

> 本机 RPM 数据库记录该已安装包拥有 `/usr/bin/chage`。

需要反向核对时：

```bash
rpm -ql package-name
```

这仍不证明文件当前存在、内容未修改、当前用户可执行或仓库中只有该提供者。

### ⑥ 查询 `semanage` 的候选提供者

先证明当前 Shell 无法解析：

```bash
type semanage
command -v semanage
```

只知道 basename 时：

```bash
dnf provides '*/semanage'
```

若已经从可靠文档得到准确路径，则优先：

```bash
dnf provides /usr/sbin/semanage
```

从实际输出记录候选包、版本/发行号、架构、来源与匹配路径。不要凭记忆写死包名；不要把候选关系写成已安装状态。

无结果时按顺序调查：拼写与路径、模式是否被引号保护、DNF 元数据是否可读、目标仓库是否在当前允许范围。仓库修复和安装留给第 16、17 章。

### ⑦ 汇总证据矩阵

| 对象 | 证据层 | 允许声明 | 不能扩大为 |
|---|---|---|---|
| `test` | 当前 Bash 解析 | 当前优先对象与同名候选 | 软件包所有权或功能健康 |
| `cd` | Bash builtin 帮助 | 当前 Bash 的语法 | 外部程序安装状态 |
| `passwd(5)` | 本地文件格式手册 | 字段语义与关联路径 | `/etc/passwd` 当前内容无误 |
| `apropos password` | man 索引 | 本地相关候选主题 | 命令已安装或已执行 |
| `rpm -qf` | 本机 RPM 数据库 | 路径的已安装包所有权记录 | 文件当前存在、内容完整或仓库唯一提供者 |
| `dnf provides` | DNF 当前可见软件包数据 | 候选提供关系 | 已安装、可调用或功能完成 |

### ⑧ 典型错误与修正

| 错误 | 为什么不合格 | 最小修正 |
|---|---|---|
| 只执行 `which test` | 忽略 builtin、function 和 alias | 用 `type` / `type -a` |
| 直接 `man passwd` | 没有证明页面属于 section 5 | 使用 `man 5 passwd` |
| `apropos` 空结果后宣布没有命令 | 未区分关键词、文档与索引 | 检查已知页面和 `whatis`，必要时 `mandb` |
| 把 `command -v cd` 的 `cd` 当路径 | builtin 的简洁结果可以只是名称 | 结合 `type cd` 与 `help cd` |
| 把 `rpm -qf` 与 `dnf provides` 都翻译成“来自哪个包” | 混淆本地所有权与候选提供关系 | 分别记录本机数据库与 DNF 数据范围 |
| `dnf provides` 命中后写“已安装” | 候选关系不等于安装状态 | 后续用 RPM/DNF 安装查询验证 |
| 未引用 `*/semanage` | 通配符可能先被当前 Shell 展开 | 使用单引号保护模式 |

</section>


<section class="topic summary" id="RHCSA-03-S01">

## <span class="topic-label summary-label">本章收束</span> 把“不知道”转换成一条可复核的本机调查路径

本章的工作方法不是记住所有工具，而是稳定选择下一条证据：

```text
未知名称或异常行为
→ type / command 确认当前 Shell 对象
→ help / --help / man / info 选择匹配的帮助源
→ SYNOPSIS / OPTIONS / FILES / SEE ALSO 提取操作依据
→ whatis / apropos 在名称未知时发现主题
→ rpm -qf 证明本机已有路径的包所有权
→ dnf provides 证明 DNF 可见数据中的候选提供关系
→ 将每条结论限制在它实际证明的层次
```

## 主要判断表

| 问题 | 第一入口 | 结论范围 | 下一层 |
|---|---|---|---|
| 当前 Shell 会执行什么 | `type` / `command -V` | 当前会话的解析对象 | 帮助或实际路径 |
| 是否有同名候选 | `type -a` | 当前环境可见的候选集合 | 选择目标对象 |
| builtin 怎样使用 | `help` | 当前 Bash builtin 语义 | 操作后状态验证 |
| 外部程序常用形式 | `--help` | 快速 Usage 与常用选项 | `man` / `info` |
| 同名 man page 怎样消歧 | `man section page` | 特定对象的本地手册 | 读取标准标题 |
| 只知道功能怎样发现命令 | `apropos` / `man -k` | 本地索引候选 | 打开具体 man page |
| 已有路径属于哪个已安装包 | `rpm -qf` | 本机 RPM 所有权 | 安装/验证章节 |
| 缺失路径由谁提供 | `dnf provides` | DNF 可见候选提供者 | 仓库与事务章节 |
| 查询结果互相矛盾 | 先标注各自证据层 | 不强求输出一致 | 选择高区分度下一证据 |

## 工作方法

1. 先写问题层，再敲命令；
2. 先用当前环境证据确认对象，再进入帮助；
3. 读手册时从对象和形式开始，不从示例盲抄；
4. 空结果先调查可见性与索引，不直接宣布对象不存在；
5. 软件来源必须区分本机所有权与仓库候选；
6. 任何“找到”都不是最终功能证明。

## 向下一章交接

本章把路径当作查询键，但尚未解释路径如何解析、文件类型怎样区分、硬链接与符号链接如何影响对象身份。第 04 章《文件系统层次、路径、文件类型与链接》将在这里继续：当你已经找到一个路径，下一步要判断它在文件系统中究竟指向什么。

<div class="final-note">本章未连接受控 RHEL 9 虚拟机，也未执行命令级 live test。环境相关的真实输出应在后续实验中按本章证据链回填。</div>

</section>
