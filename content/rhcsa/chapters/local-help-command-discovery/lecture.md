---
title: "RHCSA 第 03 章 本地帮助、命令发现与软件能力查询"
chapter_id: RHCSA-03
exam: RHCSA
part: "第一篇 命令行与本地信息处理"
slug: local-help-command-discovery
status: integrated
validation: static
live_test: not_performed
base_commit: "39e873dab15347a0f1a7611a6f212c3d26bd3562"
sources:
  - RH124-RHEL9-Ch4
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

<!-- 维护元数据、来源和内部 ID 不应在正式发布版正文中显示。 -->

# 第 03 章　本地帮助、命令发现与软件能力查询

面对一条陌生命令时，最危险的习惯不是“记不住参数”，而是还没有确认自己正在调查什么，就直接从记忆、搜索引擎或一段旧命令中抄答案。相同的名称在当前 Bash 中可能是 alias、function、builtin，也可能是磁盘上的外部程序；一条路径可能已经由某个 RPM 包安装，也可能只是管理员手工创建；仓库中有软件包能够提供某个文件，也不代表该包已经安装，更不代表当前 Shell 已经能调用它。

本章建立一条只依赖本机证据的调查路径。先从当前 Shell 的视角确认名称如何解析，再为对应对象选择 `help`、`--help`、`man` 或 `info`；不知道命令名时，通过 `whatis`、`apropos` 和 man 索引按功能发现能力；已经拿到文件路径时，使用 `rpm -qf` 查询本地所有权；命令或路径缺失时，使用 `dnf provides` 查询当前软件源元数据中的提供者。整条路径的重点不是“知道更多命令”，而是让每一个结论都能回答：证据来自哪里、证明到哪一层、还不能证明什么。

**[概念]** 命令名称只是输入给 Shell 的文本。当前 Bash 可能把它解释为 alias、function、builtin 或外部可执行文件；这些对象的生命周期、帮助入口和软件包归属并不相同。

**[概念]** 帮助文档也是系统对象。Bash builtin 的语义由 Bash 自己记录；外部程序可能提供短帮助、man page 或 Info 文档；`whatis` 与 `apropos` 依赖手册索引，而不是直接扫描整个系统。

**[概念]** 本地 RPM 数据库记录“已安装软件包拥有了哪些路径”；DNF 仓库元数据记录“哪些候选软件包声明能够提供某个文件或能力”。本地所有权与仓库提供能力是两个不同状态。

**[操作语义]** `type` 与 `command -V/-v` 从当前 Bash 的解析环境取得证据；`help`、`--help`、`man`、`whatis`、`apropos` 和 `info` 从不同帮助源取得语法和说明；`rpm -qf` 与 `dnf provides` 分别查询本机安装状态和仓库能力。

**[操作语义]** 本章的“操作”以调查为主。除重建手册索引等明确诊断动作外，不通过安装、删除、强制覆盖或修改仓库来制造答案；软件事务归第 16 章，DNF 仓库配置归第 17 章。

<section class="topic knowledge" id="RHCSA-03-K01" data-kind="knowledge-topic">

## [知识专题] 名称、对象、位置和软件包是四个不同问题

命令行上的一个单词看起来很简单，但从输入到执行至少经过了 Shell 语法识别、alias 展开、function 与 builtin 查找、外部命令路径搜索等层次。排错时若把这些层次压成一句“这个命令在哪里”，就会出现典型误判：`which` 找到一个文件，却没有发现同名 alias；`command -v` 返回 builtin 名称，却被当成磁盘路径；`dnf provides` 找到软件包，却误以为命令已经安装。

### ① [知识点] 当前 Shell 能调用的对象不只有外部文件

本章重点区分四类对象：

| 对象 | 本质 | 常见作用范围 | 首选身份查询 | 首选帮助入口 |
|---|---|---|---|---|
| alias | Shell 在解析阶段替换的名称缩写 | 当前 Shell，可能来自启动文件 | `type` | 查看 alias 定义并转向真实命令帮助 |
| function | 当前 Shell 中定义的命令体 | 当前 Shell 或子 Shell 导入范围 | `type`、`declare -f` | `type`/`declare -f` 读定义，再查其调用命令 |
| builtin | Bash 进程内部实现的命令 | Bash 自身 | `type`、`command -V` | `help <builtin>` |
| 外部命令 | 文件系统中的可执行程序或脚本 | 取决于路径、权限和环境 | `type`、`command -v` | `<command> --help`、`man`、`info` |

alias 可能把短名称展开为带参数的完整命令；function 可以包含多条命令和控制结构；builtin 不需要从磁盘启动独立程序；外部命令则通常对应一个可执行路径。它们可能同名，因此“知道名字”并不等于“知道对象”。

### ② [知识点] 当前解析结果、磁盘位置、文件所有权和仓库提供者不是同一事实

稳定调查应明确自己正在回答哪一个问题：

```text
当前 Bash 会执行什么
        → type / command -V / command -v

磁盘上可能有哪些相关二进制、源码或手册位置
        → whereis；which 仅作路径线索

本机这个路径由哪个已安装 RPM 包拥有
        → rpm -qf <PATH>

当前启用的软件源中哪个包能够提供这个路径
        → dnf provides <PATH-OR-PATTERN>
```

这四层可以给出不同答案，而且不同并不表示其中某条命令“出错”。例如 alias 可以遮蔽外部命令；管理员手工创建的脚本可能不属于任何 RPM 包；仓库中存在新版本提供者，也不改变本机当前安装包的所有权记录。

### ③ [知识点] 查询结果具有作用范围和时间边界

