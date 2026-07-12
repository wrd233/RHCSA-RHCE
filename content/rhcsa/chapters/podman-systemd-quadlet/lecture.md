---
title: "第 32 章 容器持久化、用户 systemd 与 Quadlet"
chapter_id: RHCSA-32
exam: RHCSA
part: 第八篇　容器
slug: podman-systemd-quadlet
validation: static
status: integrated
sources:
  - RH134-RHEL9
  - RHEL9-container-documentation
  - podman-systemd.unit(5)-4.6.1
  - systemctl(1)
  - loginctl(1)
  - journalctl(1)
---


# 第 32 章　容器持久化、用户 systemd 与 Quadlet

容器能够运行，不等于它已经成为一项可维护的系统服务。手工执行一次 `podman run`，只建立了一个当前实例；用户退出、主机重启、镜像更新或配置变化以后，这个实例是否还能以相同参数恢复，取决于另一个层次的声明和生命周期管理。

本章把容器从“当前正在运行的对象”提升为“可以由用户 systemd manager 重建和监督的声明对象”。主线不是把长串 `podman run` 命令塞进手写 service，也不是把旧的 `podman generate systemd` 当成唯一答案，而是使用 Quadlet `.container` 文件表达期望状态，再由 generator 生成普通 `.service`，最后通过 `systemctl --user`、`loginctl`、`journalctl` 和 Podman 证据完成分层验收。

**[概念]** 当前容器实例是一次运行事实，拥有容器 ID、名称、镜像 ID、端口、挂载、环境变量和退出状态；Quadlet 声明是下一次生成实例时的配置输入。两者可能一致，也可能已经发生漂移。

**[概念]** 用户 systemd manager 属于特定 UID。`systemctl --user` 操作的是当前用户的 manager，不是系统 PID 1 管理的 system scope。root 执行普通 `systemctl` 不能代替目标普通用户的 `systemctl --user`。

**[概念]** linger 是登录生命周期策略。启用 linger 后，系统可以在开机时创建该用户的 manager，并在最后一次注销后保留它；linger 不会自动修复 Quadlet 路径、字段、端口冲突或数据权限。

**[概念]** Quadlet `.container` 是声明真源；generator 在系统启动或 `daemon-reload` 时读取它，生成同名 `.service`。生成结果属于派生状态，不应直接编辑。

**[操作语义]** `podman` 观察容器、镜像、端口、挂载和日志；`systemctl --user` 控制用户 unit；`loginctl` 查询和改变用户 manager 的登录外生命周期；`journalctl --user-unit=` 读取用户 unit 的启动失败和运行事件。

**[判断边界]** `.container` 文件存在，不等于 unit 已生成；unit 已生成，不等于当前 active；unit active，不等于容器内部应用可用；应用可用，不等于数据已外置；当前成功，也不等于重启后在用户尚未登录时仍成功。

---

<section class="topic knowledge" id="RHCSA-32-K01">

## [知识专题] 当前实例与声明配置：先分清“已经发生”与“下一次应发生”

把现有容器迁移为 systemd 服务时，最危险的做法是直接抄一条记忆中的模板。现有实例可能包含题目要求保留的数据、端口、环境变量和用户映射，也可能包含临时试验参数。正确切入点是先建立当前事实，再决定哪些事实应进入声明，哪些应该被纠正。

### ① [知识点] 容器实例只描述当前事实

`podman ps -a` 能显示名称、状态、端口等摘要，`podman inspect` 能读取创建时的详细配置。它们回答的是：当前这个实例怎样被创建、现在处于什么状态。容器 ID 不是长期配置标识；实例被删除和重建后，ID 通常变化。

建议在迁移前至少记录：

```bash
podman ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
podman inspect report > ~/report-before.json
podman port report
podman logs --tail 50 report
```

`inspect` 是基线证据，不是自动生成声明的权威模板。它可能保留历史临时选项，仍需根据任务目标筛选。

### ② [知识点] 声明配置描述下一次生成的期望状态

`.container` 文件表达下一次服务启动时应使用的镜像、名称、端口、挂载和环境。修改声明不会在同一瞬间改写当前容器；systemd 先要重新加载生成结果，运行实例再通过 restart 或下一次启动采用新配置。

因此需要区分三次变化：

```text
编辑 .container
→ systemctl --user daemon-reload 重新生成 service
→ systemctl --user restart NAME.service 重建运行实例
```

只完成第一步时，当前业务可能仍在使用旧参数；只执行 restart 而没有 reload，也可能继续使用旧的 generated unit。

### ③ [知识点] 迁移不是“复制所有旧参数”，而是建立可验证终态

迁移时将现有事实分成三类：

| 类别 | 例子 | 处理 |
|---|---|---|
| 必须保留 | 业务数据目录、规定端口、必要环境变量 | 进入声明并逐项验证 |
| 应纠正 | 临时随机端口、错误名称、数据只在可写层 | 按任务终态重构 |
| 暂不进入主线 | 调试用 shell、临时 capability、实验标签 | 有明确需求才保留 |

迁移前不要先删除旧实例。先确认数据在何处、是否有外部副本、端口是否被依赖，再安排最小停机切换。

