from content_factory import write_chapter
def c(q,a,e="",t="command",p="P0"): return(q,a,e,t,p)

write_chapter(
 track="rhcsa",slug="boot-recovery",number="第十一章",title="启动过程、Target 与系统恢复",chapter_id="RHCSA-BOOT",
 sources=["RH134-RHEL9","RHCSA-Course-18","RHCSA9-Mock"],
 intro="启动恢复题在正常系统之外修改持久状态，任何路径、挂载或 SELinux 判断错误都可能让下一次启动继续失败。本章把 firmware、boot loader、kernel/initramfs、systemd target 与恢复根环境串成可验证链路。",
 concepts=["启动依次经过 firmware、boot loader、kernel/initramfs 和 systemd；target 是一组 unit 依赖的同步点，不是传统运行级别进程。", "rescue 提供较完整的单用户环境，emergency 更小；`rd.break` 在 initramfs 阶段中断，此时真实根通常挂在 `/sysroot` 且可能只读。"],
 semantics=["`systemctl get-default/set-default/isolate` 分别查询默认 target、改变下次启动目标和切换当前目标。", "恢复环境中 `mount -o remount,rw /sysroot`、`chroot /sysroot` 后才对真实系统执行 passwd、fstab 修复和持久配置。"],
 topics=[
 ("RHCSA-BOOT-K01","知识专题","启动阶段与 target 边界","""### ① [知识点] 每阶段失败证据不同
看不到 boot loader、kernel panic、initramfs 找不到根、systemd 进入 emergency 是不同层。journal 只覆盖内核/systemd 能记录的阶段。

### ② [知识点] 默认 target 与当前 target 分开
`set-default` 只改变下次启动链接；`isolate` 当前切换并停止无关 unit，可能断开图形或网络会话。

### ③ [验证点] 查询默认、当前与失败 unit
```bash
systemctl get-default
systemctl list-units --type=target --state=active
systemctl --failed
journalctl -b -p err
```""","默认 `get-default`；当前 active target；失败 unit 与本次启动 journal；`isolate` 有中断风险。"),
 ("RHCSA-BOOT-O01","操作专题","使用 rd.break 重置 root 口令","""### ① [操作点] 在 boot loader 临时编辑 kernel 行
在目标启动项按 `e`，在 linux 行末增加 `rd.break`，按环境提示继续。这是一次性参数，不修改永久 GRUB 配置。

### ② [操作点] 进入真实根并修改
```bash
mount -o remount,rw /sysroot
chroot /sysroot
passwd root
touch /.autorelabel
exit
exit
```
`chroot` 前运行 passwd 会修改 initramfs 环境而非真实系统。`/.autorelabel` 让下次启动重新标记，过程可能较久。

### ③ [验证点] 恢复 Enforcing 与登录
启动后确认 `getenforce`、root 认证和 `journalctl -b`。不能声称已实机登录；讲义只给静态操作闭环。""","rd.break → `/sysroot` 重挂 rw → chroot → passwd → `/.autorelabel` → 正常启动后核对 Enforcing 与认证。"),
 ("RHCSA-BOOT-O02","操作专题","在 emergency 中修复错误 fstab","""### ① [诊断点] 先从失败 unit 找条目
`systemctl --failed`、mount unit status 和 journal 指向无法挂载的路径/UUID。备份 fstab 后用 `blkid`、`lsblk -f` 核对真实对象。

### ② [操作点] 最小修正并验证
根为只读时先重挂 rw。修改错误 UUID、类型或选项，不用 `nofail` 掩盖必需挂载。
```bash
findmnt --verify
mount -a
systemctl daemon-reload
```

### ③ [验证点] 离开恢复环境前证明关键路径
用 `findmnt`、`df -hT` 和数据检查确认，随后 `systemctl default` 或重启。""","失败 unit/journal → blkid/lsblk → 最小修 fstab → verify + mount -a → findmnt/数据 → 返回 default。"),
 ("RHCSA-BOOT-D01","诊断专题","避免在恢复环境修改错误根","""### ① [诊断点] passwd 成功但口令没变
检查是否忘记 `chroot /sysroot`，以及真实根是否 rw。

### ② [诊断点] 修复后启动卡在 relabel
若创建 `/.autorelabel`，长时间重新标记可能正常；查看控制台而非强制重启。

### ③ [诊断点] 默认 target 正确但服务未起
target 只表达依赖集合，继续查具体 unit 的 enabled、condition 和 journal。""","先确认当前根与读写状态；再修改真实持久文件；relabel 要等待；target 成功不替代具体服务验证。"),
 ],
 task=("恢复 root 访问并修正启动挂载", "系统因错误 fstab 进入 emergency，且 root 口令未知。恢复访问，保留数据并修正目标 UUID，使系统进入 multi-user.target；SELinux 最终保持 Enforcing。不得删除文件系统或用 nofail 绕过必需挂载。验收真实根、口令修改、relabel 标记、fstab 静态/实际挂载和默认 target。"),
 solution=("在 initramfs 中建立真实根修改闭环","""### ① [操作点] rd.break 与 chroot
按启动项临时加 `rd.break`，重挂 `/sysroot` 为 rw，chroot 后修改 root 口令并创建 `/.autorelabel`。

### ② [操作点] 修复持久配置
在 chroot 内运行 `lsblk -f`/`blkid`，备份并编辑 `/etc/fstab`；执行 `findmnt --verify`。若设备可用，实际 `mount -a`。

### ③ [操作点] 设置目标并退出
```bash
systemctl set-default multi-user.target
```
退出两次继续启动。完成 relabel 后核对 get-default、失败 units、目标挂载和 Enforcing。""","真实根 rw/chroot → passwd/relabel → UUID 修正 → verify/mount → set-default → 启动后综合验收。"),
 closing=("恢复操作必须作用于真实持久系统","启动阶段决定证据入口，恢复环境决定路径语义。只要先确认 `/sysroot`、读写状态与 chroot，再修改口令、fstab 和 target，就能避免“命令成功但改错系统”。SELinux relabel 和启动后功能验证是恢复闭环的一部分。"),
 cards=[
c("RHEL 启动主链路是什么？","firmware → boot loader → kernel/initramfs → systemd/target。","失败证据按阶段不同。","process"),
c("查询和设置默认 target 分别用什么？","`systemctl get-default`；`systemctl set-default <TARGET>`。","设置只影响下次启动。"),
c("`systemctl isolate` 的作用和风险是什么？","当前切换 target 并停止无关 units，可能中断会话。","不等于 set-default。","diagnosis"),
c("rd.break 后真实根通常在哪里？","`/sysroot`。","先确认并重挂 rw。","concept"),
c("重挂真实根为读写的命令是什么？","`mount -o remount,rw /sysroot`","随后 chroot。"),
c("为什么必须 `chroot /sysroot` 后再 passwd？","否则可能修改 initramfs 环境而非真实系统。","命令成功也可能作用对象错误。","diagnosis"),
c("重置口令后创建 `/.autorelabel` 的目的是什么？","让下次启动对真实文件系统重新进行 SELinux 标记。","relabel 可能耗时。","verification"),
c("修复 fstab 的证据顺序是什么？","失败 unit/journal → blkid/lsblk → 编辑 → findmnt --verify → mount -a。","不先重启。","process"),
c("fstab 必需挂载失败时能否默认加 nofail？","不能；这改变要求并掩盖错误。","修正真实 UUID/类型/选项。","diagnosis"),
c("查看本次启动错误与失败 units 用什么？","`journalctl -b -p err`；`systemctl --failed`。","再进入具体 unit。"),
c("passwd 显示成功但重启后旧口令仍有效，优先检查什么？","是否 chroot 到真实根、根是否 rw。","对象层错误。","diagnosis"),
c("默认 target 正确能否证明所有服务已运行？","不能；仍需查具体 unit active/enabled 与日志。","target 是依赖集合。","verification"),
c("rescue 与 emergency 的大致区别是什么？","rescue 环境较完整；emergency 更小且挂载更少。","按可用工具和题目选择。","comparison"),
c("root 口令恢复的完整骨架是什么？","rd.break → remount rw → chroot → passwd → autorelabel → exit。","启动后再验收。","process"),
 ]
)