`type` 与 `command` 观察当前 Bash 的状态。换一个用户、Shell、`PATH`、启动文件或会话，结果可能不同。Bash 还可能缓存外部命令的路径；系统更新或文件移动后，必要时使用 `hash -r` 清理当前 Shell 的命令路径缓存，再重新查询。

`rpm -qf` 观察本机 RPM 数据库；`dnf provides` 观察当前系统可见的软件源元数据。仓库启停、订阅、架构和元数据时间都会影响候选结果。任何查询都必须连同它的观察范围一起解释。

### ④ [知识点] 本地帮助是操作依据，不是操作结果

在 man page 中找到正确参数，只能证明命令语法有依据；程序返回成功，只能证明本次调用没有按其退出约定报告错误。真正的系统任务仍需在目标对象上验证当前状态、持久状态和功能状态。本章训练的是“找到可靠操作依据”，不能把帮助文本扩大成实际终态。

**[Cheatsheet]** 名称先交给 `type`；builtin 先查 `help`；外部命令先看 `--help`，完整细节进 `man`；已有路径用 `rpm -qf`；缺失路径用 `dnf provides`。位置、所有权、可提供和已可调用必须分开陈述。

</section>

<section class="topic operation" id="RHCSA-03-O01" data-kind="operation-topic">

## [操作专题] 用当前 Bash 的视角确认命令到底是什么

调查陌生命令的最顺切入点不是 `which`，而是让当前 Bash 直接说明：如果把这个名称放在命令位置，它会如何解释。`type` 适合人工调查，`command -V` 提供近似的详细描述，`command -v` 适合取得简洁结果和在脚本中检查名称是否可解析。

### ① [操作] 使用 `type` 识别 alias、function、builtin 和外部命令

**作用对象：** 当前 Bash 的命令解析环境。

**基本语义：** 对每个名称报告 Bash 会如何解释它。

```bash
type <NAME>
type -a <NAME>
```

`type <NAME>` 报告当前优先解析对象；`type -a <NAME>` 尽可能列出当前环境可见的所有同名候选。典型判断方式是：

- 输出包含 “aliased to” 一类说明：该名称当前首先是 alias；
- 输出函数定义：该名称是 Shell function；
- 输出 “shell builtin”：该名称是 builtin；
- 输出绝对路径：该名称解析为外部文件；
- 查询失败：当前 Bash 未找到该名称。

具体英文或本地化措辞可能随 Bash 和 locale 变化，考试中应识别对象类型，不背整句输出。

`type -t <NAME>` 可以只输出 `alias`、`function`、`builtin`、`file` 等类别词，适合需要机器判断的场景；普通人工调查仍优先使用 `type` 或 `type -a`，因为它们保留更多上下文。

### ② [操作] 使用 `command -V` 和 `command -v` 取得详细或简洁结果

**作用对象：** 当前 Bash 的命令查找结果。

```bash
command -V <NAME>
command -v <NAME>
```

`command -V` 给出较详细、适合人工阅读的说明，通常与 `type` 的可读输出相近。`command -v` 给出较简洁的表示：外部命令通常返回路径，builtin 通常返回名称，function 通常返回函数名，alias 可能返回 alias 定义。因此，`command -v` 的成功结果不能一律当作“可执行文件路径”。

在脚本中只需判断某名称是否可由当前 Shell 解析时，常见骨架是：

```bash
command -v <NAME> >/dev/null 2>&1
```

这里依赖第 02 章已经建立的重定向知识。该检查只证明当前环境能解析名称，不证明程序运行后能完成业务目标。

不带 `-V/-v` 的 `command <NAME> ...` 是执行接口，可抑制同名 Shell function 的查找。它不是本章重点，但解释了为什么 `command -v` 属于 Bash builtin，而不是另一个普通位置搜索程序。

### ③ [操作] 将 `which` 降级为路径线索

`which <NAME>` 通常根据当前 `PATH` 寻找可执行文件路径，但不同发行版、Shell 初始化和 `which` 实现可能对 alias 与 function 有不同处理。它适合快速取得外部位置线索，不适合作为 Bash 当前解析对象的唯一证据。

当 `type` 与 `which` 不同，应先解释对象层：

```text
若 type 显示 alias/function，而 which 显示 /usr/bin/...
→ 当前 Bash 先使用 alias/function
→ /usr/bin/... 只是同名外部候选
```

不要为了让两条输出一致而删除 alias 或 function；先确认任务真正要求调用哪一个对象。

### ④ [操作] 使用 `whereis` 查标准位置中的二进制、源码和手册

**作用对象：** `whereis` 已知的标准搜索目录与数据库线索。

```bash
whereis <NAME>
whereis -b <NAME>
whereis -m <NAME>
```

`whereis` 可以同时给出二进制、源代码和 man page 的位置线索；`-b` 只看二进制，`-m` 只看手册。它不按照当前 Bash 的完整 alias/function/builtin 规则回答“会执行什么”，也不证明某路径属于哪个 RPM 包。

### ⑤ [操作] 处理路径缓存和环境差异

如果一个外部程序刚被移动、替换或卸载，而当前 Shell 仍指向旧位置，可以先重新查询：

```bash
type -a <NAME>
command -V <NAME>
```

确认是当前 Bash 的外部命令路径缓存后，再执行：

```bash
hash -r
```

随后重新运行 `type` 和实际命令。`hash -r` 只清理当前 Bash 的命令路径缓存，不安装软件、不修改 `PATH`，也不会处理 alias 或 function。

**验证与边界：** `type`/`command` 的结果是当前 Shell 证据。需要证明本地软件包所有权时继续到 `rpm -qf`；需要证明仓库提供能力时继续到 `dnf provides`。