**[Cheatsheet]** `inspect` 建立当前事实；`.container` 表达下一次期望；编辑、reload、restart 是三个不同动作；容器 ID 变化不等于数据丢失，数据位置才是关键。

</section>

<section class="topic knowledge" id="RHCSA-32-K02">

## [知识专题] 用户 systemd manager：作用域比命令名字更重要

容器由哪个用户运行，会决定 Podman 存储、容器可见性、用户 bus、unit 搜索范围和日志作用域。很多“unit not found”并不是 unit 文件不存在，而是当前命令连到了错误的 manager。

### ① [知识点] system scope 与 user scope 是两个管理域

普通命令：

```bash
systemctl status sshd.service
```

连接系统 manager，管理系统级 unit。用户命令：

```bash
systemctl --user status report.service
```

连接当前用户的 manager，管理该用户的 unit。对于 rootless 容器，Quadlet、Podman 存储和 user unit 必须归属于同一目标用户。

以下证据应在目标用户上下文中取得：

```bash
id
podman ps -a
systemctl --user list-unit-files
systemctl --user status report.service
```

不要把 root 的 `podman ps` 为空解释为目标用户没有容器，也不要把系统 manager 的 `Unit report.service could not be found` 直接解释为 Quadlet 未生成。

### ② [知识点] 登录会话与用户 manager 相关，但不是同一对象

用户通过 SSH、控制台或其他 PAM 会话登录时，通常会得到用户 runtime 目录和 user manager 访问环境。注销最后一个会话后，如果没有 linger，用户 manager 可以被停止；由它监督的长期 user service 也会失去管理者。

查询用户生命周期：

```bash
loginctl show-user appsvc -p Linger -p State -p Sessions
loginctl user-status appsvc
```

`State=active` 只表示当前存在活跃会话或 manager 状态，不等同于重启后会自动创建；`Linger=yes` 才是脱离登录会话的持久策略之一。

### ③ [知识点] linger 延长 manager 生命周期，不替代 unit 配置

启用：

```bash
sudo loginctl enable-linger appsvc
```

验证：

```bash
loginctl show-user appsvc -p Linger
```

`Linger=yes` 可以支持开机时创建 user manager，并使最后一次注销后 manager 继续存在。但它不能证明：

- `.container` 在正确目录；
- `[Install]` 已表达启动关系；
- generated service 能加载；
- 容器镜像可用；
- 端口和数据目录无冲突；
- 应用功能正确。

**[Cheatsheet]** rootless 容器、Quadlet、user unit 和日志都要在同一 UID 作用域内取证；`--user` 不是装饰选项；linger 解决登录外生命周期，不解决配置正确性。

</section>

<section class="topic knowledge" id="RHCSA-32-K03">

## [知识专题] Quadlet 的输入、搜索路径和生成物

Quadlet 的价值在于让管理员维护简短的容器声明，由 Podman generator 根据当前版本生成具体 `ExecStart=` 等实现细节。这样升级 Podman 后不需要继续维护一份历史生成脚本。

### ① [知识点] rootless `.container` 的搜索路径

本章主线使用当前用户目录：

```text
$XDG_CONFIG_HOME/containers/systemd/
~/.config/containers/systemd/
```

管理员也可以为特定 UID 或全部用户提供系统级用户声明：

```text
/etc/containers/systemd/users/<UID>/
/etc/containers/systemd/users/
```

rootful 系统声明使用：

```text
/etc/containers/systemd/
/usr/share/containers/systemd/
```

考试任务应先明确 rootless 还是 rootful。把 rootless Quadlet 放入 `~/.config/systemd/user/` 是常见路径错误；该目录适合普通 user unit，不是本章 `.container` 主路径。

### ② [知识点] 文件名映射为 service 和默认容器名

`report.container` 生成 `report.service`。若未写 `ContainerName=`，Podman 默认采用带 `systemd-` 前缀的名称，例如 `systemd-report`，以减少与手工容器重名。

```text
report.container
      ↓ generator
report.service
      ↓ podman run
systemd-report   （未显式 ContainerName 时）
```

任务明确要求容器名时应写 `ContainerName=report`，并在迁移前处理已有同名实例，避免启动时发生 name already in use。

### ③ [知识点] generated service 是派生状态

generator 在开机和 manager reload 时读取声明。管理员应修改 `.container`，然后执行：

```bash
systemctl --user daemon-reload
```

可以使用以下命令观察生成结果：

```bash
systemctl --user status report.service
systemctl --user cat report.service
systemctl --user show report.service -p FragmentPath -p SourcePath -p LoadState
```

实际字段显示会随 systemd/Podman 版本变化，不能把某条固定输出当成唯一评分证据。核心判断是 service 能否被正确加载，并且来源可追溯到目标 `.container`。

**[Cheatsheet]** rootless 路径是 `~/.config/containers/systemd/`；后缀必须是 `.container`；`NAME.container → NAME.service`；默认容器名可能是 `systemd-NAME`；只编辑源声明，不编辑生成物。

</section>

<section class="topic operation" id="RHCSA-32-O01">

## [操作专题] 把 `podman run` 参数翻译为 `.container`