write_chapter(
 track="rhcsa",slug="podman",number="第十二章",title="Podman 容器与持久运行",chapter_id="RHCSA-PODMAN",
 sources=["RH134-RHEL9","Podman-Course","RHCSA9-Mock"],
 intro="Podman 以普通用户运行容器时，镜像、容器、宿主目录、端口和用户级 systemd 各有独立状态。本章以 rootless 服务为主线，强调卷标签、登录后之外的持久运行和容器内外双层验证。",
 concepts=["image 是只读模板，container 是镜像的运行实例；rootless 容器属于用户命名空间，宿主 UID、低端口和存储路径受用户权限约束。", "端口发布把宿主端口转发到容器端口；bind mount 把宿主路径暴露给容器。SELinux enforcing 下 `:Z` 为单容器私有重标记，`:z` 允许多个容器共享。"],
 semantics=["`podman pull/images/inspect` 管镜像证据，`podman run/ps/logs/exec` 管容器当前实例。", "Quadlet `.container` 或 `podman generate systemd` 生成的用户 unit 把容器目标写成 systemd 声明；`loginctl enable-linger` 允许用户退出后仍由 user manager 运行。"],
 topics=[
 ("RHCSA-PODMAN-K01","知识专题","镜像、容器、端口和存储层","""### ① [知识点] 镜像名称应包含可靠 registry/tag
短名解析依赖 registries 配置；题目给出完整引用时原样使用。digest 可证明不可变内容，tag 可能移动。

### ② [知识点] 宿主与容器端口方向不能反
`-p 8080:80` 是宿主 8080 到容器 80。容器内监听正确不代表宿主已发布。

### ③ [验证点] 分别查 inspect、监听和 HTTP
```bash
podman inspect web
podman port web
ss -lntp | grep ':8080'
curl -I http://localhost:8080/
```""","镜像看 images/inspect；实例看 ps/logs；映射看 podman port/ss；最终用协议请求。"),
 ("RHCSA-PODMAN-O01","操作专题","运行 rootless 容器并持久保存数据","""### ① [操作点] 用目标用户准备目录
```bash
install -d -m 0750 -o webuser -g webuser /home/webuser/site
sudo -iu webuser podman pull registry.example.com/web:9
```

### ② [操作点] 创建端口、环境和卷
```bash
podman run -d --name web -p 8080:80 \\
  -v /home/webuser/site:/usr/share/nginx/html:Z \\
  -e APP_ENV=exam registry.example.com/web:9
```

### ③ [验证点] 当前实例和数据
`podman ps`、`logs`、`inspect`、`port` 后从宿主 curl；重建容器前后检查宿主文件，证明数据不只存在于可写层。""","目标用户准备目录 → pull → run name/port/volume/env → ps/logs/inspect/port → 宿主 HTTP 与数据检查。"),
 ("RHCSA-PODMAN-O02","操作专题","用用户 systemd 持久运行容器","""### ① [操作点] 选择当前 RHEL 9 可用集成
较新 RHEL 9/Podman 优先 Quadlet：在 `~/.config/containers/systemd/web.container` 描述 Image、PublishPort、Volume，并 daemon-reload。题目/环境明确使用生成 unit 时可运行 `podman generate systemd --new --files --name web`。

### ② [操作点] 启用用户 unit 与 linger
```bash
loginctl enable-linger webuser
sudo -iu webuser systemctl --user daemon-reload
sudo -iu webuser systemctl --user enable --now web.service
```

### ③ [验证点] user manager、unit 和容器
查询 `loginctl show-user -p Linger`、`systemctl --user is-active/is-enabled`、`podman ps` 与 HTTP。仅容器当前 running 不证明注销或重启后运行。""","持久声明 → user daemon-reload → enable --now → linger → unit + 容器 + HTTP；当前 RHEL 9 优先按环境支持的 Quadlet。"),
 ("RHCSA-PODMAN-D01","诊断专题","从容器状态定位拉取、端口、权限或 SELinux","""### ① [诊断点] 容器立即退出
看 `podman ps -a`、logs 和 inspect 的 exit code/command，不反复 run 同名容器。

### ② [诊断点] permission denied on volume
检查目标用户路径权限、容器进程 UID 映射和 SELinux AVC；需要私有重标记时使用 `:Z`，不禁用 SELinux。

### ③ [诊断点] user service 登录后才运行
检查 linger、unit 所属用户、XDG/user manager 和 enabled 状态；root 的 systemctl 与 `systemctl --user` 不是同一管理器。""","退出看 ps -a/logs/inspect；卷拒绝查 DAC+UID 映射+SELinux；持久失败查 user unit/linger；不重建掩盖证据。"),
 ],
 task=("部署一个 rootless 持久 Web 容器", "以用户 webuser 使用指定完整镜像，发布宿主 8080 到容器 80，把现有站点目录持久映射并保持 SELinux Enforcing。容器应在用户退出和系统重启后由用户 systemd 管理。不得复制私有认证信息或把目录设为 777。验收镜像、实例、端口、卷标签、数据、unit、linger 和 HTTP。"),
 solution=("按用户、数据、实例和 systemd 四层部署","""### ① [操作点] 以 webuser 准备目录、登录 registry（如题目要求）并 pull 完整镜像。
### ② [操作点] 使用 `podman run -d --name web -p 8080:80 -v <HOST>:<CONTAINER>:Z`，检查 logs/inspect/curl。
### ③ [操作点] 写 Quadlet 或按环境生成 user unit，daemon-reload、enable --now，并由管理员 enable-linger。
### ④ [验证点] 查询 image ID、podman ps、port、宿主文件、user unit active/enabled、Linger=yes 和注销后 HTTP。""","用户身份 → 镜像 → 卷/端口实例 → 当前功能 → user systemd + linger → 注销/重启持久与数据验收。"),
 closing=("容器运行与服务持久性是两套状态","Podman 当前实例、宿主网络、持久目录、SELinux 标签和用户 systemd 必须分别证明。rootless 的关键是始终在目标用户上下文操作，并让 user manager 与 linger 承担生命周期，而不是用 root 重新创建同名容器。"),
 cards=[
 c("image 与 container 的区别是什么？","image 是只读模板，container 是其实例。","实例有独立运行状态。","concept"),
 c("`-p 8080:80` 的方向是什么？","宿主 8080 转发到容器 80。","宿主端口在前。","parameter"),
 c("bind mount 的 `:Z` 与 `:z` 区别是什么？",":Z 私有重标记；:z 允许多容器共享。","按共享边界选择。","comparison"),
 c("查看全部容器含已退出实例用什么？","`podman ps -a`","立即退出时先查。"),
 c("查看容器端口发布用什么？","`podman port <CONTAINER>`","再用 ss 与 curl 验证。","verification"),
 c("容器立即退出的证据入口是什么？","`podman ps -a`、`podman logs`、`podman inspect`。","不反复创建。","diagnosis"),
 c("卷 permission denied 的调查层是什么？","宿主 DAC、rootless UID 映射、SELinux 标签/AVC。","不 chmod 777 或禁用 SELinux。","diagnosis"),
 c("rootless 容器为什么要以目标用户运行 podman？","容器存储、用户命名空间和 user units 都属于该用户。","root 是另一套状态。","concept"),
 c("用户退出后仍运行 user service 的关键设置是什么？","`loginctl enable-linger <USER>`","另需 user unit enabled。"),
 c("用户 unit 与系统 unit 的 systemctl 区别是什么？","用户 unit 使用 `systemctl --user` 并在对应用户上下文。","管理器不同。","comparison"),
 c("容器 running 能否证明重启后运行？","不能；还要验证 user unit enabled 与 linger。","当前/持久分开。","verification"),
 c("完整容器验收骨架是什么？","image → ps/logs/inspect → port/ss → volume/data → user unit/linger → HTTP。","分层取证。","process"),
 ]
)