**[Cheatsheet]** 人工调查：`type`；所有候选：`type -a`；详细可读：`command -V`；简洁与退出状态：`command -v`；标准位置线索：`whereis`；`which` 不能替代 Bash 自己的判断；旧路径缓存用 `hash -r` 后复查。

</section>

<section class="topic operation" id="RHCSA-03-O02" data-kind="operation-topic">

## [操作专题] 已知命令名时选择正确的帮助入口

帮助入口的选择应由对象类型决定。最常见的失败不是“没有帮助”，而是把 builtin 当成外部程序、只看短帮助却遗漏配置文件、或者打开了同名但错误 section 的 man page。稳定顺序是先确认对象，再选择由该对象维护者提供的本地文档。

### ① [操作] Bash builtin 优先使用 `help`

**作用对象：** 当前 Bash 版本内置的命令与语法主题。

```bash
help <BUILTIN>
help -s <BUILTIN>
help -d <BUILTIN>
```

`help <BUILTIN>` 显示完整 builtin 帮助；`-s` 侧重简短语法；`-d` 显示短描述。需要确认 `cd`、`read`、`export`、`type` 或 `command` 等 Bash builtin 时，`help` 比机械执行 `<name> --help` 更可靠。

若 `type` 显示某名称既有 builtin 又有外部文件，应明确自己调查哪个对象：

```bash
help test
man 1 test
```

前者查询 Bash builtin，后者查询外部 `test(1)`。两者常实现相似功能，但帮助来源和进程行为不是同一对象。

### ② [操作] 使用 `--help` 快速读取外部程序的常用语法

很多 GNU 和 Linux 程序支持：

```bash
<COMMAND> --help
```

短帮助通常适合快速确认：Usage、常用选项、参数是否带值、互斥形式和退出约定。但 `--help` 是广泛采用的约定，不是所有程序都以完全相同的方式实现；有些程序使用子命令帮助，有些将完整细节放在 man 或 Info 中。

因此：

```text
需要几秒内确认常用参数 → --help
需要完整语义、文件、环境变量、退出状态和相关主题 → man
需要 GNU 节点式长文档或教程式说明 → info
```

### ③ [操作] 使用 `man` 进入系统本地参考

```bash
man <TOPIC>
man <SECTION> <TOPIC>
```

`man` 从本地手册路径中选择主题并通过分页器显示。已知准确主题时，先打开默认匹配；若存在同名页或需要文件格式、管理员命令等特定对象，则显式指定 section。

手册页随软件包安装。`man <TOPIC>` 查不到，并不能直接证明系统没有该功能：可能是对象其实是 Bash builtin、手册子包未安装、主题名称不同、section 选择错误，或本机确实没有该手册。

### ④ [操作] 使用 `info` 阅读节点式 GNU 文档

```bash
info <TOPIC>
```

Info 文档以节点和菜单组织，适合内容较长、跨多个主题的 GNU 工具。常见导航包括：

- `n`：下一个节点；
- `p`：上一个节点；
- `u`：上一级节点；
- `Enter`：跟随当前菜单项或引用；
- `q`：退出。

最小化系统不一定安装所有 Info 文档。`info` 无对应主题时，应回到 `type`、`--help` 和 `man`，而不是把缺少 Info 节点解释为命令不存在。

### ⑤ [操作] 建立本地帮助路由

```text
先执行 type / command -V
│
├─ alias       → 查看 alias 展开，再查真实命令
├─ function    → 查看函数定义，再查函数内部调用对象
├─ builtin     → help <NAME>
└─ external    → <NAME> --help → man [SECTION] <NAME> → info <NAME>

名称未知、只知道功能
└─ apropos / man -k
```

互联网搜索只能在本地证据不足后补充。考试环境可能没有外网，而本地帮助与当前系统版本直接对应，因此它应成为第一证据。

**[Cheatsheet]** `help` 管 Bash builtin；`--help` 管快速语法；`man` 管完整本地参考；`info` 管节点式长文档；不知道名称时不要逐个猜命令，转到 `apropos`。

</section>

<section class="topic operation" id="RHCSA-03-O03" data-kind="operation-topic">

## [操作专题] 把 man page 读成可执行的操作依据

打开 man page 只是入口。真正的能力是能在几十屏内容中迅速回答：我打开的是哪个对象、命令骨架怎样写、哪个参数改变目标状态、配置或数据文件在哪里、下一张相关手册是什么。RHCSA 最常用的 section 是 1、5 和 8，但排错时也应能识别其他 section 的对象类型。

### ① [知识点] man section 是对象分类，不是难度等级

| Section | 主要对象 | 本章判断重点 |
|---:|---|---|
| 1 | 用户可执行命令与 Shell 命令 | 普通命令的调用语法 |
| 2 | 系统调用 | 用户空间调用内核的接口，通常供编程和深度排错 |
| 3 | 库函数 | 程序库接口 |
| 4 | 特殊文件和设备 | 设备或内核接口文件 |
| 5 | 文件格式和配置文件 | 配置语法、字段和文件结构 |
| 6 | 游戏 | RHCSA 很少使用 |
| 7 | 约定、协议和杂项 | 信号、正则表达式、协议、整体概念 |
| 8 | 系统管理命令 | 通常需要管理员关注的管理工具 |
| 9 | 内核例程 | 内核开发接口，RHCSA 很少使用 |

引用手册页时常写成 `passwd(1)`、`passwd(5)`。括号中的数字是 section，不是版本号。

### ② [操作] 用显式 section 消除同名歧义

