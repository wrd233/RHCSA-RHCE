---
title: "第十一章 启动过程、Target 与系统恢复"
chapter_id: RHCSA-BOOT
exam: RHCSA
validation: static-verified
sources: [RH134-RHEL9, RHCSA-Course-18, RHCSA9-Mock]
---

# 第十一章　启动过程、Target 与系统恢复

启动恢复题在正常系统之外修改持久状态，任何路径、挂载或 SELinux 判断错误都可能让下一次启动继续失败。本章把 firmware、boot loader、kernel/initramfs、systemd target 与恢复根环境串成可验证链路。

**[概念]** 启动依次经过 firmware、boot loader、kernel/initramfs 和 systemd；target 是一组 unit 依赖的同步点，不是传统运行级别进程。

**[概念]** rescue 提供较完整的单用户环境，emergency 更小；`rd.break` 在 initramfs 阶段中断，此时真实根通常挂在 `/sysroot` 且可能只读。

**[操作语义]** `systemctl get-default/set-default/isolate` 分别查询默认 target、改变下次启动目标和切换当前目标。

**[操作语义]** 恢复环境中 `mount -o remount,rw /sysroot`、`chroot /sysroot` 后才对真实系统执行 passwd、fstab 修复和持久配置。

<section class="topic knowledge" id="RHCSA-BOOT-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 启动阶段与 target 边界

### ① [知识点] 每阶段失败证据不同
看不到 boot loader、kernel panic、initramfs 找不到根、systemd 进入 emergency 是不同层。journal 只覆盖内核/systemd 能记录的阶段。

### ② [知识点] 默认 target 与当前 target 分开
`set-default` 只改变下次启动链接；`isolate` 当前切换并停止无关 unit，可能断开图形或网络会话。

### ③ [验证点] 查询默认、当前与失败 unit
```bash
systemctl get-default
systemctl list-units --type=target --state=active
systemctl --failed
journalctl -b -p err
```

**[Cheatsheet]** 默认 `get-default`；当前 active target；失败 unit 与本次启动 journal；`isolate` 有中断风险。

</section>

<section class="topic operation" id="RHCSA-BOOT-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 使用 rd.break 重置 root 口令

### ① [操作点] 在 boot loader 临时编辑 kernel 行
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
启动后确认 `getenforce`、root 认证和 `journalctl -b`。不能声称已实机登录；讲义只给静态操作闭环。

**[Cheatsheet]** rd.break → `/sysroot` 重挂 rw → chroot → passwd → `/.autorelabel` → 正常启动后核对 Enforcing 与认证。

</section>

<section class="topic operation" id="RHCSA-BOOT-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 在 emergency 中修复错误 fstab

### ① [诊断点] 先从失败 unit 找条目
`systemctl --failed`、mount unit status 和 journal 指向无法挂载的路径/UUID。备份 fstab 后用 `blkid`、`lsblk -f` 核对真实对象。

### ② [操作点] 最小修正并验证
根为只读时先重挂 rw。修改错误 UUID、类型或选项，不用 `nofail` 掩盖必需挂载。
```bash
findmnt --verify
mount -a
systemctl daemon-reload
```

### ③ [验证点] 离开恢复环境前证明关键路径
用 `findmnt`、`df -hT` 和数据检查确认，随后 `systemctl default` 或重启。

**[Cheatsheet]** 失败 unit/journal → blkid/lsblk → 最小修 fstab → verify + mount -a → findmnt/数据 → 返回 default。

</section>

<section class="topic diagnosis" id="RHCSA-BOOT-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 避免在恢复环境修改错误根

### ① [诊断点] passwd 成功但口令没变
检查是否忘记 `chroot /sysroot`，以及真实根是否 rw。

### ② [诊断点] 修复后启动卡在 relabel
若创建 `/.autorelabel`，长时间重新标记可能正常；查看控制台而非强制重启。

### ③ [诊断点] 默认 target 正确但服务未起
target 只表达依赖集合，继续查具体 unit 的 enabled、condition 和 journal。

**[Cheatsheet]** 先确认当前根与读写状态；再修改真实持久文件；relabel 要等待；target 成功不替代具体服务验证。

</section>

<section class="classic-task task-page" id="RHCSA-BOOT-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 恢复 root 访问并修正启动挂载

系统因错误 fstab 进入 emergency，且 root 口令未知。恢复访问，保留数据并修正目标 UUID，使系统进入 multi-user.target；SELinux 最终保持 Enforcing。不得删除文件系统或用 nofail 绕过必需挂载。验收真实根、口令修改、relabel 标记、fstab 静态/实际挂载和默认 target。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-BOOT-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 在 initramfs 中建立真实根修改闭环

### ① [操作点] rd.break 与 chroot
按启动项临时加 `rd.break`，重挂 `/sysroot` 为 rw，chroot 后修改 root 口令并创建 `/.autorelabel`。

### ② [操作点] 修复持久配置
在 chroot 内运行 `lsblk -f`/`blkid`，备份并编辑 `/etc/fstab`；执行 `findmnt --verify`。若设备可用，实际 `mount -a`。

### ③ [操作点] 设置目标并退出
```bash
systemctl set-default multi-user.target
```
退出两次继续启动。完成 relabel 后核对 get-default、失败 units、目标挂载和 Enforcing。

**[Cheatsheet]** 真实根 rw/chroot → passwd/relabel → UUID 修正 → verify/mount → set-default → 启动后综合验收。

</section>

<section class="topic closing" id="RHCSA-BOOT-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 恢复操作必须作用于真实持久系统

启动阶段决定证据入口，恢复环境决定路径语义。只要先确认 `/sysroot`、读写状态与 chroot，再修改口令、fstab 和 target，就能避免“命令成功但改错系统”。SELinux relabel 和启动后功能验证是恢复闭环的一部分。

</section>