Quadlet 不是另一种 shell 命令拼接，而是把容器参数映射为可读字段。转换时应逐项回答：该字段控制哪个对象，是否能从题目终态验证，是否需要重复出现。

### ① [操作] 镜像与容器名称

**作用对象：** 下一次创建的容器实例。

**基本形式：**

```ini
[Container]
Image=registry.example.com/rhcsa/report:9
ContainerName=report
```

`Image=` 是 `.container` 的必需字段。优先使用完整镜像名，避免短名称解析不确定。tag 表示可变名称；若任务要求精确不可漂移版本，可使用 digest，但考试题通常会给定 tag 或完整引用。

`ContainerName=` 是可选字段。省略时要接受默认 `systemd-` 前缀名称；题目指定名字时再显式设置。

**验证：**

```bash
podman inspect report --format '{{.Name}} {{.ImageName}} {{.Image}}'
```

不要把 `podman images` 中存在目标 tag 当成运行实例已经采用该 image ID 的证据。

### ② [操作] 端口与环境变量

**基本形式：**

```ini
[Container]
PublishPort=18080:8080
Environment=REPORT_MODE=exam
Environment=LOG_LEVEL=info
```

`PublishPort=` 对应 `podman run --publish`，可重复使用。`18080:8080` 表示宿主端口 18080 映射到容器端口 8080。只有容器端口而没有固定宿主端口时可能产生动态宿主端口，不适合要求固定入口的题目。

`Environment=` 对应 `--env`，可重复使用。包含空格或特殊字符时要遵循 systemd 单元语法，避免随意套用 shell 引号规则。

**验证：**

```bash
podman port report
podman inspect report --format '{{json .Config.Env}}'
curl -fsS http://127.0.0.1:18080/
```

端口存在只能证明转发表达，`curl` 或实际协议测试才进入功能层。

### ③ [操作] 数据卷、服务重启与开机关系

**基本形式：**

```ini
[Container]
Volume=/home/appsvc/report-data:/var/lib/report:Z

[Service]
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

`Volume=` 对应 `--volume`，可重复使用。宿主路径在左，容器路径在右。`:Z` 为该容器准备私有 SELinux 标签；共享语义和完整标签诊断归第 29、31 章，本章只要求保留最小安全边界。

`Restart=on-failure` 属于生成 service 的 `[Service]` 配置，适合进程异常退出后重试；它不会修复不可拉取镜像、重名容器、端口占用和持续权限错误，只会让失败反复出现。

Quadlet 生成的 service 属于 transient/generated unit，不能把普通 unit 的 `systemctl --user enable report.service` 当作唯一主线。自动启动关系写进源文件 `[Install]`，由 generator 应用。用户级服务通常使用 `default.target`。

**完整示例：**

```ini
[Unit]
Description=Persistent rootless report container
After=network-online.target

[Container]
Image=registry.example.com/rhcsa/report:9
ContainerName=report
PublishPort=18080:8080
Volume=/home/appsvc/report-data:/var/lib/report:Z
Environment=REPORT_MODE=exam

[Service]
Restart=on-failure
RestartSec=5
TimeoutStartSec=900

[Install]
WantedBy=default.target
```

`TimeoutStartSec=900` 不是所有题目都需要。镜像首次拉取可能超过 systemd 默认启动超时，只有证据表明启动卡在拉取且网络正常时，才考虑预拉镜像或延长超时。

**[Cheatsheet]** `Image` 必需；`ContainerName` 控制实例名；`PublishPort` 左宿主右容器；`Volume` 左源右目标；`Environment` 可重复；`Restart` 不修复根因；Quadlet 开机关系写 `[Install]`。

</section>

<section class="topic operation" id="RHCSA-32-O02">

## [操作专题] 从声明到运行：reload、start 与证据链

最小流程不是一句 `start`。每一步产生不同证据，失败时应停在当前层调查，而不是继续堆命令。

### ① [操作] 建立目录和声明

```bash
install -d -m 0755 ~/.config/containers/systemd
vi ~/.config/containers/systemd/report.container
```

检查：

```bash
ls -l ~/.config/containers/systemd/report.container
sed -n '1,200p' ~/.config/containers/systemd/report.container
```

文件应属于目标用户，宿主数据目录也要在该用户和容器映射可访问的权限范围内。不要为了跳过调查直接 `chmod 777`。

### ② [操作] 重新生成并启动 unit

```bash
systemctl --user daemon-reload
systemctl --user start report.service
```

若需要立即应用声明变更：

```bash
systemctl --user restart report.service
```

`daemon-reload` 让 manager 重新读取 source unit 并运行 generator，不会自行重启已运行服务。`restart` 负责让新生成的 service 进入运行实例。

### ③ [操作] 查询 unit、容器和功能

```bash
systemctl --user status report.service --no-pager
systemctl --user show report.service \
  -p LoadState -p ActiveState -p SubState -p Result -p NRestarts