```bash
man passwd
man 1 passwd
man 5 passwd
```

默认 `man passwd` 按系统配置的 section 顺序选择第一张匹配页，通常进入 `passwd(1)` 命令。需要读取 `/etc/passwd` 文件格式时，应明确执行 `man 5 passwd`。

类似地，任务描述若提到“某配置文件的字段”，往往需要第 5 节；若提到“管理员执行的命令”，通常进入第 8 节。不要只因标题相同就假定页面内容相同。

### ③ [知识点] `SYNOPSIS` 是形式语法，不是可直接复制的固定命令

`SYNOPSIS` 常使用排版和符号表达命令骨架：

- 固定命令名和选项按原样输入；
- `<NAME>`、斜体或大写占位词需要替换为实际值；
- `[ ... ]` 通常表示可选部分；
- `...` 表示前一对象可以重复；
- `|` 常表示多个形式中选择其一；
- 多行 synopsis 可能表示多个合法调用形式。

不同项目的排版习惯可能略有不同，因此还要阅读紧邻的 `DESCRIPTION` 和 `OPTIONS`。不要把方括号、尖括号或省略号机械输入命令行，除非手册明确说明它们是字面字符。

### ④ [操作] 从 `OPTIONS` 提取会改变结果的参数

查参数时至少确认四件事：

```text
参数作用于哪个对象
参数是否必须带值
值的单位或允许形式
它与其他参数能否组合
```

例如，看到 `-f FILE` 时不能只记住 `-f`；还要确认 `FILE` 是输入、输出还是配置路径，能否重复，缺省值是什么。若选项只在某子命令下有效，应沿页面结构进入对应子命令段落。

### ⑤ [操作] 用 `FILES` 和 `SEE ALSO` 扩展证据链

`FILES` 通常列出相关配置、数据、缓存或运行时路径。它能帮助管理员找到下一层对象，但不表示页面列出的每个文件都必然存在，也不表示当前程序正在读取其中所有文件。

`SEE ALSO` 指向相关命令、文件格式、协议或概念页。遇到“命令参数看懂了，但配置字段在哪里”“服务命令和配置文件是什么关系”等问题时，应从这里跳转，而不是回到互联网重新搜索。

典型路线：

```text
man ssh
→ SEE ALSO 中找到 ssh_config(5)
→ man 5 ssh_config

man passwd
→ SEE ALSO 中找到 passwd(5)、shadow(5)
→ 进入文件格式页
```

### ⑥ [操作] 使用分页器进行定向查找

man 通常借助 `less` 一类分页器。高频导航：

| 键 | 作用 |
|---|---|
| `Space` / `PageDown` | 向下翻屏 |
| `b` / `PageUp` | 向上翻屏 |
| `/pattern` | 向下搜索正则模式 |
| `n` | 重复同方向搜索 |
| `N` | 反方向重复搜索 |
| `g` | 页面开头 |
| `G` | 页面末尾 |
| `q` | 退出 |

参数名以连字符开头时，可搜索包含上下文的形式，如 `/--recursive`，也可以先搜索 `OPTIONS` 再在该区域继续定位。搜索按分页器的正则表达式规则工作，特殊字符可能需要转义。

### ⑦ [操作] 利用标准标题快速定位答案

常见标题及其问题边界：

| 标题 | 主要回答 |
|---|---|
| `NAME` | 主题名称和一句用途 |
| `SYNOPSIS` | 合法调用形式 |
| `DESCRIPTION` | 对象和总体语义 |
| `OPTIONS` | 参数语义与组合 |
| `EXAMPLES` | 典型用法，不一定覆盖本机实际状态 |
| `FILES` | 相关路径 |
| `ENVIRONMENT` | 影响行为的环境变量 |
| `EXIT STATUS` | 返回状态含义 |
| `SEE ALSO` | 关联证据入口 |
| `BUGS` | 已知限制 |

并非每张页面都包含全部标题。没有 `FILES` 不代表程序不使用文件；应继续阅读 `DESCRIPTION`、项目文档和关联页面。

### ⑧ [操作] 用 man 自己的帮助学习 man

```bash
man man
man 7 man-pages
```

`man(1)` 解释查找、section、分页和选项；`man-pages(7)` 解释 Linux man page 的章节与书写约定。遇到低频 man 参数时，应按本章方法查询，而不是把所有参数预先背下来。

**[Cheatsheet]** 1 是命令，5 是文件格式，8 是管理命令；同名主题显式写 section；`SYNOPSIS` 看骨架，`OPTIONS` 看参数，`FILES` 找路径，`SEE ALSO` 找下一张证据；页面内用 `/`、`n/N`、`g/G`、`q`。

</section>

<section class="topic operation" id="RHCSA-03-O04" data-kind="operation-topic">

## [操作专题] 不知道命令名时从功能描述发现本地能力

实际任务往往只描述目标：“修改密码过期时间”“列出监听端口”“找出文件由哪个包提供”，而不会告诉你命令名。此时逐个猜命令效率低，也容易被相似名称误导。man 数据库把页面名称、section 和一句描述做成索引，`whatis` 与 `apropos` 分别支持准确主题查询和关键词发现。

### ① [操作] `whatis` 查询已知主题的一行描述

```bash
whatis <TOPIC>
man -f <TOPIC>
```

`whatis` 在手册索引中查找准确主题名称并显示简短描述，常用于确认一个已知名称有哪些 section。它不是任意全文搜索，也不读取命令的当前运行状态。

典型用途：

```bash
whatis passwd
```

若结果同时包含 `passwd(1)` 和 `passwd(5)`，应根据任务对象进入正确 section。

