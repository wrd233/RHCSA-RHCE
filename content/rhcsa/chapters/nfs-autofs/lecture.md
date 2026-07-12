---
title: "第九章 网络文件系统与自动挂载"
chapter_id: RHCSA-NFS
exam: RHCSA
validation: static-verified
sources: [RH134-RHEL9, RHCSA-Course-24, RHCSA9-Mock]
---

# 第九章　网络文件系统与自动挂载

NFS 把远端导出接入本机目录树，autofs 则在访问路径时按需建立挂载。两者的关键不是目录是否存在，而是远端导出、客户端包、当前挂载、持久条目和触发行为是否对应。

**[概念]** NFS export 是服务端公布的共享路径；客户端 mount 将服务器与导出路径映射到本地目录。网络中断、服务端权限和 root_squash 都会影响最终功能。

**[概念]** autofs master map 指向子 map；indirect map 在父目录下按 key 创建挂载，direct map 用完整路径作为 key。未访问时 findmnt 无结果可以是正常按需状态。

**[操作语义]** `showmount -e` 查询传统导出列表，`mount -t nfs` 建立当前挂载，`findmnt -t nfs,nfs4` 读取真实挂载关系。

**[操作语义]** `automount -m` 展开有效 map，访问 key 触发挂载；`systemctl reload autofs` 重新读取映射。

<section class="topic knowledge" id="RHCSA-NFS-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> NFS 路径、版本与身份边界

### ① [知识点] 客户端看到的是远端文件系统

`server:/export/path` 是挂载源，本地目录只是接入点。目录原有内容会被挂载遮蔽；卸载后重新出现。NFSv4 可能使用服务端伪根，`showmount` 结果不是所有 NFSv4 环境的唯一真相。

### ② [知识点] root_squash 改变远端 root 身份

服务端默认常把客户端 root 映射为匿名身份，避免远端 root 获得服务端 root 权限。客户端 chmod 失败不应通过关闭 root_squash 解决；按导出策略、远端所有者和实际业务用户判断。

### ③ [验证点] 分开验证发现、挂载和读写

```bash
showmount -e servera
findmnt /mnt/share
nfsstat -m
sudo -u alice touch /mnt/share/client-test
```
发现导出不能证明可挂载，当前挂载不能证明题目身份可写。

**[Cheatsheet]** 导出发现 `showmount -e`；当前源 `findmnt`；选项/版本 `nfsstat -m`；最后用目标身份验证读写。

</section>

<section class="topic operation" id="RHCSA-NFS-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 建立当前与 fstab NFS 挂载

### ① [操作点] 查询后建立当前挂载

安装 `nfs-utils`，确认名称解析与导出，再创建空挂载点。`-t nfs` 指定类型，`-o` 只添加题目需要的版本或选项。

```bash
dnf install nfs-utils
showmount -e servera
mkdir -p /mnt/shared
mount -t nfs servera:/exports/shared /mnt/shared
```

### ② [操作点] 写入持久条目

```fstab
servera:/exports/shared  /mnt/shared  nfs  defaults,_netdev  0  0
```

`_netdev` 表达依赖网络，但不自动修复服务器不可达。是否使用 `nofail`、`x-systemd.automount` 必须由题意决定。

### ③ [验证点] 当前、持久与远端功能

```bash
systemctl daemon-reload
findmnt --verify
umount /mnt/shared
mount -a
findmnt /mnt/shared
```
卸载再 mount -a 能证明条目确实建立挂载；仍需读取或写入远端文件。

**[Cheatsheet]** 当前：`mount -t nfs`；持久：fstab + `_netdev`；重载、verify、卸载后 `mount -a`；最终 `findmnt` 与目标身份功能测试。

</section>

<section class="topic operation" id="RHCSA-NFS-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 配置 autofs indirect map

### ① [操作点] 建立 master 与子 map

```text
# /etc/auto.master.d/exam.autofs
/shares  /etc/auto.shares  --timeout=60

# /etc/auto.shares
docs  -fstype=nfs,rw  servera:/exports/docs
```

访问 `/shares/docs` 才触发挂载。indirect map 的 key 是 `docs`，不是完整路径。

### ② [操作点] 校验并加载

```bash
automount -m
systemctl enable --now autofs
systemctl reload autofs
```

### ③ [验证点] 触发前、触发后与超时

```bash
findmnt /shares/docs
ls /shares/docs
findmnt /shares/docs
journalctl -u autofs -b
```
触发前无具体 NFS mount 可以正常；访问后必须出现正确源。超时卸载后再次访问应能重新挂载。

**[Cheatsheet]** master 指父目录和 map；map 的 key 形成子路径；`automount -m` 查有效映射；访问触发后用 `findmnt` 核对源。

</section>

<section class="topic diagnosis" id="RHCSA-NFS-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 根据症状区分解析、导出、权限与触发层

### ① [诊断点] No route 或名称失败
先用 `getent hosts`、`ip route get` 和端口连接检查网络，不修改 map 路径掩盖连接问题。

### ② [诊断点] access denied by server
核对客户端请求的导出路径、来源网络和服务端 export 权限；客户端目录 chmod 无法改变服务端拒绝。

### ③ [诊断点] autofs 路径存在但未挂载
实际访问 key，查看 `automount -m` 和 autofs journal。indirect key、完整远端路径或 map 语法错误是不同层。

**[Cheatsheet]** 解析→路由→服务端导出→客户端包/挂载→身份权限；autofs 再加 master/map/触发三层。

</section>

<section class="classic-task task-page" id="RHCSA-NFS-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 提供一个持久共享和一个按需共享

servera 导出 `/exports/team` 与 `/exports/home/&`。把 team 持久挂载到 `/srv/team`；为用户路径配置 indirect autofs，使访问 `/remote/alice` 时挂载对应远端目录。不得把按需共享写成永久常驻挂载。验收导出、当前/持久 team、map 展开、触发源、用户读写和超时后再触发。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-NFS-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 分别建立 fstab 与 indirect map

### ① [操作点] 调查与持久挂载
```bash
dnf install nfs-utils autofs
getent hosts servera; showmount -e servera
mkdir -p /srv/team
mount -t nfs servera:/exports/team /srv/team
```
写入 fstab 后执行 `daemon-reload`、`findmnt --verify`、卸载与 `mount -a`。

### ② [操作点] 配置按需用户目录
```text
/remote  /etc/auto.remote
*  -fstype=nfs,rw  servera:/exports/home/&
```
`*` 捕获 key，`&` 代入远端路径。运行 `automount -m`，启用 autofs。

### ③ [验证点] 触发和身份功能
```bash
ls /remote/alice
findmnt /remote/alice
sudo -u alice test -r /remote/alice
```
等待超时后再次访问并检查 journal。

**[Cheatsheet]** team：fstab 闭环；remote：master + wildcard map + 触发；两者都核对远端源和目标身份。

</section>

<section class="topic closing" id="RHCSA-NFS-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 远端源、当前挂载和触发策略必须分开

NFS 题先证明网络与导出，再证明客户端挂载和实际身份功能；autofs 题则把未触发状态视为正常候选，通过访问与 findmnt 证明按需行为。持久 fstab 与 autofs map 是两种不同生命周期，不互相替代。

</section>
