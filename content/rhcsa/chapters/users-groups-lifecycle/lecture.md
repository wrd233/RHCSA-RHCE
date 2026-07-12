---
title: "第 07 章 用户、组与账号生命周期"
chapter_id: RHCSA-07
exam: RHCSA
part: "第二篇 身份、权限与特权控制"
slug: users-groups-lifecycle
status: content_frozen_for_integration
validation: static
live_test: not_performed
candidate_version: "5.1"
base_commit: "961a29b3af4c07a828078a5de90c221a036546df"
sources:
  - RH124-RHEL9-Ch6
  - RHEL9-RHCSA-current-book
  - RHEL9-Configuring-Basic-System-Settings-Ch7
  - shadow-utils-man-pages
  - glibc-getent-and-coreutils-id-man-pages
  - RHCSA9-Mock
---

<!-- 稳定 Section ID、来源和静态验证信息属于维护层；阅读版不显示。 -->

<div class="cover">
<div class="cover-inner">
<div class="cover-series">RHEL 9 · RHCSA 实操讲义</div>
<div class="cover-number">07</div>
<div class="cover-title">用户、组与账号生命周期</div>
<div class="cover-subtitle">从名称映射到会话凭据：把创建、修改、停用、期限与数据边界放进同一条生命周期链。</div>
<div class="cover-tags"><span>对象模型</span><span>操作语义</span><span>验证</span><span>诊断</span><span>经典任务</span></div>
<div class="cover-note">大字号阅读版</div>
</div>
</div>

<section class="reading-nav">

# 本章阅读导航

**先抓住一条主线：** 本地账号管理不是“执行一条创建或锁定命令”，而是让名称解析、UID/GID、组关系、账号数据库、口令期限、家目录和新会话凭据共同达到可验证终态。

<div class="model-grid">
<div class="model-card"><b>01</b><strong>识别身份对象</strong><span>区分名称、UID/GID、主组与附加组</span></div>
<div class="model-card"><b>02</b><strong>读取数据库状态</strong><span>定位 passwd、shadow、group 与 gshadow</span></div>
<div class="model-card"><b>03</b><strong>建立变更基线</strong><span>用 getent、id、passwd -S 与 chage -l 取证</span></div>
<div class="model-card"><b>04</b><strong>推进生命周期</strong><span>创建、修改、锁定、过期和删除</span></div>
<div class="model-card"><b>05</b><strong>刷新会话身份</strong><span>比较数据库状态与现有进程凭据</span></div>
<div class="model-card"><b>06</b><strong>验证数据边界</strong><span>检查家目录、数字所有权与删除遗留</span></div>
</div>

<div class="nav-columns">
<div class="topic-map">
<h2>专题地图</h2>
<div class="topic-row"><b>知识专题</b><span>从名称到数字身份：用户、组和会话</span></div>
<div class="topic-row"><b>知识专题</b><span>四个本地账号数据库</span></div>
<div class="topic-row"><b>操作专题</b><span>先查询再变更：建立可信基线</span></div>
<div class="topic-row"><b>操作专题</b><span>默认值、skeleton 与精确创建</span></div>
<div class="topic-row"><b>操作专题</b><span>修改用户、组和家目录</span></div>
<div class="topic-row"><b>知识专题</b><span>停用账号的多状态模型</span></div>
<div class="topic-row"><b>操作专题</b><span>su、newgrp 与会话身份</span></div>
<div class="topic-row"><b>诊断专题</b><span>从登录失败或“改了不生效”推进证据</span></div>
<div class="topic-row"><b>经典任务</b><span>精确创建；安全停用并评估删除</span></div>
</div>
<div class="nav-questions">
<h2>阅读时持续回答</h2>
<ol>
<li>当前看到的是名称映射，还是进程实际持有的凭据？</li>
<li>主组和附加组分别记录在哪里？</li>
<li>操作改变的是口令、期限、Shell，还是账号记录？</li>
<li>组变更是否已经进入一个新会话？</li>
<li>家目录字段变化是否伴随数据迁移？</li>
<li>密码锁定、到期、nologin 与删除分别阻止什么？</li>
<li>删除前哪些文件仍由旧 UID/GID 拥有？</li>
<li>当前证据能证明什么，又不能证明什么？</li>
</ol>
<div class="reading-note"><strong>阅读提示：</strong> 每次操作都先判断它改变的是名称映射、数字身份、口令期限、家目录数据还是会话凭据；随后选择能够证明该层终态的证据。</div>
</div>
</div>

</section>

<div class="chapter-kicker">第 07 章 · 正文</div>

服务器上的“用户”并不只是一个可以输入的用户名。系统真正依赖的是名称到 UID/GID 的映射、一个主组与若干附加组、四个本地账号数据库、口令和期限字段、家目录与登录 Shell，以及某个已经运行的进程实际持有的凭据。只观察其中一层，就会得到看似合理却错误的结论：账号已经加入组，旧 Shell 仍没有新组；口令已经锁定，已有会话或非口令认证仍可能存在；用户已经删除，旧 UID 拥有的数据仍留在文件系统中。

本章以“身份对象 → 数据库状态 → 生命周期操作 → 新会话验证 → 数据边界”为主线。先理解名称、数字身份和会话凭据为什么必须分开，再进入创建默认值、用户和组的创建与修改、口令期限、停用与删除；最后用证据链处理“用户不能登录”“组已修改但仍不生效”“账号已删除却留下数字所有者”等问题。

本章只负责本地用户、组和账号生命周期。身份参与文件访问判定的规则留给第 08 章《传统权限、umask 与特殊权限位》；特权授权留给第 10 章《sudo 与最小特权授权》；SSH 密钥认证留给第 20 章《SSH 客户端、服务端与密钥认证》。

::: {.concept-card}
<span class="concept-chip">概念</span> **UID / GID** 是系统使用的数字身份。用户名和组名是名称服务提供的人类可读映射，文件元数据和进程凭据最终都能落到 UID 与 GID。改名通常不改变原 UID，删除后重用 UID 却可能让新账号继承对旧文件的名称解释，因此数字身份的调查贯穿创建、修改和删除。
:::

::: {.concept-card}
<span class="concept-chip">概念</span> **主组与附加组** 描述用户所属组的两个不同层次。每个用户恰好有一个主组，其 GID 位于用户条目中；附加组用于补充成员关系，通常在组数据库的成员字段中表达。`/etc/group` 某组成员列表为空，不代表没有用户把它作为主组。
:::

::: {.concept-card}
<span class="concept-chip">概念</span> **账号数据库** 由 `/etc/passwd`、`/etc/shadow`、`/etc/group` 和 `/etc/gshadow` 共同组成：公开属性与受保护字段被分离保存。理解字段是为了读证据和诊断关联状态，而不是把直接编辑文本文件当作日常管理方法；正常生命周期应由专用命令同时维护关联数据库和锁。
:::

::: {.concept-card}
<span class="concept-chip">概念</span> **认证状态** 不是单一开关。口令字段可用或锁定、账号是否到期、登录 Shell 是否允许交互、认证服务是否接受其他凭据，以及是否已有会话，分别属于不同层次。`passwd -l` 只锁定口令字段，不能被扩大解释为“这个身份在所有入口和所有现有进程中立即消失”。
:::