### ② [操作] `apropos` 或 `man -k` 按功能关键词发现主题

```bash
apropos <KEYWORD>
man -k <KEYWORD>
```

两者在 man page 的名称和简短描述索引中匹配关键词，输出通常由三部分组成：

```text
主题名称 (section) - 一句描述
```

最有效的关键词通常来自任务中的稳定名词或动作，而不是整段自然语言。例如任务提到密码过期，可先搜索 `password`、`expiry` 等，再根据描述识别 `chage(1)`、`passwd(1)` 或相关文件格式页。

### ③ [诊断] 空结果不等于系统没有能力

`apropos` 或 `whatis` 没有输出时，按以下顺序判断：

```text
拼写或主题名是否正确
→ 关键词是否过窄或语言不同
→ 目标是否其实是 Bash builtin
→ 对应 man page 是否安装
→ man 数据库索引是否存在或需要刷新
```

man-db 系统使用 `mandb` 建立索引。在软件包刚安装、索引损坏或极简环境中，管理员可检查并重建索引：

```bash
sudo mandb
```

该动作重建手册索引，不安装命令本身。执行前应确认当前问题确实是索引，而不是主题拼写或帮助入口选错。

### ④ [边界] `man -K` 是全文搜索，不是默认第一步

部分 man 实现支持：

```bash
man -K <TEXT>
```

它搜索手册正文，范围比 `apropos` 大，耗时和资源也更高。只有在名称与描述索引无法定位、且确实需要正文关键词时才使用。先用 `apropos` 缩小主题，再阅读候选页通常更快。

### ⑤ [边界] 帮助主题搜索与软件包搜索不可互换

`apropos` 回答“哪些本地手册主题的名称或描述与关键词相关”；`dnf search` 回答“哪些软件包元数据与关键词相关”；`dnf provides` 回答“哪个软件包声明提供指定路径或能力”。知道缺失文件名时，`dnf provides` 比宽泛的关键词搜索更有确定性。

**[Cheatsheet]** 已知准确主题：`whatis`/`man -f`；只知道功能：`apropos`/`man -k`；空结果先查入口、关键词、man page 和索引；正文全文检索 `man -K` 只作后备。

</section>

<section class="topic operation" id="RHCSA-03-O05" data-kind="operation-topic">

## [操作专题] 从已有文件反查本机已安装软件包

当命令已经存在，调查重点常从“它是什么”转向“谁安装了它”。RHEL 使用本地 RPM 数据库记录已安装包及其文件清单。`rpm -qf` 以文件路径为查询键，能把一个现存路径关联到拥有它的已安装包。

### ① [操作] 使用 `rpm -qf` 查询文件所有权

**作用对象：** 本机 RPM 数据库中的已安装包文件记录。

```bash
rpm -qf <ABSOLUTE_PATH>
```

例如：

```bash
rpm -qf /usr/bin/chage
rpm -qf /etc/passwd
```

结果通常包含包名、版本、发行号和架构。应把它解释为：“本机 RPM 数据库记录该路径由这个已安装包拥有。”不要把它扩大为“仓库中只有这个包”或“该文件内容仍与软件包原始内容完全一致”。文件完整性验证属于 RPM 事务章节。

普通查询通常不需要 root 权限，因为它只读取本地数据库。

### ② [操作] 使用绝对路径建立稳定查询键

`rpm -qf` 查询的是路径记录，不是 Shell 命令名称。先通过 `type` 或 `command -v` 确认外部路径，再把路径交给 RPM：

```bash
command -v chage
rpm -qf /usr/bin/chage
```

若 `command -v` 返回的是 builtin 名称、alias 定义或 function 名称，就不能直接把该字符串当作文件路径。需要先确认是否存在对应外部候选，例如：

```bash
type -a test
rpm -qf /usr/bin/test
```

### ③ [诊断] 区分路径不存在、路径存在但未被 RPM 管理、数据库记录异常

稳定流程是先确认目标路径，再查询所有权：

```text
路径或命令名是否正确
→ type/command -v 是否给出外部路径
→ 该路径当前是否存在
→ rpm -qf 是否有所有者
```

管理员手工创建的脚本、从源码安装的程序、应用解压目录和某些运行时生成文件可能不属于任何 RPM 包。此时 `rpm -qf` 没有所有者是有效结论，不应通过随意安装同名包来“修复”。

### ④ [操作] 从包名反查文件清单，完成双向核对

已取得包名后，可以继续：

```bash
rpm -ql <PACKAGE>
```

它列出该已安装包登记的文件。需要只看配置文件或文档时，`rpm -qc`、`rpm -qd` 可提供进一步只读查询，但完整 RPM 查询与事务体系归第 16 章。本章只建立“路径 → 已安装包 → 文件清单”的调查闭环。

### ⑤ [边界] 文件所有权不等于当前 Shell 会执行它

一个包拥有 `/usr/bin/example`，并不能证明当前 `example` 名称一定解析到该路径：同名 alias、function、另一个更靠前的 `PATH` 目录或权限问题都可能改变结果。因此安装层和 Shell 层要分别验证。

**[Cheatsheet]** 先用 `type` 找对象；只有得到外部路径后才用 `rpm -qf`；`rpm -qf` 证明本地所有权，不证明仓库唯一性、文件未被修改或当前 Shell 一定调用它；包的文件清单用 `rpm -ql`。

</section>

<section class="topic operation" id="RHCSA-03-O06" data-kind="operation-topic">

## [操作专题] 从缺失命令或路径反查仓库提供能力

