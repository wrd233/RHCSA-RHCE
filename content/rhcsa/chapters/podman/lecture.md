---
title: "第十二章 Podman 容器与持久运行"
chapter_id: RHCSA-PODMAN
exam: RHCSA
validation: static-verified
sources: [RH134-RHEL9, Podman-Course, RHCSA9-Mock]
---

# 第十二章　Podman 容器与持久运行

Podman 以普通用户运行容器时，镜像、容器、宿主目录、端口和用户级 systemd 各有独立状态。本章以 rootless 服务为主线，强调卷标签、登录后之外的持久运行和容器内外双层验证。

**[概念]** image 是只读模板，container 是镜像的运行实例；rootless 容器属于用户命名空间，宿主 UID、低端口和存储路径受用户权限约束。

**[概念]** 端口发布把宿主端口转发到容器端口；bind mount 把宿主路径暴露给容器。SELinux enforcing 下 `:Z` 为单容器私有重标记，`:z` 允许多个容器共享。

**[操作语义]** `podman pull/images/inspect` 管镜像证据，`podman run/ps/logs/exec` 管容器当前实例。

**[操作语义]** Quadlet `.container` 或 `podman generate systemd` 生成的用户 unit 把容器目标写成 systemd 声明；`loginctl enable-linger` 允许用户退出后仍由 user manager 运行。

<section class="topic knowledge" id="RHCSA-PODMAN-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 镜像、容器、端口和存储层

### ① [知识点] 镜像名称应包含可靠 registry/tag
短名解析依赖 registries 配置；题目给出完整引用时原样使用。digest 可证明不可变内容，tag 可能移动。

### ② [知识点] 宿主与容器端口方向不能反
`-p 8080:80` 是宿主 8080 到容器 80。容器内监听正确不代表宿主已发布。

### ③ [验证点] 分别查 inspect、监听和 HTTP
```bash
podman inspect web
podman port web
ss -lntp | grep ':8080'
curl -I http://localhost:8080/
```

**[Cheatsheet]** 镜像看 images/inspect；实例看 ps/logs；映射看 podman port/ss；最终用协议请求。

</section>

<section class="topic operation" id="RHCSA-PODMAN-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 运行 rootless 容器并持久保存数据

### ① [操作点] 用目标用户准备目录
```bash
install -d -m 0750 -o webuser -g webuser /home/webuser/site
sudo -iu webuser podman pull registry.example.com/web:9
```

### ② [操作点] 创建端口、环境和卷
```bash
podman run -d --name web -p 8080:80 \
  -v /home/webuser/site:/usr/share/nginx/html:Z \
  -e APP_ENV=exam registry.example.com/web:9
```

### ③ [验证点] 当前实例和数据
`podman ps`、`logs`、`inspect`、`port` 后从宿主 curl；重建容器前后检查宿主文件，证明数据不只存在于可写层。

**[Cheatsheet]** 目标用户准备目录 → pull → run name/port/volume/env → ps/logs/inspect/port → 宿主 HTTP 与数据检查。

</section>

<section class="topic operation" id="RHCSA-PODMAN-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 用用户 systemd 持久运行容器

### ① [操作点] 选择当前 RHEL 9 可用集成
较新 RHEL 9/Podman 优先 Quadlet：在 `~/.config/containers/systemd/web.container` 描述 Image、PublishPort、Volume，并 daemon-reload。题目/环境明确使用生成 unit 时可运行 `podman generate systemd --new --files --name web`。

### ② [操作点] 启用用户 unit 与 linger
```bash
loginctl enable-linger webuser
sudo -iu webuser systemctl --user daemon-reload
sudo -iu webuser systemctl --user enable --now web.service
```

### ③ [验证点] user manager、unit 和容器
查询 `loginctl show-user -p Linger`、`systemctl --user is-active/is-enabled`、`podman ps` 与 HTTP。仅容器当前 running 不证明注销或重启后运行。

**[Cheatsheet]** 持久声明 → user daemon-reload → enable --now → linger → unit + 容器 + HTTP；当前 RHEL 9 优先按环境支持的 Quadlet。

</section>

<section class="topic diagnosis" id="RHCSA-PODMAN-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 从容器状态定位拉取、端口、权限或 SELinux

### ① [诊断点] 容器立即退出
看 `podman ps -a`、logs 和 inspect 的 exit code/command，不反复 run 同名容器。

### ② [诊断点] permission denied on volume
检查目标用户路径权限、容器进程 UID 映射和 SELinux AVC；需要私有重标记时使用 `:Z`，不禁用 SELinux。

### ③ [诊断点] user service 登录后才运行
检查 linger、unit 所属用户、XDG/user manager 和 enabled 状态；root 的 systemctl 与 `systemctl --user` 不是同一管理器。

**[Cheatsheet]** 退出看 ps -a/logs/inspect；卷拒绝查 DAC+UID 映射+SELinux；持久失败查 user unit/linger；不重建掩盖证据。

</section>

<section class="classic-task task-page" id="RHCSA-PODMAN-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 部署一个 rootless 持久 Web 容器

以用户 webuser 使用指定完整镜像，发布宿主 8080 到容器 80，把现有站点目录持久映射并保持 SELinux Enforcing。容器应在用户退出和系统重启后由用户 systemd 管理。不得复制私有认证信息或把目录设为 777。验收镜像、实例、端口、卷标签、数据、unit、linger 和 HTTP。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-PODMAN-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 按用户、数据、实例和 systemd 四层部署

### ① [操作点] 以 webuser 准备目录、登录 registry（如题目要求）并 pull 完整镜像。
### ② [操作点] 使用 `podman run -d --name web -p 8080:80 -v <HOST>:<CONTAINER>:Z`，检查 logs/inspect/curl。
### ③ [操作点] 写 Quadlet 或按环境生成 user unit，daemon-reload、enable --now，并由管理员 enable-linger。
### ④ [验证点] 查询 image ID、podman ps、port、宿主文件、user unit active/enabled、Linger=yes 和注销后 HTTP。

**[Cheatsheet]** 用户身份 → 镜像 → 卷/端口实例 → 当前功能 → user systemd + linger → 注销/重启持久与数据验收。

</section>

<section class="topic closing" id="RHCSA-PODMAN-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 容器运行与服务持久性是两套状态

Podman 当前实例、宿主网络、持久目录、SELinux 标签和用户 systemd 必须分别证明。rootless 的关键是始终在目标用户上下文操作，并让 user manager 与 linger 承担生命周期，而不是用 root 重新创建同名容器。

</section>