::: {.concept-card}
<span class="concept-chip">概念</span> **密码期限** 把口令最后修改日、最短和最长期限、警告期、过期后的非活动期与账号到期日分开记录。密码过期要求更新凭据，账号到期限制账号继续使用；二者应分别通过 `passwd -S` 与 `chage -l` 观察，不能用一个日期替代全部状态。
:::

::: {.concept-card}
<span class="concept-chip">概念</span> **当前会话身份** 是进程在会话建立时取得的 UID、主 GID 和附加组集合。管理员修改数据库后，已经运行的 Shell 不会自动刷新全部组凭据。`id USER` 读取名称服务计算出的身份，而目标用户新登录或 `su - USER` 后在会话内运行 `id`，才能证明新凭据已经进入实际进程。
:::

::: {.ops-quick}
<span class="ops-chip">操作语义</span> 以下七组入口覆盖本章最关键的查询、创建、修改、停用、删除和会话验证。先识别命令改变或观察的对象，再记参数。

### `getent` / `id`

**SYNOPSIS**

```bash
getent database [key ...]
id [OPTION]... [USER]
```

通过 NSS 查询账号或组的解析结果，并汇总指定用户或当前进程的数字身份与组凭据。

**重要参数 / 形式**

`getent passwd USER`
: 查询用户条目；结果可能来自本地文件或其他 NSS 身份源。

`getent group GROUP`
: 查询组条目和显式成员；不能单独列出所有把它作为主组的用户。

`id USER`
: 显示名称服务计算出的用户身份。

`id`
: 显示当前进程实际持有的凭据，适合验证新会话。

---

### `useradd`

**SYNOPSIS**

```bash
useradd [options] LOGIN
useradd -D [options]
```

创建本地用户条目，并按显式参数和默认配置决定 UID、组、家目录、Shell、期限与 skeleton 初始化。

**重要参数 / 形式**

`-u UID`
: 指定用户数字身份；创建前检查名称服务和现有文件是否冲突。

`-g GROUP`
: 指定主组；目标组通常应先存在。

`-G G1,G2`
: 指定初始附加组列表。

`-d HOME`
: 设置家目录字段，本身不保证目录被创建。

`-m`
: 创建家目录并复制 skeleton 内容。

`-s SHELL`
: 指定登录 Shell。

---

### `usermod`

**SYNOPSIS**

```bash
usermod [options] LOGIN
```

修改已有本地账号的名称、数字身份、组关系、家目录、Shell、口令字段或账号到期状态。

**重要参数 / 形式**

`-aG GROUP USER`
: 把用户追加到附加组；`-a` 只有与 `-G` 组合才表达追加。

`-G G1,G2 USER`
: 用给定列表替换附加组集合；遗漏已有组会将其移除。

`-L` / `-U`
: 锁定或解锁口令字段；不等于终止已有会话。

`-d HOME -m USER`
: 同时修改家目录字段并请求移动旧家目录内容。

`-l NEW OLD`
: 修改登录名；不会自动改完所有外部引用。

---

### `userdel`

**SYNOPSIS**

```bash
userdel [options] LOGIN
```

删除本地账号记录；是否删除默认家目录和邮件池由参数决定，账号在其他路径中的数据不由命令自动发现。

**重要参数 / 形式**

`userdel USER`
: 删除账号记录，默认保留家目录和其他数据。

`userdel -r USER`
: 同时删除记录中的家目录和邮件池；不代表清理任意挂载点或业务目录。

删除前调查
: 保存旧 UID/GID，并按数字身份查找外部文件。

---

### `groupadd` / `groupmod` / `groupdel`

**SYNOPSIS**

```bash
groupadd [options] GROUP
groupmod [options] GROUP
groupdel [options] GROUP
```

管理本地组的名称和 GID；删除前必须确认没有用户继续把该 GID 作为主组，并调查旧 GID 拥有的数据。

**重要参数 / 形式**

`groupadd -g GID GROUP`
: 使用指定 GID 创建组。

`groupmod -n NEW OLD`
: 修改组名，数字身份保持不变。

`groupmod -g GID GROUP`
: 修改 GID；文件系统中的旧数字所有权需要单独处理。

`groupdel GROUP`
: 删除组；被用户作为主组时通常会被阻止。

---

### `passwd` / `chage`

**SYNOPSIS**

```bash
passwd [options] [LOGIN]
chage [options] LOGIN
```

`passwd` 管理口令字段和快速状态，`chage` 管理密码期限与账号到期日。

**重要参数 / 形式**

`passwd -S USER`
: 查看口令状态摘要；结合现场输出判断，不背诵伪造状态文本。

`passwd -l USER` / `passwd -u USER`
: 锁定或解锁口令字段。

`chage -m MIN -M MAX -W WARN USER`
: 设置最短、最长和警告期限。

`chage -I DAYS USER`
: 设置密码过期后的非活动期。

`chage -E DATE USER`
: 设置账号到期日。

`chage -d 0 USER`
: 要求用户下次使用口令登录时修改密码。

---

### `su` / `newgrp`

**SYNOPSIS**

```bash
su [options] [-] [USER [ARGUMENT...]]
newgrp [-] [GROUP]
```

建立新的用户或组身份 Shell，用于验证数据库变更是否已经进入实际进程凭据。

**重要参数 / 形式**

`su USER`
: 切换用户，但通常保留较多当前环境。

`su - USER`
: 请求登录式环境，更接近一次新的登录会话。

`newgrp GROUP`
: 启动一个以目标组作为当前组的新 Shell；`exit` 返回上一层。

会话内 `id`
: 验证实际 UID、主 GID 与附加组，而不是只看数据库记录。

:::


<section class="topic knowledge" id="RHCSA-07-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 从名称到数字身份：用户、组和会话是什么关系

账号管理最容易出现的误判，是把“用户名存在”当成完整身份。实际上，一个用户条目把名称映射为 UID、主 GID、家目录和登录 Shell；组条目把组名映射为 GID 和显式成员；进程在创建会话时取得一组真实凭据。先分清这三层，后续创建、改名、改组和删除才不会破坏数据归属。

### ① <span class="point-label">[知识点]</span> 用户名和 UID 分别解决可读性与系统身份

用户名用于登录、命令输入和展示；UID 是本地系统识别用户的核心数字。`id`、`ps` 和文件元数据最终都能落到数字身份。UID 0 是 `root`；系统账号与普通账号的默认范围由本机 `/etc/login.defs` 等配置决定，不能只凭习惯猜测现场边界。

账号改名通常不改变 UID，因此原有文件仍由同一个数字身份拥有。相反，删除账号后再把相同 UID 分配给新账号，旧文件会被解释为新账号所有，这正是删除前必须调查数字身份的原因。

### ② <span class="point-label">[知识点]</span> 每个用户只有一个主组，但可有多个附加组

主组 GID 位于用户数据库中。用户新建文件时，默认组所有者通常取自主组，但具体继承与权限规则留给第 08 章《传统权限、umask 与特殊权限位》。附加组用于把用户加入额外的协作或角色集合。

`/etc/group` 的成员列表为空，并不能证明无人属于该组：用户可能通过 `/etc/passwd` 中的主 GID 把它作为主组。因此查询一个用户应优先使用 `id USER`，而不是只查看某一条组记录。