write_chapter(
 track="rhcsa",slug="comprehensive",number="第十三章",title="RHCSA 综合任务",chapter_id="RHCSA-COMPREHENSIVE",
 sources=["RHCSA9-Mock","RH124-RHEL9","RH134-RHEL9"],
 intro="综合题不引入新的命令体系，而是要求识别多个对象之间的依赖和交叉影响。本章用一台服务器的完整终态训练读题、风险排序、分层验证和最终清单。",
 concepts=["综合验收把身份、网络、仓库、服务、存储、SELinux、调度和容器视为共享同一主机状态的多个目标，后做的修改可能破坏先完成的题。", "证据矩阵把每项要求映射到当前状态、持久配置和功能验证，避免以一条成功命令覆盖多个评分点。"],
 semantics=["调查命令先建立共享对象图；最小修改只推进一个目标层；最终检查从题目原文逐项反查证据。"],
 topics=[
 ("RHCSA-COMPREHENSIVE-K01","知识专题","把题目编排为依赖图与风险队列","""### ① [知识点] 基础依赖先于业务
网络/解析影响仓库、NFS 与 SSH；仓库影响软件；身份影响权限和 rootless 容器；存储与 SELinux 影响服务数据。

### ② [知识点] 高风险写操作必须有证据门
磁盘初始化、网络切换、fstab、启动恢复和权限递归修改先记录基线与恢复路径。

### ③ [验证点] 每题记录当前、持久、功能三列
例如服务为 active/enabled/HTTP，挂载为 findmnt/fstab/data，防火墙为 runtime/permanent/remote request。""","先画依赖与共享对象；低风险基础先做；高风险操作设证据门；每题维护当前/持久/功能三列。"),
 ("RHCSA-COMPREHENSIVE-O01","操作专题","执行中保持局部闭环","""### ① [操作点] 完成一层立即验证
仓库刷新后再装包，服务语法通过后再启动，fstab verify/mount 后再继续，SELinux 规则应用后再测业务。

### ② [诊断点] 卡题保存缺失证据
记录最后错误、已证实层、未证实层和共享影响，不用删除/重建清空现场。

### ③ [验证点] 每次共享对象变化后回归相关题
修改 httpd 端口后回查 firewalld/SELinux；改变用户组后用新会话回查目录与容器。""","局部闭环 → 保存卡点 → 共享对象变化后回归；不把局部成功扩大。"),
 ("RHCSA-COMPREHENSIVE-O02","操作专题","完成最终一页检查","""### ① [验证点] 身份、网络和软件
`id/getent`、nmcli/ip/getent、dnf/rpm；确认题目值和持久性。

### ② [验证点] 服务、安全和调度
active/enabled/listen/function；firewalld 双态；SELinux Enforcing/规则/标签；cron 实际产物。

### ③ [验证点] 存储和容器
lsblk/pvs/vgs/lvs、findmnt/df/fstab、swapon；Podman image/container/volume/port/user unit/linger。

### ④ [边界] 重启前先跑静态检查
网络 profile、`findmnt --verify`、服务语法和恢复入口都成立后才决定是否重启。""","从原题逐项复核；静态配置→当前状态→功能→持久性；共享对象回归；重启不是第一排错。"),
 ],
 task=("把服务器配置为可综合验收的终态", "服务器需同时完成项目用户与共享目录、静态网络与仓库、HTTP 服务及非标准内容目录、XFS/LVM/Swap 持久存储、NFS autofs、周期健康检查、rootless 容器和默认 target。题目给定设备与地址必须按现场值使用，已有数据不得删除，SELinux 保持 Enforcing。请自行安排顺序并提供最终证据矩阵。"),
 solution=("按依赖和风险推进一条推荐路径","""### ① [操作点] 先调查网络、设备、身份、现有服务和挂载，建立共享对象表。
### ② [操作点] 完成网络/解析/仓库，再创建身份与目录；随后安装配置服务。
### ③ [操作点] 设备证据充分后完成分区/LVM/文件系统/fstab/Swap；再配置 NFS、SELinux、计划任务和容器。
### ④ [验证点] 每题使用本章三列表；运行服务语法、findmnt verify、Anki 中的各层命令，回查共享端口/路径/用户。重启前确认恢复路径。""","依赖图 → 基础连接 → 身份/软件 → 高风险存储 → 安全/调度/容器 → 证据矩阵 → 回归与持久性。"),
 closing=("最终答案是一组互相一致的系统状态","综合能力不是执行更多命令，而是让用户、路径、端口、设备和服务在当前与重启后保持一致。证据矩阵让每个评分点都有对应查询，也让交叉影响在交卷前被发现。"),
 cards=[
c("RHCSA 综合题首先应建立什么？","对象依赖图、共享影响表和高风险操作队列。","不从最长命令开始。","process"),
c("为什么网络与名称解析通常先于仓库/NFS/SSH？","后三者依赖可达地址和解析。","修改网络仍需恢复路径。","concept"),
c("综合题的三列证据是什么？","当前状态、持久配置、最终功能。","每项要求分别映射。","process"),
c("共享对象修改后为什么要回归？","后续端口、路径、组或服务变化可能破坏已完成题。","记录相关题号。","diagnosis"),
c("高风险存储操作的证据门是什么？","设备身份、签名/归属、已有数据、目标与恢复条件。","不足时停止写入。","process"),
c("最终检查应从哪里开始？","从题目原文逐项反查对象和证据。","不是从命令历史。","verification"),
c("重启前最少检查什么？","网络持久 profile、fstab verify/mount、关键服务语法和恢复入口。","重启不是通用排错。","verification"),
c("服务综合验收包含哪些层？","包/配置语法、active/enabled、监听、安全层、协议功能。","局部成功不替代整体。","process"),
c("存储综合验收包含哪些层？","设备/LVM、文件系统、当前挂载、fstab、容量和数据。","Swap 另查 swapon。","process"),
c("容器综合验收包含哪些层？","镜像、实例、端口、卷/数据、user unit、linger、HTTP。","rootless 身份一致。","process"),
c("卡题时应记录什么？","已证实层、缺失证据、最后错误和共享影响。","保留现场。","diagnosis"),
c("综合任务完成的判据是什么？","所有要求都有对象正确、功能成立且持久状态一致的证据。","命令执行过不等于完成。","verification"),
 ]
)

if __name__=="__main__": print("seeded final RHCSA chapters")