podman ps -a --filter name=report
podman port report
curl -fsS http://127.0.0.1:18080/
```

`ActiveState=active` 证明 systemd 当前认为主服务活动；它不能独立证明应用内容正确。若镜像内进程保持运行但返回错误页面，unit 仍可能 active。

**帮助入口：**

```bash
man podman-systemd.unit
man systemctl
man systemd.service
```

**[Cheatsheet]** 创建声明后 reload；需要当前采用新配置再 restart；`status/show` 查 manager，`podman` 查实例，协议请求查功能。

</section>

<section class="topic knowledge" id="RHCSA-32-K04">

## [知识专题] 依赖、顺序与 Restart：三种不同关系

容器服务可能依赖另一个服务、挂载点或网络准备。依赖关系不能只靠排列文件名，也不能只写 `After=` 就假设依赖对象一定会启动。

### ① [知识点] `Requires=` 表达启动和失败关系

```ini
[Unit]
Requires=database.service
```

要求 database unit 一起参与事务；所需 unit 无法启动时，当前 unit 通常不能成功进入目标状态。它表达“需要谁”，不保证先后顺序。

### ② [知识点] `After=` 只表达顺序

```ini
[Unit]
After=database.service
```

表示两者都进入同一事务时，本 unit 在 database 之后启动。它不会主动把 database 拉入事务。常见组合是：

```ini
[Unit]
Requires=database.service
After=database.service
```

依赖其他 Quadlet 时使用生成后的 `.service` 名称，例如 `After=database.service`，不是 `After=database.container`。

### ③ [知识点] Restart 处理退出结果，不处理声明错误

```ini
[Service]
Restart=on-failure
RestartSec=5
```

该策略处理非零退出、信号终止等失败。以下问题通常会形成稳定失败或循环：

- `ContainerName=` 与旧实例重名；
- 宿主端口已占用；
- 数据目录不可访问；
- 应用参数错误，启动即退出；
- 镜像引用无效。

出现循环时先取证：

```bash
systemctl --user show report.service -p Result -p NRestarts
journalctl --user-unit=report.service -b -n 100 --no-pager
podman ps -a --filter name=report
```

不要把 `Restart=always` 当成“提高可靠性”的无条件答案。若应用正常完成后本应退出，always 会制造无意义循环。

**[Cheatsheet]** `Requires` 解决“需要谁”，`After` 解决“谁先谁后”，`Restart` 解决“失败退出后怎么办”；三者不可互换。

</section>

<section class="topic operation" id="RHCSA-32-O03">

## [操作专题] 让数据独立于容器实例

持久化的目标不是让容器 ID 永远不变，而是让业务数据不依赖一次实例的可写层。最强的验证不是“容器重启后文件还在”，而是删除并由声明重建实例后，外部数据仍能被新实例读取。

### ① [操作] 识别数据所在层

调查现有挂载：

```bash
podman inspect report --format '{{json .Mounts}}'
podman volume ls
findmnt -T /home/appsvc/report-data
```

如果关键文件只存在容器内且没有对应挂载，应先导出或复制到规划的持久目录，再删除旧实例。不要先 `podman rm` 再确认数据。

### ② [操作] 准备宿主目录和最小权限

```bash
install -d -m 0750 ~/report-data
printf 'persistent-marker\n' > ~/report-data/marker.txt
ls -ldZ ~/report-data
```

宿主传统权限、容器内 UID、rootless 用户映射和 SELinux 标签共同决定访问。默认排障顺序：

```text
宿主路径是否正确
→ 所有者和模式是否允许
→ 容器内进程使用哪个 UID
→ 当前 SELinux 上下文和 AVC
```

禁止以 `chmod 777` 或关闭 SELinux 代替调查。

### ③ [操作] 通过重建验证持久性

最低层：

```bash
podman exec report cat /var/lib/report/marker.txt
```

更强验证：

```bash
systemctl --user stop report.service
podman ps -a --filter name=report
systemctl --user start report.service
podman exec report cat /var/lib/report/marker.txt
```

若维护窗口和任务允许，可在确认数据外置后删除实例，再由 unit 重建；不要删除宿主数据目录或 named volume。

```bash
systemctl --user stop report.service
podman rm report
systemctl --user start report.service
podman exec report cat /var/lib/report/marker.txt
```

该流程证明数据跨实例，而不是只跨进程 restart。实际考试中是否手工 `podman rm` 要依据题目和现有状态决定，不把破坏性步骤当成无条件模板。

**[Cheatsheet]** 可写层随实例；外部目录/volume 才是持久层；先定位数据再删除；最强验证是新实例读取旧数据。

</section>

<section class="topic operation" id="RHCSA-32-O04">

## [操作专题] 声明变更、镜像更新与重建边界

容器维护常见误判是“镜像已经 pull，所以服务已经更新”。本地 tag 指向新 image ID，不会自动把已运行容器替换成新实例；Quadlet 源文件变化也不会自动让当前容器采用新值。

### ① [操作] 变更前保存基线

```bash
podman inspect report > ~/report-before.json
systemctl --user show report.service \
  -p ActiveState -p SubState -p Result -p NRestarts
