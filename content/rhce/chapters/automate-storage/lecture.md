---
title: "第十章 自动化存储、文件系统与挂载"
chapter_id: RHCE-STORAGE
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE9-Mock, Ansible-Documentation]
---

# 第十章　自动化存储、文件系统与挂载

存储自动化必须面对每台主机设备条件不同和写操作不可逆。模块能保证对象 state，却不能判断题目中的设备是否安全；设备证据、容量来源、文件系统和 mount 双态仍需逐层验证。

**[概念]** community.general.lvg/lvol 管 VG/LV，community.general.filesystem 管签名，ansible.posix.mount 管 fstab 与当前挂载；实际 FQCN/字段以已安装 Collection 为准。

**[概念]** 容量可表达绝对值、增量或百分比。自动化应描述目标总量，避免每次运行都增加；扩容文件系统需要 resizefs 或专用步骤，XFS 不缩小。

**[操作语义]** 先 gather facts/lsblk 调查，但不从设备名模式推定空闲。模块 state present 只推进对应层；远端 `pvs/vgs/lvs/blkid/findmnt/df` 形成验收。

<section class="topic knowledge" id="RHCE-STORAGE-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 设备安全不是模块自动判断

### ① [知识点] 设备安全不是模块自动判断
lvg 的 pvs 参数会初始化/加入设备；题目设备不确定时先 assert 事实和人工证据门。不要自动 wipefs/force。

### ② [知识点] 目标大小避免增量漂移
lvol size 写目标容量或百分比；使用扩容参数时确认模块幂等语义。每次 `+1G` 的命令式 shell 会持续增长。

### ③ [验证点] LVM、文件系统和挂载三层
lvs 变大不代表 df 变大；mount state mounted/ephemeral/present 的当前与 fstab 语义不同，按模块文档选择。

**[Cheatsheet]** 设备安全不是模块自动判断；目标大小避免增量漂移；LVM、文件系统和挂载三层

</section>

<section class="topic operation" id="RHCE-STORAGE-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 用变量描述每主机布局

### ① [操作点] 用变量描述每主机布局
host_vars 定义 devices、vg、lv、size、fstype、mount；assert 设备键存在和尺寸条件。

### ② [操作点] 按依赖创建
lvg → lvol → filesystem → file mountpoint → mount。已有 filesystem 不重建；扩容使用 resizefs 并保留数据。

### ③ [验证点] 执行前后与幂等
limit 单主机，远端查对象/UUID/fstab/findmnt/df/数据；第二次无 changed，再扩全组。

**[Cheatsheet]** 用变量描述每主机布局；按依赖创建；执行前后与幂等

</section>

<section class="topic diagnosis" id="RHCE-STORAGE-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> VG 不存在或设备不存在

### ① [诊断点] VG 不存在或设备不存在
用 hostvars/Facts 与远端 lsblk 证明条件，fail/assert 给明确消息，不用 ignore_errors。

### ② [诊断点] LV 变大 df 不变
文件系统 resize 未完成；按类型执行模块 resize 或 xfs_growfs，不继续增加 LV。

### ③ [诊断点] mount 每次 changed
检查 src 是否稳定（UUID/设备路径）、opts 顺序、state 与 fstab 现状；不要用 shell mount。

**[Cheatsheet]** VG 不存在或设备不存在；LV 变大 df 不变；mount 每次 changed

</section>

<section class="topic knowledge" id="RHCE-STORAGE-X01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 设备事实、容量单位与失败保护

### ① [知识点] ansible_devices 不是安全空闲证明
Facts 可给设备大小、分区和型号，但未必包含所有签名/LVM/挂载关系。真正初始化前仍需受控 `lsblk/blkid/pvs` 证据或题目明确保证。

### ② [参数点] 容量字符串保持题意单位
`size: 2g`、百分比和 resizefs 行为由当前 collection 模块定义。extent 题若模块不能精确表达，应计算并 assert 结果，不用近似容量悄悄改变目标。

### ③ [失败边界] 先 fail 再做破坏性任务
用 assert 检查设备变量存在、VG 条件和目标大小；block/rescue 可输出明确错误，但不能在 rescue 中格式化另一块猜测设备。

**[Cheatsheet]** Facts 只做初筛；容量保持题意单位并 assert；破坏性 task 前显式 fail，rescue 不猜替代设备。

</section>

<section class="classic-task task-page" id="RHCE-STORAGE-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 按主机变量创建并挂载逻辑卷

在指定主机使用给定空闲设备创建 VG/LV/ext4 或 XFS 并持久挂载；空间不足时输出明确失败，不得格式化未知设备。随后扩容并保留标记数据。验收模块结果、三层容量、fstab、挂载和幂等。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-STORAGE-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 把设备差异放入变量并设置证据门

### ① [操作点] host_vars 描述布局，assert 设备/容量前提。
### ② [操作点] lvg/lvol/filesystem/mount 按依赖；扩容 resizefs。
### ③ [验证点] pvs/vgs/lvs、blkid、findmnt/df、标记校验，第二次执行。

**[Cheatsheet]** 变量/设备证据 → LVM → filesystem → mount → 数据 → 扩容 → 幂等。

</section>

<section class="topic closing" id="RHCE-STORAGE-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 幂等模块不能替代设备风险判断

模块擅长比较已知对象状态，但初始化哪个设备仍由数据和证据决定。按依赖创建并分层验收，才能避免自动化放大破坏性错误。

</section>