### ③ <span class="point-label">[知识点]</span> 用户私有组是一种默认组织方式，不是数字必须相等的规则

RHEL 普通用户通常会获得一个与用户名同名的用户私有组，并把它作为主组。这种约定便于协作权限设计，但 UID 与 GID 在语义上是两个独立命名空间，不要求数值永远相同。创建共享组时，应先检查组名和 GID 是否冲突，而不是为了“整齐”强行复用数字。

### ④ <span class="point-label">[知识点]</span> 账号数据库与运行进程持有的凭据不是同一个时刻

`id alice` 由当前名称服务查询账号关系；alice 已经打开的 Shell 中运行 `id`，显示的是该进程实际持有的 UID、主 GID 和附加组。管理员执行 `usermod -aG developers alice` 后，数据库立即变化，但旧 Shell 不会自动刷新。验证最终使用身份时必须建立新会话。

### ⑤ <span class="point-label">[知识点]</span> 本地账号只是 NSS 可能返回的一类来源

`getent passwd alice` 和 `getent group developers` 通过系统名称服务查询，结果可能来自本地文件，也可能来自其他配置的身份源。本章的 `useradd`、`usermod` 和 `userdel` 只用于本地账号；看到 `getent` 有结果，不代表应直接用本地工具修改远程目录账号。

::: {.cheatsheet}
**Cheatsheet**  名称便于人读，UID/GID 才是系统身份；主组在用户条目中，附加组在组成员关系中；`id USER` 看数据库解析，用户现有 Shell 中的 `id` 看实际会话；删除或重用数字身份前先调查文件。
:::

</section>

<section class="topic knowledge" id="RHCSA-07-K02" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 四个本地账号数据库：字段如何共同描述一个身份

四个数据库不是四份重复名单，而是把公开属性与受保护信息分开保存。读懂字段的目的不是鼓励手工编辑，而是能够解释 `getent`、`passwd -S`、`chage -l` 的结果，并在账号异常时知道下一条证据在哪里。

### ① <span class="point-label">[知识点]</span> `/etc/passwd` 的七个字段定义账号基本属性

典型结构：

```text
login:password-placeholder:UID:GID:GECOS:home:shell
```

| 字段 | 说明 | 常见判断 |
|---|---|---|
| `login` | 登录名 | 名称必须唯一 |
| `x` | 口令占位 | 实际受保护字段在 shadow 中 |
| `UID` | 用户数字身份 | 删除和重用风险围绕它展开 |
| `GID` | 主组数字身份 | 不等于 `/etc/group` 显式成员列表 |
| `GECOS` | 注释或说明 | 可用 `usermod -c` 修改 |
| `home` | 家目录路径 | 字段变化不等于数据已移动 |
| `shell` | 登录 Shell | `nologin` 只限制正常交互 Shell |

### ② <span class="point-label">[知识点]</span> `/etc/shadow` 把口令状态和期限拆成九个字段

典型结构：

```text
login:password:lastchg:min:max:warn:inactive:expire:reserved
```

- `password`：口令哈希或特殊锁定标记；不要把其前缀固定解释为某一种算法，现场算法受版本和策略影响。
- `lastchg`：上次修改口令距 Unix epoch 的天数。
- `min`、`max`、`warn`：最短期限、最长期限、提前警告天数。
- `inactive`：口令过期后允许延迟多少天，之后账号因口令失效而不可用。
- `expire`：账号到期日，与“口令到期日”不是同一个字段。

`passwd -S USER` 适合快速查看口令状态；`chage -l USER` 更适合查看期限。二者互补，不能只看一条输出。

### ③ <span class="point-label">[知识点]</span> `/etc/group` 的四个字段定义组和显式成员

典型结构：

```text
group:password-placeholder:GID:member1,member2
```

最后一个字段主要列出附加成员。某用户把该组作为主组时，通常不会因此自动出现在成员列表中。组口令机制在现代系统中很少作为推荐授权方式，本章只识别字段，不把共享组口令作为常规方案。

### ④ <span class="point-label">[知识点]</span> `/etc/gshadow` 保存受保护的组管理信息

典型结构：

```text
group:encrypted-password:administrators:members
```

它可以表达组管理员和成员，并与 `/etc/group` 配合。普通 RHCSA 用户和组任务主要通过 `useradd`、`usermod`、`groupadd` 等工具完成；直接维护组管理员或组口令不是本章经典任务的主线。

### ⑤ <span class="point-label">[知识点]</span> 专用工具同时维护关联文件和锁，不应默认手工编辑

直接编辑可能造成 passwd 与 shadow、group 与 gshadow 不一致，也可能绕过文件锁和字段校验。普通生命周期操作使用专用命令；只有在系统恢复等受控场景下才考虑 `vipw`、`vigr` 等安全编辑入口，并且那属于更高级的恢复边界。

::: {.cheatsheet}
**Cheatsheet**  passwd 管公开属性，shadow 管口令与期限；group 管 GID 和显式成员，gshadow 管受保护的组管理字段；主组不能只靠 group 成员列表判断；正常管理用专用命令，不直接改文本数据库。
:::

</section>

<section class="topic operation" id="RHCSA-07-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 先查询再变更：建立账号与组的可信基线

创建或修改前必须先回答：名称是否已被解析、目标 UID/GID 是否已占用、账号当前属于哪些组、口令和期限处于什么状态、当前会话是否陈旧。查询顺序应从无副作用的名称服务证据开始，再进入受保护字段和数据路径。

### ① <span class="point-label">[查询]</span> 用 `getent` 查询名称服务中的用户和组

**作用对象：** 系统 NSS 配置能够解析的数据库。

**基本形式：**

```bash
getent passwd alice
getent group developers
getent passwd 2401
getent group 4200
```

按名称和按数字都无结果，才说明在当前名称服务视图中没有冲突。`grep '^alice:' /etc/passwd` 只能证明本地文件中是否有行，不能替代 NSS 查询。

### ② <span class="point-label">[查询]</span> 用 `id` 汇总用户身份，并区分指定用户与当前会话

```bash
id alice             # 查询名称服务计算出的 alice 身份
id                    # 查看当前进程实际持有的身份
id -u alice
id -g alice
id -G alice
id -nG alice
```

修改组后，管理员侧 `id alice` 已显示新组，而用户旧 Shell 中 `id` 未显示，这是会话尚未刷新，不是 `usermod` 必然失败。

### ③ <span class="point-label">[查询]</span> 用 `passwd -S` 和 `chage -l` 分别查看口令与期限

```bash
passwd -S alice
chage -l alice
```

`passwd -S` 的状态字样可能随实现和本地化不同，重点判断“可用、锁定、无口令”以及日期字段，不在静态讲义中伪造固定输出。`chage -l` 用于核对上次修改、最短/最大期限、警告、失效和账号到期。

### ④ <span class="point-label">[调查]</span> 记录家目录和数字所有权基线

```bash
getent passwd alice
stat -c 'path=%n uid=%u gid=%g owner=%U group=%G' /srv/home/alice
find /srv -xdev -uid 2401 -print
```

修改 UID、移动家目录或删除账号前，至少记录旧 UID/GID、家目录路径和账号在目标业务路径中的文件。`find /` 可能成本很高，真实工作中应按挂载点和业务范围分批调查。

### ⑤ <span class="point-label">[查询]</span> 使用帮助入口确认现场工具语义