curl -fsS http://127.0.0.1:18080/ > ~/report-before.out
```

基线至少覆盖运行状态、镜像、端口、挂载、环境和业务输出。

### ② [操作] 修改声明后 reload + restart

```bash
vi ~/.config/containers/systemd/report.container
systemctl --user daemon-reload
systemctl --user restart report.service
```

若只改了宿主数据内容或应用自身可热加载配置，是否需要容器 restart 取决于应用；不要把 systemd `daemon-reload` 误认为应用 reload。

### ③ [操作] 区分 tag、image ID 与当前实例

```bash
podman image inspect registry.example.com/rhcsa/report:9 \
  --format '{{.Id}}'
podman inspect report --format '{{.Image}} {{.ImageName}}'
```

只有当前实例的 `.Image` 与期望 image ID 一致，才能证明它采用了当前本地镜像。更新后重新验证端口、环境、挂载、数据和功能。自动更新机制属于扩展，不在 RHCSA 主线完整展开。

**[Cheatsheet]** pull 改变本地镜像，不直接替换容器；源变更要 reload；实例采用新配置要 restart/recreate；更新后回归数据和业务功能。

</section>

<section class="topic diagnosis" id="RHCSA-32-D01">

## [诊断专题] linger 已启用，但 unit 没有生成

症状可能是：`loginctl show-user` 显示 `Linger=yes`，但 `systemctl --user status report.service` 返回 unit not found。此时 linger 已经排除一个生命周期问题，但不能证明 Quadlet 已被目标 manager 读取。

### ① [诊断] 先确认作用域和版本

```bash
id
podman version
systemctl --user --version
loginctl show-user "$USER" -p Linger
```

**假设 A：** 命令在错误用户下执行。下一条最有区分度的证据是 `id` 与 `echo $HOME`，再比较声明的所有者和路径。

**假设 B：** Podman 版本低于 Quadlet 支持范围。下一条证据是 `podman version` 和本机 `man podman-systemd.unit` 是否存在相关 `.container` 说明。

### ② [诊断] 检查路径、后缀和内容

```bash
find ~/.config/containers/systemd -maxdepth 1 -type f -printf '%f\n'
sed -n '1,200p' ~/.config/containers/systemd/report.container
```

常见错误：

- 放到 `~/.config/systemd/user/`；
- 文件名是 `report.service` 或 `report.container.txt`；
- `[Container]` 拼写错误；
- 缺少必需的 `Image=`；
- 文件属于其他用户；
- 编辑器写入不可见字符或错误换行。

### ③ [诊断] reload 后从 manager 日志取证

```bash
systemctl --user daemon-reload
systemctl --user list-unit-files | grep -F report
journalctl --user -b --since '-10 min' --no-pager
```

**最小修复：** 只修正错误路径、字段或用户归属，再 reload。不要为了让 unit 出现而另写一份手工 `.service`，否则会绕过本章声明主线并制造两个配置真源。

**再验证：** `report.service` 可加载、来源指向 `.container`，然后才进入启动层。

**[Cheatsheet]** `Linger=yes + unit not found` 优先查用户、版本、路径、后缀、必需字段和 generator 日志；不要先改成 rootful，也不要另建同名手工 service。

</section>

<section class="topic diagnosis" id="RHCSA-32-D02">

## [诊断专题] unit 已生成，但容器启动失败或循环重启

这里的目标是从 systemd 结果推进到 Podman 和宿主资源，而不是反复执行 restart。

### ① [诊断] 读取最小状态向量

```bash
systemctl --user show report.service \
  -p LoadState -p ActiveState -p SubState -p Result -p NRestarts