命令不存在时，直接猜包名容易失败：命令名与包名不一定相同，一个包可能提供多个工具，文件也可能由专门的子包提供。DNF 可以根据路径或提供能力查询当前可见软件源中的候选包。本章只进行只读能力查询，不执行安装。

### ① [操作] 已知完整路径时优先按完整路径查询

```bash
dnf provides /usr/bin/<NAME>
dnf provides /path/to/file
```

完整路径最有区分度，因为它同时约束目录和文件名。任务文档、错误日志或其他主机若给出了准确路径，应优先使用它，而不是退化成宽泛关键词。

### ② [操作] 只知道 basename 时使用带引号的通配模式

```bash
dnf provides '*/<NAME>'
```

例如：

```bash
dnf provides '*/semanage'
```

引号用于防止当前 Shell 先在工作目录中展开 `*`。这里借用了第 01 章的引用知识；本章只强调：传给 DNF 的应是完整模式字符串，而不是当前目录提前展开后的多个文件名。

### ③ [输出判断] 一个查询可能返回多个候选

结果可能因架构、版本、仓库、兼容包或多个路径匹配而出现多个候选。选择前记录：

- 包名及版本/发行号；
- 架构；
- 来源仓库；
- 实际匹配的文件路径；
- 当前任务是否要求该架构与仓库。

不要只复制第一行。若候选来自调试、兼容或非目标架构包，应继续比较匹配路径和任务约束。

### ④ [边界] `dnf provides` 证明“可提供”，不证明“已安装”

查询命中后，仍然只能声明：当前 DNF 可见的系统与仓库元数据中，有候选包声明提供目标。它不能单独证明：

- 软件包已经安装；
- 命令位于当前 `PATH`；
- 当前 Shell 没有同名 alias/function；
- 命令具备完成任务所需的配置或权限；
- 仓库配置本身符合考试要求。

安装动作归软件管理章节。未来完成安装后，应分别验证：

```text
rpm -q <PACKAGE>       → 包已安装
rpm -qf <PATH>         → 路径归属
command -v <NAME>      → 当前 Shell 可解析
<NAME> --help / man    → 语法入口
实际状态查询           → 功能终态
```

### ⑤ [诊断] 查询无结果时不要立刻宣布“没有这个包”

按以下顺序推进：

```text
确认命令或文件名拼写
→ 尝试已知完整路径
→ 只知道 basename 时使用带引号的 */name
→ 检查是否选择了错误架构或命令名称
→ 确认当前 DNF 是否有可用仓库元数据
→ 仓库配置问题转交第 17 章
```

本章不以关闭签名检查、强制安装、添加未知第三方仓库或使用 `--allowerasing` 作为默认答案。

### ⑥ [比较] `dnf search` 与 `dnf provides` 的选择

`dnf search <KEYWORD>` 在软件包名称和描述中搜索概念，适合只知道软件类别；`dnf provides <PATH>` 针对明确文件或能力，结论更直接。错误信息已经给出缺失文件时，优先 `provides`；只有完全没有路径线索时才考虑关键词搜索。

**[Cheatsheet]** 完整路径优先；只有 basename 用 `'*/name'`；通配符必须引号保护；多候选看架构、仓库和匹配路径；provides 不是 install，更不是功能验收。

</section>

<section class="topic diagnosis" id="RHCSA-03-D01" data-kind="diagnosis-topic">

## [诊断专题] 当命令、帮助、位置和软件查询结果彼此不一致

本章工具观察的是不同层。诊断目标不是让所有输出变得相同，而是把每条证据放回它所属的层次，并选择下一条最有区分度的查询。下面的链路都从症状开始，避免“多试几个命令”的随机排错。

### ① [诊断] 症状：`command not found`

```text
症状
→ Shell 无法解析名称

当前证据
→ type <NAME>
→ command -v <NAME>

假设
├─ 拼写错误
├─ 当前 PATH 不含外部路径
├─ 程序未安装
├─ 仅在另一个用户或环境中可用
└─ Shell 仍持有旧路径缓存

下一条高区分度证据
→ type -a <NAME>
→ 明确预期路径后查询 dnf provides

最小处理
→ 修正名称/环境；需要安装时转第 16、17 章

再验证
→ command -v、rpm -qf、帮助入口和真实功能分别检查
```

不要在尚未确认对象时修改 `PATH`，也不要从互联网抄一个包名直接安装。

### ② [诊断] 症状：`which` 显示路径，但执行的行为不同

```text
当前证据
→ which 只给出外部位置线索

假设
→ 同名 alias 或 function 优先

下一条证据
→ type <NAME>
→ type -a <NAME>

最小处理
→ 明确使用当前对象，或在确有需要时调用外部绝对路径

再验证
→ command -V <NAME>
```

这不是 `which` 必然错误，而是它没有回答完整的 Bash 解析问题。

### ③ [诊断] 症状：`man <NAME>` 查不到，但命令可以执行

```text
当前证据
→ type <NAME>

假设
├─ 名称是 Bash builtin，应使用 help
├─ man page 未安装
├─ 手册主题名不同
└─ 需要特定 section

下一条证据
→ help <NAME>
→ <NAME> --help
→ whatis / apropos
→ man <SECTION> <TOPIC>
```

最小处理不是安装一切文档，而是先把对象和主题名确认清楚。

### ④ [诊断] 症状：`apropos` 没有结果

```text
当前证据
→ whatis <known-topic>
→ man <known-topic>

假设
├─ 关键词过窄或语言不匹配
├─ 本地没有对应 man page
└─ man 数据库索引缺失或陈旧

下一条证据
→ 更换稳定名词
→ 检查已知页面能否打开
→ 必要时检查/运行 mandb
```