```bash
man useradd
man usermod
man userdel
man groupadd
man groupmod
man groupdel
man passwd
man chage
man getent
```

课程给出核心路径，man page 用于核对现场版本的参数、默认行为和限制。

::: {.cheatsheet}
**Cheatsheet**  `getent` 查解析，`id USER` 查数据库身份，当前 Shell 的 `id` 查会话凭据；`passwd -S` 查口令状态，`chage -l` 查期限；变更 UID/GID 或删除前记录数字身份和文件清单。
:::

</section>

<section class="topic operation" id="RHCSA-07-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> `useradd` 默认值与 skeleton：新账号从哪里继承初始状态

`useradd` 不是只把一行追加到 `/etc/passwd`。它会合并显式参数、系统默认值和 skeleton 内容，并更新多个数据库。考试题需要确定终态时，应把关键属性写成显式参数；真实工作修改全局默认值时，要清楚它只影响后续创建。

### ① <span class="point-label">[操作]</span> 用 `useradd -D` 查看可管理的默认项

```bash
useradd -D
```

常见项目包括默认组、家目录基路径、非活动期、到期日、Shell、skeleton 目录和是否创建邮件池。输出以现场版本为准。`useradd -D -s /bin/bash` 等形式可以修改部分默认值，但不代表所有创建策略都由该命令管理。

### ② <span class="point-label">[知识点]</span> `/etc/default/useradd` 与 `/etc/login.defs` 职责不同

- `/etc/default/useradd`：`useradd` 自身的默认属性，例如家目录基路径、默认 Shell、skeleton 目录等。
- `/etc/login.defs`：UID/GID 范围、系统账号范围、默认口令期限、家目录创建策略等多项系统级默认。

命令行参数优先表达当前账号目标。修改这些配置不会回溯更改现有账号；现有用户要用 `usermod`、`passwd` 或 `chage` 单独处理。

### ③ <span class="point-label">[操作]</span> `/etc/skel` 只在创建家目录时复制初始内容

```bash
ls -la /etc/skel
useradd -m -k /etc/skel alice
```

隐藏文件同样属于 skeleton 内容。`-k` 需要与创建家目录的操作配合。修改 `/etc/skel` 不会自动同步既有用户家目录。

### ④ <span class="point-label">[边界]</span> 系统账号与普通账号的默认行为不同

`useradd -r service1` 从系统账号范围选择 UID，并通常不应假设会自动创建家目录。服务账号是否需要家目录、Shell 或数据目录必须由服务设计决定；不要为了“能登录测试”给服务账号默认分配交互式 Shell。

### ⑤ <span class="point-label">[操作]</span> 用显式参数避免依赖未知默认值

考试题指定家目录、Shell、UID、主组和期限时，建议显式写出：

```bash
useradd -u 2401 -g ops -G developers,audit \
  -d /srv/home/lina -m -s /bin/bash \
  -e 2030-12-31 lina
```

命令只是请求；之后仍要分别验证账号字段、组关系、家目录和期限。

::: {.cheatsheet}
**Cheatsheet**  参数覆盖默认；`useradd -D` 只展示部分默认；`/etc/login.defs` 影响后续创建，不回溯；`/etc/skel` 只有创建家目录时才复制；目标明确时用 `-m` 等显式参数。
:::

</section>

<section class="topic operation" id="RHCSA-07-O03" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 创建精确的用户与组终态

稳定的创建流程不是先运行 `useradd` 再看缺什么，而是先确定组、数字身份、家目录、Shell、附加组和期限，再按依赖顺序创建。组必须先存在，附加组列表必须完整，口令状态和首次登录策略要单独设置。

### ① <span class="point-label">[操作]</span> 创建普通组或指定 GID 的组

```bash
groupadd ops
groupadd -g 4200 ops
groupadd -r appsvc
```

`-g` 指定 GID；`-r` 创建系统组。创建前用 `getent group NAME` 和 `getent group GID` 检查名称与数字冲突。

### ② <span class="point-label">[操作]</span> 组合 `useradd` 的身份参数

| 参数 | 作用 |
|---|---|
| `-u UID` | 指定 UID |
| `-g GROUP` | 指定主组，组必须已存在 |
| `-G G1,G2` | 指定附加组列表 |
| `-c COMMENT` | 账号说明 |
| `-s SHELL` | 登录 Shell |

```bash
useradd -u 2401 -g ops -G developers,audit \
  -c 'Operations trainee' -s /bin/bash lina
```

### ③ <span class="point-label">[操作]</span> 明确家目录是否创建及其位置

| 参数 | 作用 |
|---|---|
| `-d PATH` | 设置家目录字段 |
| `-m` | 创建家目录并复制 skeleton |
| `-M` | 明确不创建家目录 |
| `-k DIR` | 指定 skeleton 目录，配合 `-m` |

仅有 `-d` 不应被理解为“一定搬入数据”；创建任务中使用 `-d PATH -m` 才能同时表达字段和目录。

### ④ <span class="point-label">[操作]</span> 设置账号到期和口令失效期

```bash
useradd -e 2030-12-31 -f 5 lina
```

`-e` 设置账号到期日；`-f` 设置口令过期后多少天转为失效。它们不是同一个时间点。更完整的期限策略通常在创建后用 `chage` 设置并验证。

### ⑤ <span class="point-label">[操作]</span> 设置初始口令并强制下次修改

```bash
passwd lina
chage -d 0 lina
```

交互式 `passwd` 避免把明文口令写入命令历史。模拟题中可能出现 RHEL 扩展 `passwd --stdin`，但它不应成为真实运维默认示范。

### ⑥ <span class="point-label">[验证]</span> 按对象分层验收

```bash
getent passwd lina
getent group ops
getent group developers
getent group audit
id lina
passwd -S lina
chage -l lina
stat /srv/home/lina
su - lina -c 'id'
```

最后一条建立新会话，验证实际取得的 UID、主组和附加组。若目标账号被要求下次修改口令，非交互式 `su -c` 可能受期限策略影响，应根据任务选择验证时机。

::: {.cheatsheet}
**Cheatsheet**  先组后用户；`-g` 主组、`-G` 附加组；`-d` 设置字段、`-m` 创建目录；`-e` 账号到期、`-f` 口令过期后的失效期；口令和期限要单独设置并验证。
:::

</section>

<section class="topic operation" id="RHCSA-07-O04" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 修改账号：名称、UID、组、家目录和 Shell 不能混成一次“改用户”

账号修改往往影响不同对象。改名主要改变名称映射；改 UID 会改变数字身份；改家目录字段不一定移动数据；改组关系需要新会话生效。每次变更都应写清作用对象和数据边界，避免把一个参数的成功扩大为完整迁移。

### ① <span class="point-label">[操作]</span> 修改登录名，但不要假设其他名称自动同步

```bash
usermod -l lina2 lina
```

这会修改登录名。它不会自动保证家目录路径、邮件别名、应用配置、计划任务说明或同名私有组都按新名称迁移。若目标还要求调整家目录和组名，应作为独立步骤执行并分别验证。

### ② <span class="point-label">[操作]</span> 修改 UID 前先调查旧数字拥有的数据

```bash
old_uid=$(id -u lina2)
find /srv -xdev -uid "$old_uid" -print
usermod -u 2501 lina2
```