journalctl --user-unit=report.service -b -n 100 --no-pager
```

`Result=exit-code`、`NRestarts` 增长和 journal 中首个失败原因，比最后一行“Scheduled restart job”更有价值。

### ② [诊断] 按错误类型进入下一层

| 日志线索 | 假设 | 下一条证据 |
|---|---|---|
| name already in use | 同名手工实例残留 | `podman ps -a --filter name=report` |
| address already in use | 宿主端口冲突 | `ss -ltnp | grep :18080`、`podman ps --format` |
| permission denied | 宿主 DAC、UID 映射或 SELinux | `namei -l`、`ls -ldZ`、AVC 日志 |
| image not known/pull failed | 镜像引用或网络/认证 | `podman image exists`、手工 `podman pull` 的错误 |
| 容器很快 Exited | 应用入口或参数失败 | `podman ps -a`、`podman logs` |

手工运行诊断命令时不要轻易创建另一个同名容器；优先读取 generated service、journal 和失败实例证据。

### ③ [诊断] 最小修复后清除失败并重验

修正根因后：

```bash
systemctl --user daemon-reload   # 仅当声明有修改
systemctl --user reset-failed report.service
systemctl --user restart report.service
```

再按 unit、容器、功能和数据四层验证。`reset-failed` 只清理失败计数和状态，不修复配置。

**[Cheatsheet]** 先看 `Result/NRestarts` 和第一失败原因；重名查容器，端口查监听，权限查 DAC/映射/SELinux，退出查应用日志；修根因后再 restart。

</section>

<section class="topic diagnosis" id="RHCSA-32-D03">

## [诊断专题] 当前运行正常，但注销或重启后失败

此类故障说明当前运行层已经通过，问题集中在 user manager 生命周期、安装关系或“未登录验证方法”上。

### ① [诊断] 分开检查 `[Install]` 与 linger

源声明：

```bash
sed -n '/^\[Install\]/,$p' ~/.config/containers/systemd/report.container
```

linger：

```bash
loginctl show-user appsvc -p Linger
```

两者缺一不可：`WantedBy=default.target` 表达 manager 启动时拉起 service；linger 支持 manager 在开机和注销后存在。

### ② [诊断] 注销测试不能依赖同一个会话

在目标用户会话中确认当前功能后，退出该用户全部会话。从另一个管理员账号或远端客户端验证：

```bash
curl -fsS http://HOST:18080/
loginctl show-user appsvc -p Linger -p State
```

若重新登录目标用户后服务才恢复，说明“登录触发启动”，不能算作未登录持久成功。

### ③ [诊断] 冷启动证据应先于目标用户登录

重启后不要先登录 `appsvc`。先从其他账号或外部主机测试业务入口，再查看：

```bash
loginctl user-status appsvc
```

随后进入目标用户完整会话，核对：

```bash
systemctl --user status report.service --no-pager
journalctl --user-unit=report.service -b --no-pager
podman ps -a
```

本会话没有 RHEL 9 VM，以上属于推荐 live-test 流程，不能声明已执行。

**[Cheatsheet]** 当前 active 只证明现在；`[Install]` 解决 manager 内的启动关系，linger 解决 manager 的登录外生命周期；冷启动验收要在目标用户首次登录前先测功能。

</section>

<section class="topic task" id="RHCSA-32-T01">

## [经典任务] 把现有 rootless 容器迁移为 Quadlet，并验证未登录持久运行

### 环境

服务器上存在普通用户 `appsvc`。该用户当前手工运行一个名为 `report` 的 rootless 容器：

```text
镜像：registry.example.com/rhcsa/report:9
宿主端口：18080
容器端口：8080
宿主数据目录：/home/appsvc/report-data
容器数据目录：/var/lib/report
环境变量：REPORT_MODE=exam
```

`/home/appsvc/report-data/marker.txt` 是必须保留的数据。当前容器可以访问，但 `appsvc` 注销后不再可靠运行，系统重启后也未建立未登录启动证据。

### 目标终态

1. 以 `appsvc` 的 rootless Podman 运行，不改成 rootful。
2. 使用 `~/.config/containers/systemd/report.container` 作为维护真源。
3. 生成并运行 `report.service`，容器名称保持 `report`。
4. 端口、环境变量和数据挂载符合题目。
5. 异常退出时采用 `Restart=on-failure`，间隔 5 秒。
6. 用户注销后服务继续运行。
7. 主机重启后，在 `appsvc` 尚未登录时，外部仍能访问宿主端口。
8. 标记文件在迁移、注销和重启后仍存在。

### 限制条件

- 不得 `chmod 777`；
- 不得关闭 SELinux；
- 不得删除 `/home/appsvc/report-data`；
- 不得把数据只复制进容器可写层；
- 不得直接编辑 generated service；
- 不得以“重新登录后服务恢复”代替未登录启动验证；
- 删除旧容器前必须确认持久数据位置。

### 验收证据

| 层 | 必须给出的证据 |
|---|---|
| 身份 | `id`、目标用户的 `podman ps -a` |
| 声明 | `.container` 路径、关键字段 |
| 生成 | `report.service` 可加载且来源正确 |
| unit | `ActiveState`、`SubState`、`Result`、`NRestarts` |
| 实例 | 名称、镜像、端口、环境和挂载 |
| 数据 | 宿主和容器内都能读到标记文件 |
| 功能 | 从宿主或远端请求 `18080` 成功 |
| 生命周期 | `Linger=yes`、注销后功能、冷启动未登录功能 |
| 日志 | 当前 boot 的 user unit journal 无持续失败 |

</section>

<div class="page-break"></div>

<section class="topic answer" id="RHCSA-32-A01">

## [参考解答] 经典任务一

以下命令中的主机名、镜像可访问性和应用返回内容由实际实验环境决定。本章只提供静态核对后的参考流程，不声称已在 RHEL 9 VM 执行。

### 一、调查当前实例和数据

以 `appsvc` 的完整登录环境操作：

```bash
id
podman version
podman ps -a --filter name=report
podman inspect report > ~/report-before.json
podman port report
podman inspect report --format '{{json .Mounts}}'
ls -lZ ~/report-data/marker.txt
```

确认 `marker.txt` 位于宿主目录，而不是只存在容器可写层。若当前实例没有正确挂载，应先安全导出数据，不能直接删除实例。

记录当前功能：

```bash
curl -fsS http://127.0.0.1:18080/
```

### 二、建立 Quadlet 声明

```bash
install -d -m 0755 ~/.config/containers/systemd
cat > ~/.config/containers/systemd/report.container <<'EOF'
[Unit]
Description=Persistent rootless report container
After=network-online.target

[Container]
Image=registry.example.com/rhcsa/report:9
ContainerName=report
PublishPort=18080:8080
Volume=/home/appsvc/report-data:/var/lib/report:Z
Environment=REPORT_MODE=exam