重建索引后再次执行同一 `apropos`，才能证明问题是否位于索引层。

### ⑤ [诊断] 症状：`rpm -qf` 无所有者，但 `dnf provides` 有候选

这两条结果可以同时成立：本机当前路径可能是手工文件、尚未安装的文件甚至目标路径当前不存在；仓库元数据仍可能声明某个候选包会提供它。

```text
下一条证据
→ 确认路径是否真实存在
→ 确认 rpm 查询使用的是否是正确绝对路径
→ 记录 dnf 匹配的实际路径
```

不要把仓库候选倒推成本机所有权。

### ⑥ [诊断] 症状：更新后 Shell 仍尝试旧路径

先执行 `type -a` 和 `command -V`，确认不是 alias/function 或 `PATH` 顺序问题。若仅是 Bash 外部命令哈希缓存，执行 `hash -r` 后重新查询。若目标文件确实不存在，则回到包安装状态调查，而不是反复清缓存。

### ⑦ [安全边界] 不把“能找到帮助”扩大为“可以无调查执行”

帮助页中的破坏性选项、强制选项或覆盖选项仍需结合目标状态。找到 `--force`、`--nodeps`、`--allowerasing` 或其他绕过机制，不代表它们适合作为默认解法。先确定评分对象、已有状态、影响范围和回滚条件。

### ⑧ [工作迁移] 为工单和自动化保留可复核证据

真实工作中，调查记录至少保留：

```text
原始症状和完整名称/路径
当前 Shell 的 type / command 结果
使用的帮助主题和 section
rpm 所有权或 dnf 提供者查询
最终采用的包名、路径和版本边界
后续功能验证入口
```

这样后续人员或自动化 Agent 能从相同证据重建判断，而不是只看到一句“装了某包就好了”。

**[Cheatsheet]** 矛盾输出先分层：Shell 解析、位置线索、本地所有权、仓库提供能力。下一条证据应能排除一类假设；修复后回到同一层复查，再进入下一层验证。

</section>

<section class="topic task" id="RHCSA-03-T01" data-kind="classic-task">

## [经典任务] 在无互联网、禁止安装软件的条件下完成本地能力调查

### 环境

你以普通用户登录一台 RHEL 9 主机，当前交互 Shell 为 Bash。本机可以读取 man page、RPM 数据库和当前启用仓库的 DNF 元数据。任务期间不允许访问互联网，不允许安装、删除或升级软件包，也不允许修改仓库配置。

### 当前状态

管理员准备进行账号维护，但遇到以下未知项：

1. 不确定 `test` 在当前 Shell 中是 builtin、外部命令，还是同时存在多个候选；
2. 不知道 `cd` 的准确语法应从哪里查；
3. 需要阅读 `/etc/passwd` 的文件格式，而不是修改密码的 `passwd` 命令；
4. 只知道要调查“password aging”，不知道具体命令名；
5. 需要证明 `/usr/bin/chage` 由哪个已安装软件包拥有；
6. 当前无法调用 `semanage`，需要确定当前 DNF 元数据中哪个软件包能够提供这个命令。

### 目标终态

提交一份调查记录，针对每个对象写明：

- 使用的命令；
- 选择该入口的原因；
- 应从输出中提取的字段或结论；
- 该证据不能证明什么；
- 若查询无结果，下一条最有区分度的证据。

### 限制条件

- 不把 `which` 作为最终命令类型证据；
- 不凭记忆直接写 `semanage` 的包名；
- 不写死具体包版本、架构或仓库名称；
- `apropos` 无结果时必须调查关键词、man page 和索引；
- `dnf provides` 命中后不得声称软件已经安装；
- 不使用互联网搜索作为第一证据。

### 验收矩阵

| 评分对象 | 必须出现的证据 | 合格判断 |
|---|---|---|
| `test` 对象类型 | `type` 或 `type -a`，辅以 `command -V/-v` | 能区分当前优先对象和同名候选 |
| `cd` 帮助 | `help cd` | 明确 `cd` 是 Bash builtin |
| `/etc/passwd` 格式 | `man 5 passwd` | 明确 section 5 是文件格式 |
| password aging 能力发现 | `apropos` 或 `man -k` | 从名称、section 和描述识别候选主题 |
| `/usr/bin/chage` 所有权 | `rpm -qf /usr/bin/chage` | 只声明本机已安装包所有权 |
| `semanage` 提供者 | `dnf provides '*/semanage'` 或明确完整路径查询 | 记录候选包、架构、仓库和匹配路径，不声明已安装 |
| 失败诊断 | 对空结果给出下一条证据 | 不把空结果直接解释为能力不存在 |

</section>

<div class="page-break"></div>

<section class="topic answer" id="RHCSA-03-A01" data-kind="reference-answer">

## [参考解答] 先确认对象，再沿证据层推进

以下命令是调查骨架。由于本会话没有受控 RHEL 9 虚拟机，答案不编造固定版本、仓库、locale 或完整输出；实际考试中应记录目标主机返回的真实结果。

### ① 确认 `test` 的当前解析对象和所有候选

```bash
type test
type -a test
command -V test
command -v test
```

预期提取：

- `type test`：当前 Bash 最先如何解释 `test`；
- `type -a test`：是否同时存在 builtin 和外部文件候选；
- `command -V test`：可读的详细描述；
- `command -v test`：简洁表示，注意 builtin 可能只返回名称而不是路径。

不能证明：外部候选由哪个包拥有。若需要继续调查，应把 `type -a` 返回的真实外部路径交给 `rpm -qf`。