工具可能处理家目录中的一部分所有权，但账号在其他文件系统、共享目录、备份或应用数据库中的数字引用必须另行调查。修改后按新旧 UID 再查一次，不能只看 `id`。

### ③ <span class="point-label">[操作]</span> 正确区分附加组替换和追加

```bash
usermod -G developers,audit lina2       # 设为这一完整列表
usermod -aG oncall lina2                # 在现有列表上追加
```

漏掉 `-a` 会把未列出的附加组移除。需要移除某个组时，应先得到完整目标列表，再用 `-G` 设置终态，而不是随意拼接命令。

### ④ <span class="point-label">[操作]</span> 主组与附加组使用不同参数

```bash
usermod -g ops lina2
usermod -aG audit lina2
```

`-g` 改主组；`-G` 管附加组。修改后用 `id lina2` 查看数据库结果，并让用户在新会话中运行 `id` 验证实际凭据。

### ⑤ <span class="point-label">[操作]</span> 修改家目录字段与移动数据是两个语义

```bash
usermod -d /srv/home/lina2 lina2        # 只设置新路径
usermod -d /srv/home/lina2 -m lina2     # 设置路径并请求移动内容
```

移动前检查目标路径是否存在、容量、挂载点和业务占用。跨文件系统、SELinux 上下文和正在运行的用户进程可能使真实迁移更复杂；本章记录这些为后续 live test 项，不以静态命令保证所有现场成功。

### ⑥ <span class="point-label">[操作]</span> 修改登录 Shell 并识别边界

```bash
usermod -s /bin/bash lina2
usermod -s /sbin/nologin service1
```

`nologin` 阻止正常交互式登录 Shell，但不删除账号，不终止已有进程，也不能替代对其他认证和服务访问路径的调查。

::: {.cheatsheet}
**Cheatsheet**  `-l` 改登录名，不等于完成全局改名；`-u` 改数字身份，外部数据要查；`-G` 替换、`-aG` 追加；`-d` 改字段、`-d -m` 请求搬家；组和 Shell 变化要在新会话验证。
:::

</section>

<section class="topic operation" id="RHCSA-07-O05" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 组账号生命周期：创建、改名、改 GID 与删除

组的名称、GID、显式成员和“被哪些用户作为主组”是四个不同问题。`getent group` 能看到组记录和显式成员，却不能直接列出所有以它为主组的用户；删除组前必须补上这一层调查。

### ① <span class="point-label">[操作]</span> 创建组并验证名称与数字

```bash
getent group ops
groupadd -g 4200 ops
getent group ops
```

不要用命令成功替代验证。若指定 GID，继续用 `getent group 4200` 确认数字映射唯一。

### ② <span class="point-label">[操作]</span> 修改组名

```bash
groupmod -n operations ops
```

改名主要改变名称映射，不改变 GID。文件仍保存原 GID，因此名称展示会随映射变化。引用旧组名的 sudoers、应用配置或脚本不会自动全部更新；sudo 规则本身归第 10 章，本章只指出依赖调查。

### ③ <span class="point-label">[操作]</span> 修改 GID 前调查数字所有权

```bash
old_gid=$(getent group operations | cut -d: -f3)
find /srv -xdev -gid "$old_gid" -print
groupmod -g 4300 operations
```

`groupmod -g` 改的是组数据库的数字映射。旧 GID 拥有的外部文件不应假设全部自动变更，修改后要按旧 GID 和新 GID 重新调查。

### ④ <span class="point-label">[诊断]</span> 找出哪些用户把组作为主组

```bash
gid=$(getent group operations | cut -d: -f3)
getent passwd | awk -F: -v gid="$gid" '$4 == gid {print $1}'
```

`groupdel` 在组仍是某个用户主组时会拒绝。先为这些用户指定新的主组，再尝试删除。

### ⑤ <span class="point-label">[操作]</span> 删除组并确认遗留数据

```bash
groupdel operations
getent group operations
find /srv -xdev -gid 4300 -print
```

组记录消失不代表旧 GID 的文件已处理。要根据业务要求迁移、重新归组或保留审计记录。

::: {.cheatsheet}
**Cheatsheet**  组名与 GID分开；`groupmod -n` 改名，`groupmod -g` 改数字；`getent group` 不会完整展示主组用户；`groupdel` 前查主组引用和旧 GID 文件。
:::

</section>

<section class="topic operation" id="RHCSA-07-O06" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 口令状态与账号期限：`passwd` 和 `chage` 各回答什么

“用户不能登录”可能来自口令锁定、没有有效口令、口令已过期并超过失效期、账号已到期，或登录 Shell 被禁止。把这些状态分开，才能选择最小修复，而不是反复重置口令。

### ① <span class="point-label">[操作]</span> 设置口令并查看状态

```bash
passwd alice
passwd -S alice
```

普通用户通常只能修改自己的口令，root 可以管理任意本地账号。输出中的状态标记应结合现场帮助解释，不在静态教材中依赖一份固定本地化文本。

### ② <span class="point-label">[操作]</span> 锁定和解锁口令

```bash
passwd -l alice
passwd -u alice
# 或使用 usermod -L / usermod -U 管理口令字段
```

锁定通常通过在口令哈希前加入不可匹配标记来阻止口令认证。它不保证禁用 SSH 公钥、其他认证机制、已有会话或服务进程。解锁前先确认账号确实存在可用口令，避免把无口令账号变成意外状态。

### ③ <span class="point-label">[操作]</span> 设置口令期限

```bash
chage -m 2 -M 45 -W 7 -I 5 alice
```

| 参数 | 含义 |
|---|---|
| `-m` | 两次修改之间的最短天数 |
| `-M` | 口令最大有效天数 |
| `-W` | 到期前警告天数 |
| `-I` | 口令到期后再过多少天使账号因口令失效 |

### ④ <span class="point-label">[操作]</span> 设置账号到期日

```bash
chage -E 2030-12-31 alice
chage -l alice
```

账号到期日与口令最大期限独立。一个账号可以有尚未到期的口令，但账号整体已到期；也可以账号没有固定到期日，但口令需要周期更换。

### ⑤ <span class="point-label">[操作]</span> 强制下次登录修改口令

```bash
chage -d 0 alice
```

这会把上次修改日设置为需要立即更新的状态。启用后应在合适的交互登录路径验证；非交互命令可能因必须改口令而失败，这不是服务故障。

### ⑥ <span class="point-label">[知识点]</span> `/etc/login.defs` 的默认期限只影响后续创建

`PASS_MIN_DAYS`、`PASS_MAX_DAYS` 和 `PASS_WARN_AGE` 等默认值不会自动重写现有 shadow 条目。修改全局策略后，应分别处理既有账号并用 `chage -l` 验证。

::: {.cheatsheet}
**Cheatsheet**  `passwd -S` 看口令状态，`chage -l` 看期限；锁口令不等于完全停用账号；`-M/-m/-W/-I` 管密码生命周期，`-E` 管账号到期，`-d 0` 强制下次修改。
:::

</section>

<section class="topic knowledge" id="RHCSA-07-K03" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 停用账号不是一个开关：密码锁定、账号到期、Shell 与已有会话