[Service]
Restart=on-failure
RestartSec=5
TimeoutStartSec=900

[Install]
WantedBy=default.target
EOF
```

静态核对：

```bash
sed -n '1,200p' ~/.config/containers/systemd/report.container
ls -l ~/.config/containers/systemd/report.container
```

`TimeoutStartSec=900` 用于降低首次拉取镜像超过默认超时的风险；若镜像已预拉且环境不需要，可省略。不要通过 `PodmanArgs=` 绕过有明确字段的标准配置。

### 三、处理同名旧实例

由于声明显式使用 `ContainerName=report`，旧实例若仍存在会发生重名。先停止当前业务并再次确认数据：

```bash
podman stop report
ls -lZ ~/report-data/marker.txt
```

只有确认数据已经外置后，才删除旧实例：

```bash
podman rm report
```

若题目不允许删除现有容器，可暂时不指定 `ContainerName=`，接受默认名称，并在维护窗口另行迁移；但这不满足本任务“名称保持 report”的终态。

### 四、重新生成并启动

```bash
systemctl --user daemon-reload
systemctl --user start report.service
```

检查 generated unit：

```bash
systemctl --user status report.service --no-pager
systemctl --user show report.service \
  -p LoadState -p ActiveState -p SubState -p Result -p NRestarts
systemctl --user cat report.service
```

不要对 generated service 机械执行：

```bash
systemctl --user enable report.service
```

开机关系已经写在 `.container` 的 `[Install]` 中，由 generator 应用。

### 五、验证容器参数、功能与数据

```bash
podman ps -a --filter name=report
podman inspect report --format '{{.Name}} {{.ImageName}} {{.Image}}'
podman port report
podman inspect report --format '{{json .Config.Env}}'
podman inspect report --format '{{json .Mounts}}'
podman exec report cat /var/lib/report/marker.txt
cat ~/report-data/marker.txt
curl -fsS http://127.0.0.1:18080/
```

如果 unit active 但 `curl` 失败，继续检查应用监听地址、容器内端口、应用日志和主机防火墙；不要把 active 扩大解释为功能正确。

### 六、启用并验证 linger

由有权限的管理员执行：

```bash
sudo loginctl enable-linger appsvc
loginctl show-user appsvc -p Linger
```

预期证据是 `Linger=yes`。这一步不替代 `.container` 和 service 验证。

### 七、验证注销后运行

退出 `appsvc` 的全部登录会话。使用另一个账号或远端主机验证：

```bash
curl -fsS http://SERVER:18080/
loginctl show-user appsvc -p Linger -p State
```

若只有重新登录 `appsvc` 后才恢复，继续调查 `[Install]`、generator 生成关系和 user manager，而不是宣告完成。

### 八、验证重启后未登录运行

在得到授权和维护窗口后重启。主机起来后，先不要登录 `appsvc`。从另一个账号或远端客户端执行功能测试：

```bash
curl -fsS http://SERVER:18080/
loginctl user-status appsvc
```

随后进入 `appsvc` 的完整登录环境，回查：

```bash
systemctl --user status report.service --no-pager
systemctl --user show report.service \
  -p ActiveState -p SubState -p Result -p NRestarts
journalctl --user-unit=report.service -b --no-pager
podman ps -a --filter name=report
podman exec report cat /var/lib/report/marker.txt
```

### 九、典型错误

1. **Quadlet 放错目录：** `~/.config/systemd/user/report.container` 不属于本章 rootless Quadlet 搜索路径。
2. **只开 linger：** manager 可以存在，但没有正确 generated unit，容器仍不会启动。
3. **只看 active：** 应用可能返回错误、端口不可达或数据挂载错误。
4. **直接 `enable` generated service：** 忽略 Quadlet transient unit 的 `[Install]` 机制。
5. **先删容器再找数据：** 若数据在可写层，会造成不可恢复损失。
6. **用 `chmod 777` 修权限：** 破坏最小权限，且可能仍绕不过 SELinux 或 UID 映射。
7. **登录后验证冷启动：** 登录动作本身可能创建 manager 或触发 unit，污染证据。

</section>

<section class="topic task" id="RHCSA-32-T02">

## [经典任务] 诊断 linger 已启用但 unit 未生成，并处理重启循环

### 场景

用户 `websvc` 的 `Linger=yes`。管理员声称已经创建容器服务，但出现两组症状：

1. `systemctl --user status portal.service` 最初返回 unit not found；
2. 修改后 unit 出现，却快速进入 failed，并且 `NRestarts` 持续增长。

已知系统中存在：

- 文件 `~/.config/systemd/user/portal.container`；
- 一个停止状态的手工容器 `portal`；
- 宿主端口 `18090` 可能被其他进程使用；
- 数据目录 `~/portal-data` 不得删除；
- 禁止改成 rootful、禁止关闭 SELinux、禁止用 `Restart=always` 掩盖错误。

### 要求

按“症状 -> 当前证据 -> 假设 -> 下一条区分度最高的证据 -> 最小修复 -> 再验证”提交处理过程，并最终满足：

- `portal.container` 位于正确路径；
- generated `portal.service` 可加载；
- 容器名称和端口无冲突；
- 数据目录可由应用访问；
- unit 不再循环；
- 协议功能和持久数据通过验证。

</section>

<div class="page-break"></div>

<section class="topic answer" id="RHCSA-32-A02">

## [参考解答] 经典任务二

### 第一阶段：unit not found

**症状：** `portal.service` 不存在。

**当前证据：**

```bash
id
loginctl show-user websvc -p Linger
find ~/.config -maxdepth 4 -type f -name 'portal*' -print
```

**假设：** `.container` 放入普通 user unit 目录，而不是 Quadlet 目录。

**下一条最有区分度的证据：** 路径显示为：

```text
/home/websvc/.config/systemd/user/portal.container
```

**最小修复：**

```bash
install -d -m 0755 ~/.config/containers/systemd
mv ~/.config/systemd/user/portal.container \
   ~/.config/containers/systemd/portal.container