### ② 为 Bash builtin `cd` 选择帮助入口

```bash
type cd
help cd
```

`type` 先证明对象是 builtin，`help cd` 再读取当前 Bash 版本的语法与选项。不要把 `cd --help` 当作统一、独立的外部程序帮助入口。

### ③ 显式选择 `/etc/passwd` 的文件格式页

```bash
whatis passwd
man 5 passwd
```

`whatis` 用于观察同名主题及 section；`man 5 passwd` 明确进入文件格式页。阅读时至少定位：

```text
NAME        → 页面对象
DESCRIPTION → 文件用途
字段说明     → 每一列的语义
FILES       → 相关路径
SEE ALSO    → shadow(5)、passwd(1) 等关联页
```

`man passwd` 默认进入哪张页面取决于 section 搜索顺序，不能替代显式 section 验收。

### ④ 按功能描述发现 password aging 相关主题

先使用稳定关键词：

```bash
apropos password
# 等价入口
man -k password
```

从输出的“主题名称、section、描述”中筛选与密码过期或 aging 相关的候选，再打开页面，例如：

```bash
man 1 chage
```

若结果过多，可换用 `expiry`、`aging` 等关键词；若完全无结果：

```bash
whatis passwd
man 1 passwd
```

确认已知 man page 正常后，再判断是否需要由管理员检查索引：

```bash
sudo mandb
apropos password
```

只有重建后同一查询恢复，才能把问题归到索引层。

### ⑤ 查询 `/usr/bin/chage` 的本地 RPM 所有权

```bash
rpm -qf /usr/bin/chage
```

记录主机真实返回的包 NEVRA。合格结论是：

> 本机 RPM 数据库记录 `/usr/bin/chage` 由该已安装包拥有。

需要双向核对时：

```bash
rpm -ql <PACKAGE>
```

不能据此声明仓库中只有该包、文件未被修改，或 `chage` 在所有用户环境中都能从 `PATH` 解析。

### ⑥ 查询 `semanage` 的仓库提供能力

先确认当前 Shell 确实无法解析：

```bash
type semanage
command -v semanage
```

只知道 basename 时：

```bash
dnf provides '*/semanage'
```

如果从文档或另一条证据得到准确路径，则优先：

```bash
dnf provides /usr/sbin/semanage
```

从真实输出记录：候选包、版本/发行号、架构、仓库和匹配路径。答案不得凭记忆写死包名，也不得把候选解释为已安装状态。

若无结果，继续检查：拼写、路径模式、架构和仓库元数据可用性。仓库修复或软件安装转第 16、17 章处理。

### ⑦ 汇总分层结论

| 对象 | 证据层 | 允许声明 | 不允许扩大为 |
|---|---|---|---|
| `test` | 当前 Bash 解析 | 当前优先对象及同名候选 | 包所有权或功能健康 |
| `cd` | Bash builtin 帮助 | 当前 Bash 的语法 | 外部程序安装状态 |
| `passwd(5)` | man 文件格式页 | 文件字段和关联路径 | `/etc/passwd` 当前内容无误 |
| `apropos password` | man 索引 | 相关本地手册主题 | 软件包已安装或命令已执行 |
| `rpm -qf` | 本地 RPM 数据库 | 当前路径的已安装包所有权 | 仓库唯一提供者 |
| `dnf provides` | 当前 DNF 元数据 | 候选提供者 | 已安装、可调用或功能完成 |

### ⑧ 典型错误

1. 只执行 `which test`，忽略 builtin；
2. 使用 `man passwd` 却没有证明打开的是 section 5；
3. `apropos` 空结果后直接宣布没有相关命令；
4. 把 `command -v cd` 返回的 `cd` 当成文件路径；
5. 把 `rpm -qf` 和 `dnf provides` 都翻译为“文件来自哪个包”，忽略本地与仓库状态；
6. `dnf provides` 命中后直接写“已经安装”；
7. 未保护 `*/semanage`，让当前 Shell 提前展开通配符；
8. 只证明命令存在，没有为后续真实任务保留功能验证入口。

</section>

<section class="topic summary" id="RHCSA-03-S01" data-kind="chapter-summary">

## [本章收束] 把“不知道”转换成一条可复核的本机调查路径

本章建立的核心路径是：

```text
未知名称或异常行为
→ type / command 确认当前 Shell 对象
→ help / --help / man / info 选择正确帮助源
→ SYNOPSIS / OPTIONS / FILES / SEE ALSO 提取操作依据
→ whatis / apropos 在不知道名称时发现主题
→ rpm -qf 证明本地文件所有权
→ dnf provides 证明仓库提供能力
→ 将每条证据限制在它实际证明的层次
```

最重要的判断边界：

- `type` 证明当前 Shell 怎样解析，不证明包归属；
- `which`、`whereis` 提供位置线索，不取代 Bash 对 alias/function/builtin 的判断；
- `help` 是 builtin 的第一入口，`--help` 是常见短帮助约定，`man` 是完整本地参考，`info` 是节点式补充；
- section 1、5、8 分别常对应命令、文件格式和管理命令；
- `whatis` 查准确主题，`apropos` 按名称与描述发现主题；
- `rpm -qf` 查询已安装包所有权，`dnf provides` 查询当前元数据中的候选提供者；
- 找到语法、找到包、命令成功和真实功能正确，是不同验收层。

工作中遇到陌生工具时，不必先记住答案。只要能稳定选择下一条证据，就能在当前系统上重建可靠答案，并把这条调查路径迁移到后续用户、服务、网络、存储、SELinux 和 Ansible 任务。

</section>