“停用用户”必须先翻译成具体终态。是只禁止口令登录，还是禁止所有新的登录？是否允许服务继续以该 UID 运行？已有 Shell 和进程是否需要另行处置？数据要保留还是删除？不同机制作用于不同层，不能用一个命令代替全部答案。

### ① <span class="point-label">[比较]</span> 密码锁定只针对口令字段

`passwd -l` 或 `usermod -L` 锁定口令认证。它适合在不删除账号和数据的情况下阻止密码使用，但不应被描述为“用户从此不能通过任何方式访问系统”。SSH 密钥属于第 20 章，当前只记住这一边界。

### ② <span class="point-label">[比较]</span> 账号到期限制新的账号使用

`chage -E DATE` 或 `usermod -e DATE` 设置账号到期。需要立即使账号过期时，应依据现场 man page 选择明确的过去日期或工具推荐值，并用 `chage -l` 验证。账号到期不会自动结束已经运行的进程。

### ③ <span class="point-label">[比较]</span> `nologin` 控制正常交互式 Shell

把 Shell 设置为 `/sbin/nologin` 常用于不需要交互登录的服务账号。它不是数据删除机制，也不阻止 systemd 以该用户启动服务进程。是否影响特定协议取决于该协议是否真正调用登录 Shell。

### ④ <span class="point-label">[边界]</span> 已有会话和进程需要独立调查

锁定、过期或改 Shell 后，使用 `who`、`w`、`loginctl` 和进程查询确认是否仍有会话或进程。如何安全终止进程归第 11 章；本章只要求管理员不要声称账号状态变化已经清除了运行实例。

### ⑤ <span class="point-label">[决策]</span> 停用优先保留可审计身份，再决定删除

离职或临时停用通常先记录 UID/GID、组、家目录和数据清单，再锁定口令、设置到期，并保留账号记录以避免数字身份失去名称解释。删除应在数据移交和审批后进行，而不是停用的默认第一步。

::: {.cheatsheet}
**Cheatsheet**  锁口令、过期账号、`nologin` 和删除作用层不同；任何一种都不会自动终止已有进程；停用先保留证据和数字身份，删除要等数据边界明确。
:::

</section>

<section class="topic operation" id="RHCSA-07-O07" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 当前会话身份变化：`su`、`su -` 与 `newgrp`

管理员经常在数据库正确时仍看到功能失败，原因是测试发生在旧会话。会话工具的价值不是“看起来换了提示符”，而是建立新的进程凭据和环境，再用 `id`、`pwd`、`env` 证明实际状态。

### ① <span class="point-label">[操作]</span> `su USER` 建立目标用户 Shell，但保留较多当前环境

```bash
su alice
id
pwd
```

不带 `-` 的 `su` 主要改变用户身份，环境和工作目录可能保留较多原会话内容。它适合观察身份差异，但不能假设完全模拟正常登录。

### ② <span class="point-label">[操作]</span> `su - USER` 请求登录式环境

```bash
su - alice
id
pwd
printf '%s\n' "$HOME" "$SHELL" "$PATH"
```

`su -` 通常切换到目标家目录并建立登录式环境。具体变量由 util-linux、PAM 和系统配置共同影响，因此最终以会话内证据为准。

### ③ <span class="point-label">[验证]</span> 组变更后用新会话确认实际附加组

```bash
id alice
su - alice -c 'id'
```

第一条确认数据库解析，第二条确认新会话取得的凭据。若二者仍不同，再调查 NSS 缓存、PAM 或远程身份源，而不是重复执行 `usermod`。

### ④ <span class="point-label">[操作]</span> `newgrp GROUP` 在新 Shell 中切换当前主组

```bash
id
newgrp developers
id
exit
```

用户必须有资格使用目标组。`newgrp` 启动新的 Shell，并把该 Shell 的主组切换为目标组；退出后返回上层会话。它不会永久改写 `/etc/passwd` 中的默认主组。

### ⑤ <span class="point-label">[边界]</span> Shell 嵌套和测试完成后的恢复

连续使用 `su` 和 `newgrp` 会产生嵌套 Shell。测试后使用 `exit` 一层层返回，并再次运行 `id` 确认当前身份。不要在不清楚所处 Shell 层级时执行破坏性管理命令。

::: {.cheatsheet}
**Cheatsheet**  `su` 改身份但可能保留环境，`su -` 更接近登录会话；数据库 `id USER` 与会话内 `id` 分别验证；`newgrp` 临时切换新 Shell 的主组，`exit` 返回。
:::

</section>

<section class="topic operation" id="RHCSA-07-O08" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 删除用户和组：账号记录、家目录与其他数据的边界

删除是账号生命周期中风险最高的操作，因为名称记录消失后，文件仍保留数字 UID/GID。`userdel -r` 的作用范围有限，不能代替全系统数据调查；组删除也不会自动重写旧 GID 的所有文件。

### ① <span class="point-label">[操作]</span> `userdel USER` 只删除账号记录，不默认删除家目录

```bash
userdel alice
```

执行前记录 UID、主组、附加组、家目录和数据清单。账号删除后，原文件可能显示数字所有者或无人拥有状态。

### ② <span class="point-label">[操作]</span> `userdel -r USER` 删除默认家目录和邮件池，但不是全盘清理

```bash
userdel -r alice
```

它主要处理账号数据库、用户家目录和邮件池。用户在 `/srv`、其他挂载点、共享存储和应用目录中的文件需要单独处理。不得把 `-r` 描述成“删除该用户所有数据”。

### ③ <span class="point-label">[调查]</span> 删除前按数字 UID/GID 查找数据

```bash
uid=$(id -u alice)
gid=$(id -g alice)
find /home /srv -xdev \( -uid "$uid" -o -gid "$gid" \) -print
```

真实系统应按挂载点和业务目录扩展范围，记录结果并决定归档、移交、重新所有或保留。

### ④ <span class="point-label">[验证]</span> 删除后查找无名称解释的数据

```bash
getent passwd alice
find /home /srv -xdev \( -nouser -o -nogroup \) -print
```

`-nouser` 与 `-nogroup` 是事后审计入口，不是自动删除清单。不要在没有审批的情况下把匹配结果直接交给 `rm`。

### ⑤ <span class="point-label">[边界]</span> 避免 UID/GID 过早重用

新账号若取得旧 UID，会立即被解释为旧文件的所有者。停用阶段保留账号记录、删除阶段保留数字清单、创建阶段检查数字冲突，是防止信息泄漏的三道边界。

### ⑥ <span class="point-label">[操作]</span> 用户私有组是否删除必须重新查询

`userdel` 对同名用户私有组的处理受组状态和配置影响。执行后使用 `getent group USER` 核对；若组仍存在，再确认是否有其他成员、是否作为其他用户主组，以及旧 GID 文件是否已处理，最后才决定 `groupdel`。

::: {.cheatsheet}
**Cheatsheet**  `userdel` 删账号不删家目录；`-r` 也不覆盖任意外部数据；删除前按 UID/GID 查，删除后用 `-nouser/-nogroup` 审计；不要过早重用数字身份；同名私有组要重新查询。
:::

</section>

<section class="topic diagnosis" id="RHCSA-07-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 从“用户不能登录”或“改了仍不生效”推进到最小修复

账号故障不能从重置口令开始。先确定账号是否被解析，再分别检查口令、期限、Shell、组和会话。每一步都应选择能排除一类假设的证据，避免把多种状态揉成一句“账号有问题”。