systemctl --user daemon-reload
```

**再验证：**

```bash
systemctl --user status portal.service --no-pager
systemctl --user show portal.service -p LoadState -p SourcePath -p FragmentPath
```

若仍不存在，继续查 Podman 版本、`Image=`、文件后缀和 user journal，而不是创建同名手工 service。

### 第二阶段：restart loop

**症状：** service 出现但快速失败。

**当前证据：**

```bash
systemctl --user show portal.service \
  -p ActiveState -p SubState -p Result -p NRestarts
journalctl --user-unit=portal.service -b -n 100 --no-pager
```

假设按日志分支：

#### 分支 A：容器重名

```bash
podman ps -a --filter name=portal
```

若旧手工实例存在，先确认其挂载和数据：

```bash
podman inspect portal --format '{{json .Mounts}}'
ls -lZ ~/portal-data
```

确认数据外置后，停止并删除旧实例：

```bash
podman stop portal 2>/dev/null || true
podman rm portal
```

#### 分支 B：宿主端口冲突

```bash
ss -ltnp | grep ':18090 '
podman ps --format 'table {{.Names}}\t{{.Ports}}'
```

如果题目指定端口，停止或调整真正冲突对象前先确认业务归属；不能随意改成随机端口并宣告完成。

#### 分支 C：数据目录访问失败

```bash
namei -l ~/portal-data
ls -ldZ ~/portal-data
podman inspect portal --format '{{json .Config.User}}' 2>/dev/null
```

先修正最小传统权限和所有者，再检查 AVC。不得 `chmod 777`，不得 `setenforce 0`。

### 第三阶段：再生成、再启动和分层验证

声明有修改时：

```bash
systemctl --user daemon-reload
systemctl --user reset-failed portal.service
systemctl --user restart portal.service
```

验证：

```bash
systemctl --user show portal.service \
  -p ActiveState -p SubState -p Result -p NRestarts
podman ps -a --filter name=portal
podman port portal
podman exec portal test -r /var/lib/portal/marker.txt
curl -fsS http://127.0.0.1:18090/
journalctl --user-unit=portal.service -b -n 50 --no-pager
```

`NRestarts` 在一次历史故障后不一定立即变成零；关键是修复后不再持续增长，当前 `Result` 和业务功能正确。

</section>

<section class="topic closing" id="RHCSA-32-C01">

## [本章收束] 把容器持久性拆成可证明的链

本章的主结论不是“执行某条启动命令”，而是建立以下闭环：

```text
现有实例取证
→ Quadlet 声明成为配置真源
→ generator 生成 user service
→ user manager 监督容器
→ [Install] 建立 manager 内启动关系
→ linger 建立登录外生命周期
→ 外部数据独立于实例
→ unit、容器、数据、功能、注销和冷启动逐层验收
```

遇到故障时，不要从最后一层反复 restart。先判断失败停在哪一层：

```text
声明不存在或未识别
→ generated unit 不存在
→ unit 启动失败
→ 容器参数错误
→ 数据访问失败
→ 应用功能失败
→ 注销/重启生命周期失败
```

一项容器服务只有在“声明可维护、实例可重建、数据独立、功能可验证、用户未登录时仍能按要求启动”同时成立时，才具备本章所说的持久性。

### 章末速查

```bash
# 身份与版本
id
podman version

# Quadlet 源
ls -l ~/.config/containers/systemd/
sed -n '1,200p' ~/.config/containers/systemd/report.container

# 生成与控制
systemctl --user daemon-reload
systemctl --user start report.service
systemctl --user show report.service \
  -p LoadState -p ActiveState -p SubState -p Result -p NRestarts

# 实例与功能
podman ps -a
podman port report
podman inspect report --format '{{json .Mounts}}'
curl -fsS http://127.0.0.1:18080/

# 登录外生命周期
sudo loginctl enable-linger appsvc
loginctl show-user appsvc -p Linger

# 日志
journalctl --user-unit=report.service -b --no-pager
```

**静态验证声明：** 本章依据 RHEL 9 课程、Red Hat 容器文档、Podman 4.6.1 Quadlet 手册和 systemd 手册进行静态核对。未连接 RHEL 9 虚拟机，未执行真实注销、冷启动、端口请求和容器重建测试；这些项目已写入质量报告。

</section>