### ① <span class="point-label">[诊断]</span> 账号存在但无法登录

```text
症状：用户报告认证失败
→ getent passwd USER：账号是否解析，Shell 与家目录是什么
→ passwd -S USER：口令是否锁定或未设置
→ chage -l USER：口令和账号是否到期
→ 检查目标访问方式是否使用登录 Shell
→ 最小修复：只修改实际异常的字段
→ 建立新会话再验证
```

若口令可用、期限正常、Shell 正常，再进入具体认证服务日志；SSH 的密钥和服务端配置归第 20 章。

### ② <span class="point-label">[诊断]</span> 已把用户加入组，但访问仍失败

```text
当前证据：id USER 已显示新组
假设 A：用户仍在旧会话
下一条证据：让用户在当前 Shell 运行 id
最小修复：重新登录或建立新 su 会话
再验证：新会话 id + 目标功能测试
```

若新会话也没有该组，检查 `getent group`、NSS 来源和 `usermod -aG` 是否作用于本地账号。

### ③ <span class="point-label">[诊断]</span> 改了家目录，但登录后仍到旧位置或没有数据

```text
getent passwd USER        # 字段是否已改
stat OLD NEW              # 目录是否存在，数据是否移动
su - USER -c 'pwd; id'    # 新登录式会话看到什么
```

字段正确但新目录无数据，通常说明只使用了 `-d` 而没有搬迁，或移动过程失败。先补齐数据，再检查权限和 SELinux；权限细节归后续章节。

### ④ <span class="point-label">[诊断]</span> `groupdel` 报组是某用户主组

```bash
gid=$(getent group GROUP | cut -d: -f3)
getent passwd | awk -F: -v gid="$gid" '$4 == gid {print $1}'
```

为列出的用户选择正确新主组，逐个 `usermod -g NEWGROUP USER`，验证后再删除。不要用强制参数绕过身份关系。

### ⑤ <span class="point-label">[诊断]</span> 删除账号后目录显示数字所有者

记录数字 UID/GID，查找相关文件，确认是否应归档、移交或重新分配。若尚未重用 UID，可以在受控情况下临时重建相同数字的账号帮助恢复名称解释，但这属于恢复决策，不能在未调查时直接执行。

### ⑥ <span class="point-label">[诊断]</span> 锁定账号后用户仍有活动

先区分活动类型：已有 Shell、已有进程、SSH 密钥新登录、服务账号进程或其他协议。锁口令只能排除密码认证。根据目标分别处理账号到期、访问服务配置和运行进程；不要把一个层的修复扩大为所有层都已关闭。

::: {.cheatsheet}
**Cheatsheet**  登录失败按“解析→口令→期限→Shell→具体认证服务”调查；组变更要比较数据库与旧会话；家目录字段和数据分开；组删除先查主组引用；锁口令后仍活动先识别访问类型。
:::

</section>

<section class="topic task" id="RHCSA-07-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 创建指定 UID、组、家目录和期限的项目账号

### 环境与当前状态

- `developers` 与 `audit` 组已经存在。
- `/srv/home` 已存在，`/etc/skel/.company-profile` 已准备。
- `ops` 组和 `lina` 用户尚不存在。
- 系统中可能已有自定义 UID/GID，不能假设 `2401` 和 `4200` 一定空闲。
- 当前无可由本会话控制的 RHEL 9 VM，以下为推荐静态操作与验证路径。

### 目标终态

1. 创建组 `ops`，GID 为 `4200`。
2. 创建用户 `lina`，UID 为 `2401`。
3. `lina` 的主组为 `ops`，附加组为 `developers,audit`。
4. 家目录为 `/srv/home/lina`，实际创建并复制 skeleton 内容。
5. 登录 Shell 为 `/bin/bash`。
6. 账号到期日为 `2030-12-31`。
7. 口令最短期限 2 天、最长期限 45 天、提前 7 天警告、过期后 5 天失效。
8. 设置题目提供的临时口令，并要求下次交互登录时修改。

### 限制条件

- 不直接编辑四个账号数据库。
- 不使用非唯一 UID/GID 绕过冲突。
- 不用 `-G` 破坏题目未要求移除的既有组；本任务为新账号，可一次给出完整附加组列表。
- 不把命令成功或单条 `id` 输出扩大为全部终态正确。
- 不在命令行明文写出临时口令。

### 验收证据

| 层次 | 证据 |
|---|---|
| 组名称与 GID | `getent group ops` |
| 用户字段 | `getent passwd lina` |
| UID、主组、附加组 | `id lina` |
| 家目录与 skeleton | `stat /srv/home/lina`、检查 `.company-profile` |
| 口令状态 | `passwd -S lina` |
| 期限 | `chage -l lina` |
| 新会话身份 | 在允许的验证时机执行 `su - lina` 后 `id` |

</section>

<div class="page-break"></div>

<section class="topic answer" id="RHCSA-07-A01" data-kind="reference-answer">

## <span class="topic-label">[参考解答]</span> 创建精确项目账号

### ① 调查名称与数字冲突

```bash
getent group ops
getent group 4200
getent passwd lina
getent passwd 2401
getent group developers
getent group audit
```

预期：`ops`、`4200`、`lina`、`2401` 没有现存映射；两个附加组存在。任何冲突都应先停下并按题目调整，不使用非唯一参数强行创建。

### ② 创建组

```bash
groupadd -g 4200 ops
getent group ops
```

验证组名与 GID，而不是只看退出码。

### ③ 创建用户及家目录

```bash
useradd -u 2401 -g ops -G developers,audit \
  -d /srv/home/lina -m -s /bin/bash \
  -e 2030-12-31 lina
```

关键参数：

- `-u 2401`：指定 UID；
- `-g ops`：设置主组；
- `-G developers,audit`：设置完整附加组列表；
- `-d ... -m`：同时设置字段并创建目录；
- `-s /bin/bash`：设置登录 Shell；
- `-e`：设置账号到期日。

### ④ 设置口令与期限

```bash
passwd lina
chage -m 2 -M 45 -W 7 -I 5 lina
chage -d 0 lina
```

`passwd` 交互输入题目给定的临时口令。`chage -d 0` 会影响后续交互登录，因此应在完成无需登录的静态验证后再设置，或根据考场操作顺序安排。

### ⑤ 分层验证

```bash
getent passwd lina
getent group ops
getent group developers
getent group audit
id lina
passwd -S lina
chage -l lina
stat -c '%n %u:%g %U:%G' /srv/home/lina
ls -la /srv/home/lina
```

重点判断：

- passwd 条目中的 UID、主 GID、家目录和 Shell；
- `id` 中的主组与两个附加组；
- 家目录确实存在并包含 `.company-profile`；
- `chage -l` 中的最短、最大、警告、失效和账号到期符合目标；
- 口令状态不是锁定或无口令。

### ⑥ 新会话验证边界

需要确认实际登录身份时，可先暂时不设置 `chage -d 0`，完成：

```bash
su - lina -c 'id; pwd'
```

随后再执行 `chage -d 0 lina`。若已经强制下次改口令，非交互式 `su -c` 可能失败，这是期限策略的预期影响，不能误判为组配置错误。

### 典型错误

- 只写 `-d /srv/home/lina`，目录字段改变但目录未创建。
- 把 `-g developers` 当作附加组参数，错误改变主组。
- 用空格分隔 `-G` 的组名，而不是逗号列表。
- 设置了全局 `/etc/login.defs` 后，误以为既有用户期限会自动变化。
- `id lina` 正确便停止验收，没有检查家目录、口令和期限。

</section>

<section class="topic task" id="RHCSA-07-C02" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 安全停用外部人员账号并评估删除

### 环境与当前状态

- 本地账号 `vendor1` 存在，可能仍有登录会话和运行进程。
- 家目录中有资料，`/srv/vendor-data` 下可能有该 UID 拥有的数据。
- 业务要求立即阻止新的账号使用，但当天禁止删除任何数据。
- 一周后将依据数据移交结果决定是否删除账号。

### 第一阶段目标

1. 记录用户名、UID、主 GID、附加组、家目录、Shell、口令和期限。
2. 记录账号拥有的业务数据与当前会话线索。
3. 锁定口令并使账号立即到期，保留账号记录与全部数据。
4. 明确记录：已有会话和进程不会被这些账号操作自动结束。
5. 验证数据库中的停用状态。

### 第二阶段删除评估

1. 按保存的 UID/GID 搜索家目录外的数据。
2. 确认归档、移交或重新所有方案。
3. 决定使用 `userdel` 还是 `userdel -r`，并说明两者都不能自动处理任意外部路径。
4. 检查同名用户私有组和旧 GID 文件。
5. 不使用 `--force` 绕过调查。

</section>

<div class="page-break"></div>

<section class="topic answer" id="RHCSA-07-A02" data-kind="reference-answer">

## <span class="topic-label">[参考解答]</span> 安全停用与删除评估

### ① 建立身份和期限基线

```bash
getent passwd vendor1
id vendor1
passwd -S vendor1
chage -l vendor1
uid=$(id -u vendor1)
gid=$(id -g vendor1)
printf 'uid=%s gid=%s\n' "$uid" "$gid"
```

把输出保存到变更记录。不要在删除后才尝试猜测旧数字。

### ② 调查数据和活动线索

```bash
find /home /srv -xdev \( -uid "$uid" -o -gid "$gid" \) -print
who
w
ps -u vendor1 -f
```

`who`、`w` 和 `ps` 只用于记录活动线索。终止会话和进程属于第 11 章，应经过业务确认后处理。

### ③ 锁定口令并使账号到期

一种明确的静态路径是：

```bash
passwd -l vendor1
chage -E 0 vendor1
```

这里用 `0` 把账号到期字段设置为 Unix epoch 起始日，使其在当前日期下已经到期；执行后仍必须用 `chage -l` 核对现场解释。不要只运行 `passwd -l` 就声称账号所有访问方式都已禁用。

### ④ 验证停用状态

```bash
passwd -S vendor1
chage -l vendor1
getent passwd vendor1
```

账号记录、UID/GID 和家目录字段仍应存在；口令显示锁定，账号到期日显示已过去。再记录已有会话或进程仍需独立处理的事实。

### ⑤ 一周后的删除决策

若要求保留家目录：

```bash
userdel vendor1
```

若已经完成家目录归档并明确要求删除默认家目录和邮件池：

```bash
userdel -r vendor1
```

两种方式执行前都要再次按保存的 UID/GID 调查 `/srv/vendor-data` 等外部路径。执行后验证：

```bash
getent passwd vendor1
getent group vendor1
find /home /srv -xdev \( -uid "$uid" -o -gid "$gid" -o -nouser -o -nogroup \) -print
```

### ⑥ 典型错误

- 先 `userdel -r`，再发现业务数据尚未移交。
- 锁定口令后声称 SSH 密钥、已有会话和服务进程都已停止。
- 只查家目录，不查 `/srv`、挂载卷和共享目录。
- 删除账号后立即创建新用户，导致旧 UID 被重用。
- 把 `find ... -nouser` 的结果直接批量删除，没有人工审批。

</section>


<section class="topic closure" id="RHCSA-07-Z01" data-kind="closure">

## <span class="topic-label">[本章收束]</span> 用生命周期和证据管理身份

本章把账号管理从“记命令”还原成一条对象链：名称先解析为 UID/GID，主组与附加组共同构成数据库身份，四个账号数据库保存公开属性、口令与期限，创建和修改命令推进持久状态，而新登录、`su -` 或 `newgrp` 才让新的组凭据进入进程。停用和删除又分别作用于口令、期限、Shell、账号记录与数据，任何一步都不能被概括为“用户没了”。

### 工作方法

```text
确定目标身份
→ 读取名称与数字基线
→ 区分数据库字段和会话凭据
→ 选择最小生命周期操作
→ 验证账号、组、期限和家目录
→ 建立新会话验证实际身份
→ 删除或重用 UID/GID 前调查数据
```

操作前尽量记录用户名、UID、主 GID、附加组、家目录、Shell、口令状态与期限；操作后按同样维度复查。这样既能服务考试评分，也能在真实系统中保留审计和回退线索。

### 主要判断表

| 目标或症状 | 首要证据 | 该证据能证明 | 仍不能证明 |
|---|---|---|---|
| 用户是否被系统解析 | `getent passwd USER` | 当前 NSS 能返回账号条目 | 当前旧会话是否已采用新组 |
| 用户属于哪些组 | `id USER` | 数据库解析出的主组和附加组 | 既有 Shell 的实际组集合 |
| 口令是否锁定 | `passwd -S USER` | 口令字段的状态摘要 | SSH Key、已有会话或服务进程是否停止 |
| 密码或账号是否到期 | `chage -l USER` | 密码期限和账号到期字段 | 具体认证服务的完整准入结果 |
| 家目录是否完成迁移 | passwd 字段 + `stat` + 内容核对 | 路径、数字所有权与数据是否到位 | 文件访问权限是否符合业务规则 |
| 删除是否留下数据 | 保存的 UID/GID + `find` | 指定范围中的数字所有权遗留 | 未扫描挂载点中是否还有数据 |

### 本章总 Cheatsheet

```bash
# 查询
getent passwd USER
getent group GROUP
id USER
passwd -S USER
chage -l USER
useradd -D

# 创建
groupadd -g GID GROUP
useradd -u UID -g PRIMARY -G G1,G2 -d HOME -m -s SHELL USER
passwd USER
chage -m MIN -M MAX -W WARN -I INACTIVE -E DATE USER

# 修改
usermod -l NEW OLD
usermod -aG GROUP USER
usermod -G G1,G2 USER
usermod -g PRIMARY USER
usermod -d HOME -m USER
usermod -s SHELL USER
groupmod -n NEW OLD
groupmod -g GID GROUP

# 会话
su USER
su - USER
newgrp GROUP

# 停用与删除
passwd -l USER
chage -E DATE USER
userdel USER
userdel -r USER
groupdel GROUP
```

### 向下一章交接

本章已经确定“谁在访问”：用户的 UID/GID、组集合和会话凭据。第 08 章《传统权限、umask 与特殊权限位》将继续回答“这些身份如何被文件模式位解释”，包括所有者、所属组、其他用户、默认创建模式以及 SUID、SGID 和 Sticky 位。本章不提前展开权限计算，但会把可靠的身份与组证据交给下一章。

</section>
