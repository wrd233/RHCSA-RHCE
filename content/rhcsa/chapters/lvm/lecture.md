---
title: "第25章 LVM 逻辑存储"
chapter_id: RHCSA-25
slug: lvm
exam: RHCSA
part: "第六篇 块存储与网络存储"
version: RHEL9
status: integrated
validation: static
live_test: not_performed
sources:
  - RH134-RHEL9
  - Red-Hat-RHEL9-Configuring-and-Managing-Logical-Volumes
  - Red-Hat-RHEL9-Managing-File-Systems
  - lvm2-man-pages
  - RHCSA9-Mock-LVM
  - RHCSA-LVM-Legacy-Chapter
---

<!--
维护说明：
- 本文件是 RHCSA-25 讲义内容真源。
- 章节 ID、专题 ID、来源与静态核对状态属于维护层，正式阅读时不要求记忆。
- 本章没有连接 RHEL 9 虚拟机，所有命令均依据课程、官方文档、man page、细分课件与任务逻辑静态核对。
- 示例设备名、VG/LV 名称和路径只用于明确教学场景，不代表任何真实考试环境。
-->

# 第25章　LVM 逻辑存储

一块磁盘有空闲容量，并不等于应用已经获得了一个可安全使用的目录。真正进入业务路径之前，容量可能要依次经过块设备、物理卷、卷组、逻辑卷、文件系统和挂载点。扩容时也不是只把一个数字改大：卷组必须先有可分配的 extent，逻辑卷要获得新的块空间，文件系统再识别并使用这些空间，最后还要证明当前挂载源和原有数据都没有发生错误变化。

本章围绕两条任务链展开：从确认空闲的设备创建指定 extent 的 LV；在保留已有数据的前提下扩展现有 LV 和文件系统。分区、文件系统通用机制和 `/etc/fstab` 的完整语法分别归第 22、23、24 章。本章只调用这些已经建立的前置能力，不复制相邻章节。

**[概念]** Physical Volume（PV）是经过 LVM 初始化、能够被卷组使用的设备或分区。`pvcreate` 会写入 LVM 标签与元数据；它不是“只做标记”的无风险查询命令。

**[概念]** Volume Group（VG）把一个或多个 PV 的容量汇聚成空间池，并按固定大小的 Physical Extent（PE）管理。LV 的扩展空间来自 VG 中尚未分配的 PE，而不是来自系统中任意一块“看起来空闲”的磁盘。

**[概念]** Logical Volume（LV）是从 VG 中分配出的虚拟块设备。普通线性 LV 使用 Logical Extent（LE）表达分配单位，在同一 VG 内通常可按一个 LE 映射一个 PE 来理解。

**[概念]** 文件系统和挂载点位于 LV 之上。`lvs` 显示 LV 变大，只能证明块设备层发生变化；只有文件系统增长并且目标目录实际挂载到该文件系统，应用才能使用新增空间。

**[概念]** LVM 元数据描述 PV、VG、LV 和 extent 的关系。创建、扩展和删除命令直接改变这些对象；`pvs`、`vgs`、`lvs` 则把不同层次的状态输出为可定制报告。

**[操作语义]** `lsblk` 与 `findmnt` 从设备树和目录使用路径观察对象；`pvs`、`vgs`、`lvs` 分别读取 PV、VG、LV 状态；`df` 读取已挂载文件系统呈现的容量。它们不能互相替代。

**[操作语义]** `pvcreate`、`vgcreate`、`lvcreate` 建立对象链；`vgextend` 为已有 VG 增加容量来源；`lvextend` 从 VG 的空闲 PE 中为已有 LV 分配空间。

**[操作语义]** `lvextend -r` 尝试在扩大 LV 后继续扩大受支持的文件系统。它跨越两个对象层次，因此仍要分别验证 LV 与文件系统，不能把命令退出成功扩大为完整终态正确。

**[操作语义]** XFS 使用 `xfs_growfs` 增长且不能原地缩小；ext4 可使用 `resize2fs` 增长。缩容涉及文件系统先决条件和高数据风险，不是扩容流程的简单反向操作。

<section class="topic knowledge" id="RHCSA-25-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 从设备到业务目录：六层对象不能混成一个“磁盘”

学习 LVM 最容易出现的误区，是把设备、PV、VG、LV、文件系统和挂载点都简称为“磁盘空间”。这六层分别回答“容量在哪里”“由谁管理”“怎样汇聚”“划给谁”“如何组织数据”和“通过哪个目录访问”。创建或扩容时，只有明确当前命令改变哪一层，才能判断下一条证据应该从哪里取得。

### ① <span class="point-label">[知识点]</span> 设备是容量载体，PV 是 LVM 管理身份

`/dev/vdb1` 是一个块设备节点。它可能是空闲分区，也可能已经包含文件系统、属于某个 VG、作为 swap 使用，或者正被挂载。只有在确认没有需要保留的数据和冲突关系后，才可以把它初始化为 PV。

```text
块设备 /dev/vdb1
  ├─ 可能已有文件系统签名
  ├─ 可能已经挂载
  ├─ 可能已经是 PV
  └─ 只有通过安全调查后，才决定是否执行 pvcreate
```

`pvcreate` 写入 LVM 标签和元数据，使设备能够加入 VG。PV 可以位于整个磁盘，也可以位于分区；本章不规定唯一布局，而是要求遵守题目和当前系统证据。

### ② <span class="point-label">[知识点]</span> VG 是容量池，PE 是它的固定分配单位

VG 把一个或多个 PV 汇聚为一个逻辑容量池。创建 VG 时会确定 PE 大小。VG 中已分配的 PE 被 LV 使用，未分配的 PE 构成后续创建和扩展 LV 的直接容量来源。

<div class="layer-diagram" role="img" aria-label="PV 汇入 VG，VG 按 PE 分配给 LV">
  <div class="layer-row"><span class="layer-name">PV</span><span class="layer-box">/dev/vdb1</span><span class="plus">+</span><span class="layer-box">/dev/vdc1</span></div>
  <div class="arrow">↓ 汇入</div>
  <div class="layer-row"><span class="layer-name">VG</span><span class="layer-wide">projectvg：PE × N</span></div>
  <div class="arrow">↓ 分配 LE</div>
  <div class="layer-row"><span class="layer-name">LV</span><span class="layer-box accent">projectlv</span><span class="layer-box muted">VG Free</span></div>
</div>

“磁盘还有未分区空间”不等于“目标 VG 有空闲 PE”；“另一个 VG 有剩余容量”也不能直接供当前 LV 使用。扩容前的关键证据是目标 VG 的 `vg_free` 或 `vg_free_count`。

### ③ <span class="point-label">[知识点]</span> LV 是虚拟块设备，LE 表达它获得的分配量

LV 从 VG 中获得 LE，并向上层呈现为块设备。常见路径包括 `/dev/<VG>/<LV>` 和 `/dev/mapper/<VG>-<LV>`；应从 `lvs`、`lsblk` 或 `findmnt` 读取实际路径，不靠记忆拼接。

LV 可以存在但没有文件系统，也可以作为 swap、数据库原始设备或其他上层的成员。本章经典任务在 LV 上创建文件系统，但不能由此推导出“所有 LV 都必须格式化”。

### ④ <span class="point-label">[知识点]</span> 文件系统把块设备变成数据空间，挂载点把它接入目录树

文件系统负责目录、文件、元数据和空间分配；挂载点只是目录树中的接入口。目录存在不能证明挂载成功。若 `/srv/project` 只是根文件系统上的普通目录，应用仍然可以向其中写入数据，这会制造“目录可写所以任务成功”的危险假象。

```bash
findmnt /srv/project
df -hT /srv/project
```

第一条确认当前挂载源，第二条确认该挂载文件系统的类型和容量。持久挂载的完整机制归第 24 章；本章只把它作为最终证据链的一部分。

### ⑤ <span class="point-label">[知识点]</span> 从挂载点反向定位，比从设备名正向猜测更安全

面对“扩展 `/srv/reports`”之类的任务，目录才是业务对象。稳定的反向链是：

```text
/srv/reports
→ findmnt 确认文件系统源和类型
→ lvs/lsblk 确认对应 LV
→ vgs 确认所属 VG 和空闲 PE
→ pvs 确认 VG 的容量来自哪些 PV
```

若 `findmnt` 显示的是 NFS 等远程文件系统，应停止本地 LVM 操作并转入第 26 章。若源是普通分区而不是 LV，也不能强行套用 LVM 扩容流程。

**[Cheatsheet]** 设备提供容量；PV 提供 LVM 身份；VG 汇聚并按 PE 管理；LV 获得 LE 并呈现块设备；文件系统组织数据；挂载点提供目录入口。扩容业务目录时，从 `findmnt` 反向找到 LV 和 VG。

</section>

<section class="topic knowledge" id="RHCSA-25-K02" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> PE、LE、`-L`、`-l` 与加号：容量题真正考什么

LVM 可以按人类容量单位表达，也可以按 extent 数量表达。两者没有高低之分，关键是命令是否直接表达题目要求，以及操作是在设定目标总量还是增加增量。考试中漏写一个加号，可能让命令的含义完全改变。

### ① <span class="point-label">[知识点]</span> PE 属于 VG，LE 属于 LV 分配视图

PE 大小是 VG 属性。普通线性 LV 中，可以用一个 LE 对应一个 PE 的模型理解容量：

```text
LV 标称容量 = LE 数量 × VG 的 PE 大小
```

例如 PE 为 16 MiB，LV 使用 50 个 extent：

```text
50 × 16 MiB = 800 MiB
```

若再增加 20 个 extent：

```text
(50 + 20) × 16 MiB = 1120 MiB
```

### ② <span class="point-label">[知识点]</span> `-L` 按容量，`-l` 按 extent 或百分比

```bash
lvcreate -L 800M -n projectlv projectvg
lvcreate -l 50   -n projectlv projectvg
```

第一条直接表达 800 MiB，第二条直接表达 50 个 extent。题目明确写“50 个 PE/extent”时应使用小写 `-l`；只给出 2 GiB 等容量时使用大写 `-L` 更自然。

### ③ <span class="point-label">[知识点]</span> 无加号是目标总量，有加号是相对增量

```text
-l 70      把目标总 extent 数设为 70
-l +20     在当前基础上增加 20 个 extent
-L 2G      把目标总大小设为 2 GiB
-L +512M   在当前基础上增加 512 MiB
```

扩展一个当前为 2 GiB 的 LV 时，`-L 512M` 并不是“增加 512 MiB”，而是试图把目标总量设置为 512 MiB。`lvextend` 不会执行缩小，但错误语义会导致失败或与题意不符。

### ④ <span class="point-label">[知识点]</span> 百分比表达必须说明参照对象

创建新 LV 时：

```bash
lvcreate -l 100%FREE -n datalv datavg
```

表示使用 VG 当前全部空闲 extent。扩展已有 LV 时常见：

```bash
lvextend -l +100%FREE datavg/datalv
```

加号表示把当前全部空闲 extent 追加到现有 LV。不要因为命令方便就默认吃满 VG；生产环境通常需要为快照、其他 LV 或未来增长保留余量。

### ⑤ <span class="point-label">[知识点]</span> 人类可读容量会舍入，extent 题要看 extent 字段

`lvs` 与 `df -hT` 可能显示略有差异：前者读取 LV 块设备标称容量，后者读取文件系统可见容量，文件系统还需要元数据空间。精确判断 PE 大小和空闲 extent 时，使用：

```bash
vgs projectvg \
  -o vg_name,vg_extent_size,vg_extent_count,vg_free_count

lvs --segments projectvg/projectlv \
  -o lv_name,seg_start_pe,seg_size_pe,segtype
```

普通单段线性 LV 的 `seg_size_pe` 可直接观察该段的 extent 数量；复杂多段 LV 需要综合所有段，不能只读一行后武断下结论。

**[Cheatsheet]** PE 大小在 VG 层；`-L` 按容量，`-l` 按 extent；无加号是新总量，有加号是增加量；`100%FREE` 会消耗全部 VG 余量，只有题目明确要求时才使用。

</section>

<section class="topic operation" id="RHCSA-25-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 用定制报告建立现状图，而不是执行一串无目的命令

LVM 命令的默认输出适合快速查看，但考试和排错更需要“只显示影响下一步判断的字段”。调查顺序通常从业务路径和设备树进入，再分别读取 PV、VG、LV。每条命令都应回答一个明确问题。

### ① <span class="point-label">[操作]</span> 用 `lsblk` 和 `findmnt` 锁定设备与挂载关系

**作用对象：** 当前内核识别的块设备树和挂载表。
**基本语义：** `lsblk` 观察父子设备、类型、文件系统与挂载点；`findmnt` 从目录或源设备查找当前挂载关系。

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt /srv/project
findmnt --source /dev/mapper/projectvg-projectlv
```

**验证边界：** `lsblk` 能提示文件系统和挂载关系，但不能完整证明某设备是否已被 LVM 当作 PV 使用；还要查 `pvs`。

### ② <span class="point-label">[操作]</span> 用 `pvs` 确认 PV 归属和未分配空间

```bash
pvs -o pv_name,vg_name,pv_size,pv_free,pv_attr
```

关键字段：

| 字段 | 回答的问题 |
|---|---|
| `pv_name` | 哪个设备是 PV |
| `vg_name` | 它属于哪个 VG；空白通常表示未加入 VG |
| `pv_size` | PV 可管理的总容量 |
| `pv_free` | 该 PV 中尚未分配给 LV 的容量 |
| `pv_attr` | PV 属性摘要 |

`pv_free` 是 PV 层视角，扩展某个 LV 时仍应查看其所属 VG 的整体空闲量。

### ③ <span class="point-label">[操作]</span> 用 `vgs` 读取容量池和 extent

```bash
vgs projectvg \
  -o vg_name,pv_count,lv_count,vg_size,vg_free,vg_extent_size,vg_extent_count,vg_free_count
```

最关键的两个扩容字段是 `vg_free` 和 `vg_free_count`。前者适合容量单位任务，后者适合按 extent 数量的任务。若题目要求新增 20 个 extent，而 `vg_free_count` 小于 20，就必须先解决 VG 的容量来源。

### ④ <span class="point-label">[操作]</span> 用 `lvs` 读取 LV 身份、路径、大小和映射

```bash
lvs -o lv_name,vg_name,lv_size,lv_path,lv_attr,segtype,devices
```

`lv_path` 比凭记忆拼接 `/dev/<VG>/<LV>` 更可靠；`devices` 能提示 LV 的数据分布在哪些 PV 上，但不应把它误解为文件系统当前挂载位置。

需要看 extent 段时：

```bash
lvs --segments projectvg/projectlv \
  -o lv_name,seg_start_pe,seg_size_pe,segtype,devices
```

### ⑤ <span class="point-label">[操作]</span> 把四层报告串成一个可执行判断

面对“扩展 `/srv/project` 20 个 extent”，推荐调查：

```bash
findmnt /srv/project
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
lvs -o lv_name,vg_name,lv_size,lv_path,segtype,devices
vgs -o vg_name,vg_free,vg_extent_size,vg_free_count
pvs -o pv_name,vg_name,pv_size,pv_free
```

调查结束时应能回答：

```text
挂载点当前由谁提供？
→ 文件系统类型是什么？
→ 对应哪个 LV 和 VG？
→ VG 是否有足够 PE？
→ 若没有，新容量能从哪个已确认空闲的设备进入？
```

**[Cheatsheet]** `lsblk` 看设备树，`findmnt` 看当前挂载；`pvs` 看 PV 归属；`vgs` 看容量池和空闲 extent；`lvs` 看 LV 路径、大小和映射。先决定要回答的问题，再选择字段。

</section>

<section class="topic operation" id="RHCSA-25-O02" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 从确认空闲的设备创建 PV、VG 和 LV

创建链不是一段可以复制到任意服务器的脚本。真正稳定的路径是先建立安全门，再逐层创建并验证。经典任务使用 `/dev/vdb1`、`projectvg`、`projectlv` 只是为了让对象关系具体化。

### ① <span class="point-label">[操作]</span> 写操作前建立设备安全门

**作用对象：** 题目指定的候选设备。
**目标：** 证明设备身份正确，且没有需要保留的数据或冲突用途。

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt --source /dev/vdb1
pvs -o pv_name,vg_name,pv_size,pv_free
blkid /dev/vdb1
```

`blkid` 无输出不等于绝对安全；它只是未发现可识别签名。还要结合题目、设备树、挂载关系和 PV 状态。发现已有文件系统、swap、PV 归属或不明数据时应停止，而不是立即使用 `--force`。

### ② <span class="point-label">[操作]</span> `pvcreate`：让设备进入 LVM 管理

**基本形式：**

```bash
pvcreate /dev/vdb1
```

**操作后验证：**

```bash
pvs /dev/vdb1 -o pv_name,vg_name,pv_size,pv_free,pv_attr
```

此时设备成为 PV，但尚未自动获得 VG、LV、文件系统或挂载点。若题目提供的是整个磁盘而不是分区，命令对象可能是 `/dev/vdb`；设备选择由题目和第 22 章的布局证据决定。

### ③ <span class="point-label">[操作]</span> `vgcreate`：建立 VG 并确定 PE 大小

```bash
vgcreate -s 16M projectvg /dev/vdb1
```

`-s 16M` 设置 PE 大小，属于 VG 属性。操作后验证：

```bash
pvs /dev/vdb1 -o pv_name,vg_name,pv_size,pv_free
vgs projectvg \
  -o vg_name,pv_count,vg_size,vg_free,vg_extent_size,vg_extent_count,vg_free_count
```

看到 `projectvg` 名称并不足够；题目指定 16 MiB PE 时必须检查 `vg_extent_size`。

### ④ <span class="point-label">[操作]</span> `lvcreate`：从 VG 分配容量

按 50 个 extent 创建：

```bash
lvcreate -l 50 -n projectlv projectvg
```

按 800 MiB 创建：

```bash
lvcreate -L 800M -n projectlv projectvg
```

本任务明确要求 extent，因此选择第一条。操作后验证：

```bash
lvs projectvg/projectlv \
  -o lv_name,vg_name,lv_size,lv_path,lv_attr,segtype,devices
lvs --segments projectvg/projectlv \
  -o lv_name,seg_start_pe,seg_size_pe,segtype
```

### ⑤ <span class="point-label">[操作]</span> 向文件系统与挂载章节交接，而不复制相邻知识

LV 创建后仍是块设备。若题目要求 XFS 和持久挂载，需要调用第 23、24 章能力：

```bash
mkfs.xfs /dev/projectvg/projectlv
mkdir -p /srv/project
blkid /dev/projectvg/projectlv
# 使用真实 UUID 建立 /etc/fstab 记录
findmnt --verify
mount -a
findmnt /srv/project
```

本章只保留这个接口骨架和验收证据，不展开 `mkfs.xfs` 参数、UUID 机制或 fstab 六字段。

**[Cheatsheet]** 调查设备 → `pvcreate` → 验证 PV → `vgcreate -s` → 验证 PE 和容量 → `lvcreate -L/-l` → 验证 LV。文件系统和持久挂载属于上层，不因 LV 创建成功而自动成立。

</section>

<section class="topic operation" id="RHCSA-25-O03" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> VG 空间不足：先扩展容量池，再扩展 LV

`lvextend` 只能从目标 VG 的空闲 PE 中分配空间。它不会自动搜索新磁盘，也不会借用其他 VG 的余量。VG 空间不足时，正确分支是让新容量经过 PV 和 `vgextend` 进入目标容量池。

### ① <span class="point-label">[操作]</span> 先证明 VG 的确不足

```bash
vgs projectvg \
  -o vg_name,vg_size,vg_free,vg_extent_size,vg_free_count
```

若需要增加 20 个 extent，则 `vg_free_count >= 20` 才能直接扩展。不要仅看 `lsblk` 中某块磁盘有空间就认为条件满足。

### ② <span class="point-label">[操作]</span> 对新设备重新执行安全调查

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt --source /dev/vdc1
pvs -o pv_name,vg_name,pv_size,pv_free
blkid /dev/vdc1
```

新设备若已属于其他 VG，应先调查其业务归属；不能用强制参数把它抢入 `projectvg`。若设备有需要保留的文件系统，本章扩容路径立即停止。

### ③ <span class="point-label">[操作]</span> 初始化 PV 并加入已有 VG

```bash
pvcreate /dev/vdc1
vgextend projectvg /dev/vdc1
```

推荐显式分成两步，这样每一步都有可验证状态。虽然某些 LVM 命令可以联动初始化设备，考试与工作中把对象变化拆开更容易控制风险。

### ④ <span class="point-label">[操作]</span> 重新验证成员关系和空闲 extent

```bash
pvs -o pv_name,vg_name,pv_size,pv_free
vgs projectvg \
  -o vg_name,pv_count,vg_size,vg_free,vg_extent_size,vg_free_count
```

只有确认 `/dev/vdc1` 已属于 `projectvg`，且 `vg_free_count` 满足目标后，才继续执行 `lvextend`。

**[Cheatsheet]** VG 不足不是 LV 参数问题。新容量必须经过“确认设备 → PV → `vgextend` → 验证 VG 余量”，之后才能被 LV 使用。

</section>

<section class="topic operation" id="RHCSA-25-O04" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 保留数据扩展 LV 与文件系统

扩容的安全目标不是“最终容量数字变大”，而是原文件系统继续存在、原数据保持可读、挂载关系不变，并且新增块空间已经被文件系统使用。操作前基线和操作后分层验收同样重要。

### ① <span class="point-label">[操作]</span> 建立扩容前基线

以 `/srv/project` 为例：

```bash
findmnt /srv/project
df -hT /srv/project
lvs projectvg/projectlv \
  -o lv_name,vg_name,lv_size,lv_path,segtype,devices
vgs projectvg \
  -o vg_name,vg_free,vg_extent_size,vg_free_count
sha256sum /srv/project/marker.txt
```

基线至少证明：目标挂载点、文件系统类型、对应 LV、VG 余量和一份需要保留的数据。校验和只证明指定文件保持一致，不等于完整备份。

### ② <span class="point-label">[操作]</span> 用正确的总量或增量表达扩展 LV

增加 20 个 extent：

```bash
lvextend -l +20 projectvg/projectlv
```

增加 512 MiB：

```bash
lvextend -L +512M projectvg/projectlv
```

扩到总大小 2 GiB：

```bash
lvextend -L 2G projectvg/projectlv
```

命令成功后立即查看 `lvs`。此时若未使用 `-r`，文件系统通常仍保持原容量，这是预期的中间状态，而不是继续重复 `lvextend` 的理由。

### ③ <span class="point-label">[操作]</span> `-r` 联动 LV 与文件系统，但仍要分层验证

```bash
lvextend -l +20 -r projectvg/projectlv
```

长选项形式：

```bash
lvextend --extents +20 --resizefs projectvg/projectlv
```

`-r` 会在 LV 扩展后调用文件系统调整路径。需要注意：

- VG 空间不足时，LV 扩展无法完成；
- 文件系统类型不受支持或调整失败时，可能出现 LV 已变大但文件系统未变大的部分终态；
- 命令没有报错仍不替代 `lvs`、`df`、`findmnt` 和数据验证。

### ④ <span class="point-label">[操作]</span> 手工扩展已挂载的 XFS

先扩展 LV：

```bash
lvextend -l +20 projectvg/projectlv
```

再对已挂载 XFS 的挂载点执行：

```bash
xfs_growfs /srv/project
```

`xfs_growfs` 的核心对象是已挂载的 XFS 文件系统，常用参数是挂载点。不要把 `/dev/projectvg/projectlv` 机械地当成该命令的普通参数。XFS 可以增长，但不能原地缩小。

### ⑤ <span class="point-label">[操作]</span> 手工扩展 ext4

先扩展 LV，再执行：

```bash
resize2fs /dev/datavg/reportslv
```

`resize2fs` 作用于文件系统所在的块设备。扩容前仍要先从 `findmnt -no FSTYPE` 或 `lsblk -f` 确认它确实是 ext4，不能把 XFS 与 ext4 工具混用。

### ⑥ <span class="point-label">[操作]</span> 扩容后的六层验收

```bash
pvs -o pv_name,vg_name,pv_size,pv_free
vgs projectvg \
  -o vg_name,vg_size,vg_free,vg_extent_size,vg_free_count
lvs projectvg/projectlv \
  -o lv_name,vg_name,lv_size,lv_path,segtype,devices
findmnt /srv/project
df -hT /srv/project
sha256sum /srv/project/marker.txt
```

需要同时成立：

```text
PV/VG 关系符合预期
→ VG 空闲量按扩展消耗
→ LV 容量增加
→ 文件系统容量增加
→ 挂载源仍是目标 LV
→ 原文件内容或校验值保持一致
```

**[Cheatsheet]** 扩容前记录对象与数据基线；`+` 表示增加量；`-r` 跨两层但不免除验证；XFS 用挂载点执行 `xfs_growfs`，ext4 对设备执行 `resize2fs`；最后同时查 LVM、文件系统、挂载和数据。

</section>

<section class="topic diagnosis" id="RHCSA-25-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 容量没有按预期出现：从症状找到断裂层

LVM 故障不应从“再试一次命令”开始。先判断症状位于设备、PV、VG、LV、文件系统还是挂载层，再选择最有区分度的证据。修复只改变断裂层，避免通过删除或重新格式化重建整个对象链。

### ① <span class="point-label">[诊断]</span> `lvs` 已增大，`df` 没变化

**症状：** LV 容量增加，但挂载点文件系统容量保持原值。
**当前证据：**

```bash
lvs <VG>/<LV> -o lv_name,lv_size,lv_path
findmnt <MOUNT_POINT>
df -hT <MOUNT_POINT>
```

**假设：** 文件系统尚未扩展，或 `-r` 的文件系统阶段失败。
**下一条证据：** 确认文件系统类型。
**最小修复：** XFS 执行 `xfs_growfs <MOUNT_POINT>`；ext4 执行 `resize2fs <LV_PATH>`。
**再验证：** 同时比较 `lvs` 与 `df -hT`。

### ② <span class="point-label">[诊断]</span> `lvextend` 报 VG 空间不足

**症状：** 扩展无法分配新 extent。
**下一条证据：**

```bash
vgs <VG> -o vg_name,vg_free,vg_extent_size,vg_free_count
```

若确实不足，调查候选新设备，执行 `pvcreate` 和 `vgextend`。不要通过缩小或删除其他 LV 作为默认答案，也不要认为系统中其他磁盘的空闲空间已经自动属于该 VG。

### ③ <span class="point-label">[诊断]</span> 目录存在，但 `findmnt` 没有目标记录

**症状：** `/srv/project` 可访问甚至可写，但没有目标挂载。
**风险：** 数据可能写入根文件系统中的空目录。
**下一条证据：**

```bash
findmnt /srv/project
df -hT /srv/project
```

若本章任务调用持久挂载，应回到第 24 章检查真实 UUID、文件系统类型、挂载点和 fstab 语法，不应删除 LV 重来。

### ④ <span class="point-label">[诊断]</span> `pvcreate` 发现已有签名或 PV 归属

**症状：** 目标设备并非已证明的空闲设备。
**下一步：** 停止写操作，重新执行 `lsblk`、`findmnt --source`、`blkid`、`pvs`，并确认题目是否指错设备。
**禁止捷径：** 不使用 `--force` 或清除签名来掩盖冲突。

### ⑤ <span class="point-label">[诊断]</span> `vgextend` 发现设备属于其他 VG

这不是“命令需要更强参数”，而是设备已经有管理归属。应调查原 VG、LV、挂载点和数据用途。只有明确退役并经过迁移流程后，才可能从原 VG 移除；该过程超出本章的安全扩容主线。

### ⑥ <span class="point-label">[诊断]</span> `lvs` 与 `df` 数字略有差异

文件系统需要元数据和保留空间，人类可读单位也会舍入。只要 LV 与文件系统都按预期增长，且差异合理，就不能仅凭数字不完全相等判定失败。extent 题应查看 `vg_extent_size` 和 `seg_size_pe`，文件系统验收查看 `df -hT`。

### ⑦ <span class="point-label">[诊断]</span> `-r` 执行后终态不清楚

不要假设 `-r` 的两个动作具有不可分割的原子性。重新查询：

```bash
lvs <VG>/<LV> -o lv_name,lv_size,lv_path
findmnt <MOUNT_POINT>
df -hT <MOUNT_POINT>
```

若 LV 已变大而文件系统未变大，只补做正确的文件系统增长；不要再盲目追加一次同样的 LV 增量。

**[Cheatsheet]** `lvs` 大、`df` 小：查文件系统；VG 不足：查 `vgs` 并扩容量池；目录存在无挂载：查 `findmnt`；设备有签名或归属：停止写操作；数字略有差异：区分块设备容量、文件系统容量和舍入。

</section>

<section class="topic diagnosis" id="RHCSA-25-D02" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 删除、缩容与已有数据：哪些动作不能当作“快速修复”

LVM 创建和扩展通常可以在明确容量来源后安全推进，删除和缩容则可能直接移除数据范围。尤其是文件系统与 LV 两层的大小关系一旦处理错误，文件系统可能在下一次读写时才暴露损坏。考试中没有明确要求时，不应主动做破坏性优化。

### ① <span class="point-label">[边界]</span> `lvreduce` 不是 `lvextend` 的无害反向操作

减少 LV 会从末端收回逻辑 extent。若文件系统仍认为这些块属于自己，数据和元数据会落在已经不存在的区域。即使工具提供文件系统联动选项，也必须理解文件系统是否支持缩小、是否需要离线、当前数据是否能够容纳在目标大小内。

### ② <span class="point-label">[边界]</span> XFS 只能增长，不能原地缩小

RHEL 9 的 XFS 没有缩小工具。要求把 XFS 变小的真实工作场景通常需要：

```text
建立新的较小文件系统
→ 迁移并校验数据
→ 切换挂载
→ 经过回退窗口后再退役旧对象
```

不能先执行 `lvreduce` 再期待 XFS 自动适配。

### ③ <span class="point-label">[边界]</span> ext4 支持缩小，不等于可以机械照抄命令

ext4 缩小通常是离线操作，并要求先把文件系统缩到不大于目标 LV 的大小，再缩小 LV。完整文件系统缩容归第 23 章；本章只建立顺序边界：**文件系统先满足安全目标，LV 才能缩小**。

### ④ <span class="point-label">[边界]</span> 删除命令只服务于明确退役

`lvremove`、`vgremove`、`pvremove` 不是通用排错工具。执行前至少要证明：

- 对象不再被挂载或使用；
- 没有需要保留的数据；
- 上层持久配置已经清理或有替代对象；
- 删除顺序符合依赖关系；
- 题目或变更单明确要求退役。

### ⑤ <span class="point-label">[边界]</span> 标记文件和校验和是验证证据，不是备份

经典任务用 `marker.txt` 或 `sha256sum` 证明扩容没有通过重新格式化完成。它只能覆盖被检查的文件，不能证明整个应用数据的一致性。生产变更仍应按业务要求执行备份、快照或应用级一致性控制。

**[Cheatsheet]** 扩容可沿容量链推进；缩容先受文件系统能力约束。XFS 不可缩小；ext4 缩小是高风险离线路径；删除只用于明确退役；标记文件不是备份。

</section>

<section class="topic knowledge" id="RHCSA-25-K03" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 从考试容量题迁移到生产变更

考试题通常给出干净设备和明确终态，生产系统则可能有历史配置、多个业务、容量增长趋势和变更窗口。核心命令不变，但证据密度和回退要求更高。最值得迁移的不是命令顺序，而是“对象、容量来源、数据、验证”四条控制线。

### ① <span class="point-label">[工作迁移]</span> 变更前保存可比较的基线

建议记录：

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
pvs -o pv_name,vg_name,pv_size,pv_free
vgs -o vg_name,pv_count,lv_count,vg_size,vg_free,vg_extent_size,vg_free_count
lvs -o lv_name,vg_name,lv_size,lv_path,lv_attr,segtype,devices
findmnt <MOUNT_POINT>
df -hT <MOUNT_POINT>
```

再按业务要求保存关键文件校验、应用停写状态或备份证据。没有基线，就无法判断操作改变了什么。

### ② <span class="point-label">[工作迁移]</span> 不默认使用全部 VG 空间

`+100%FREE` 很方便，但会消耗所有当前余量。应考虑其他 LV、快照、日志增长和下一次变更。任务只要求增加 20 个 extent 时，直接表达 `+20` 通常更符合最小变更原则。

### ③ <span class="point-label">[工作迁移]</span> 把局部成功写成多层验收矩阵

```text
LVM 层：PV/VG/LV 关系和容量
文件系统层：类型与可用空间
挂载层：业务路径实际来源
数据层：原数据可读且一致
持久层：重启后关系可恢复
业务层：应用能够按预期读写
```

RHCSA 本章重点覆盖前四层，并调用第 24 章完成持久层。生产变更还需要应用级验证，不能只凭 `df` 完成工单。

### ④ <span class="point-label">[工作迁移]</span> 记录不可逆边界和停止条件

停止条件包括：设备身份不明确、发现未知签名、设备属于其他 VG、备份要求未满足、文件系统类型与计划不符、VG 余量不足但没有经批准的新设备。面对这些证据，正确动作是停止和升级，而不是增加强制参数。

**[Cheatsheet]** 生产扩容要有基线、最小增量、多层验收和停止条件。`+100%FREE` 不是默认最佳实践；命令成功也不是业务终态。

</section>

<section class="classic-task task-page" id="RHCSA-LVM-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 建立并扩展一个可持久挂载的项目卷

一台 RHEL 9 服务器具有两个已经准备好的候选分区：`/dev/vdb1` 和 `/dev/vdc1`。题目说明它们用于本任务，但执行写操作前仍需确认其当前状态。完成以下目标：

1. 使用 `/dev/vdb1` 创建名为 `projectvg` 的 VG，PE 大小为 16 MiB；
2. 在 `projectvg` 中创建名为 `projectlv` 的 LV，初始大小为 50 个 extent；
3. 在该 LV 上创建 XFS，并通过真实 UUID 持久挂载到 `/srv/project`；
4. 在 `/srv/project/marker.txt` 中写入一行 `keep-this-data`，并记录校验和；
5. 将 `projectlv` 再增加 20 个 extent，同时扩大 XFS；
6. 若 `projectvg` 的空闲 extent 不足，应先使用 `/dev/vdc1` 扩大 VG；
7. 不得通过重新格式化、删除原 LV、缩小其他 LV 或强制覆盖未知签名获得结果。

**目标终态：** LV 最终对应 70 个 extent，即在 16 MiB PE 下标称容量约为 1120 MiB；XFS 使用新增空间；`/srv/project` 当前由目标 LV 提供；持久配置可解析；标记文件内容和校验值保持不变。

**验收证据：**

```text
设备与 PV 归属
VG 的 PE 大小和空闲 extent
LV 路径、容量与 extent
XFS 容量
当前挂载源
持久配置验证
原数据内容和校验和
```

<div class="self-help">
<strong>卡住时再想一想</strong>
<p><code>lvs</code> 变大能否证明 XFS 已经增长？</p>
<p><code>vg_free_count</code> 小于 20 时，新设备要经过哪两个对象层？</p>
<p>目录存在能否证明目标文件系统挂载成功？</p>
</div>

> 请先独立完成。参考解答从新页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-LVM-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 从设备调查到八层验收

先把题目拆成设备身份、PV/VG 关系、PE 大小、LV 初始容量、文件系统、持久挂载、数据保留和扩容八个状态。下面的设备名来自任务场景，真实环境必须使用实际查询结果。

### ① 建立初始证据

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt --source /dev/vdb1
findmnt --source /dev/vdc1
blkid /dev/vdb1
blkid /dev/vdc1
pvs -o pv_name,vg_name,pv_size,pv_free
vgs -o vg_name,vg_size,vg_free,vg_extent_size,vg_free_count
lvs -o lv_name,vg_name,lv_size,lv_path,devices
findmnt /srv/project
```

若发现文件系统、挂载、swap、已有 PV/VG 归属或无法解释的数据，停止写操作。题目明确且查询证据一致后再继续。

### ② 创建 PV 和指定 PE 的 VG

```bash
pvcreate /dev/vdb1
vgcreate -s 16M projectvg /dev/vdb1

pvs /dev/vdb1 -o pv_name,vg_name,pv_size,pv_free
vgs projectvg \
  -o vg_name,pv_count,vg_size,vg_free,vg_extent_size,vg_extent_count,vg_free_count
```

确认 `vg_extent_size` 为 16 MiB。

### ③ 创建 50 个 extent 的 LV

```bash
lvcreate -l 50 -n projectlv projectvg

lvs projectvg/projectlv \
  -o lv_name,vg_name,lv_size,lv_path,lv_attr,segtype,devices
lvs --segments projectvg/projectlv \
  -o lv_name,seg_start_pe,seg_size_pe,segtype
```

对于普通单段线性 LV，`seg_size_pe` 应对应 50。

### ④ 调用文件系统与持久挂载能力

```bash
mkfs.xfs /dev/projectvg/projectlv
mkdir -p /srv/project
blkid /dev/projectvg/projectlv
```

将 `blkid` 返回的真实 UUID 写入 `/etc/fstab`。示意结构如下，不能复制占位值：

```fstab
UUID=<真实 UUID> /srv/project xfs defaults 0 0
```

在重启前验证并建立当前挂载：

```bash
systemctl daemon-reload
findmnt --verify
mount -a
findmnt /srv/project
df -hT /srv/project
```

`systemctl daemon-reload`、fstab 字段和持久验证的完整原理属于第 24 章；这里作为任务接口使用。

### ⑤ 建立数据保留证据

```bash
printf '%s\n' 'keep-this-data' > /srv/project/marker.txt
sha256sum /srv/project/marker.txt | tee /root/project-marker.sha256
```

### ⑥ 判断 VG 是否有 20 个空闲 extent

```bash
vgs projectvg \
  -o vg_name,vg_free,vg_extent_size,vg_free_count
```

若 `vg_free_count` 小于 20，先调查并加入第二个 PV：

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt --source /dev/vdc1
blkid /dev/vdc1
pvs -o pv_name,vg_name,pv_size,pv_free

pvcreate /dev/vdc1
vgextend projectvg /dev/vdc1

pvs -o pv_name,vg_name,pv_size,pv_free
vgs projectvg \
  -o vg_name,pv_count,vg_size,vg_free,vg_extent_size,vg_free_count
```

### ⑦ 增加 20 个 extent 并扩大 XFS

联动路径：

```bash
lvextend -l +20 -r projectvg/projectlv
```

或者分步路径：

```bash
lvextend -l +20 projectvg/projectlv
xfs_growfs /srv/project
```

不能同时执行两套路径。分步路径更便于观察中间状态；`-r` 路径更短，但仍须查询最终两层。

### ⑧ 最终分层验证

```bash
pvs -o pv_name,vg_name,pv_size,pv_free
vgs projectvg \
  -o vg_name,pv_count,vg_size,vg_free,vg_extent_size,vg_extent_count,vg_free_count
lvs projectvg/projectlv \
  -o lv_name,vg_name,lv_size,lv_path,lv_attr,segtype,devices
lvs --segments projectvg/projectlv \
  -o lv_name,seg_start_pe,seg_size_pe,segtype

findmnt /srv/project
df -hT /srv/project
lsblk -f
blkid /dev/projectvg/projectlv
findmnt --verify

cat /srv/project/marker.txt
sha256sum -c /root/project-marker.sha256
```

预期判断：VG 的 PE 为 16 MiB；LV 最终对应 70 个 extent，标称约 1120 MiB；XFS 容量较扩展前增长；挂载源仍指向 `projectlv`；真实 UUID 与持久记录一致；标记文件校验通过。

**典型错误：**

- 忘记 `+`，把增量写成目标总量；
- 看到 `lvs` 增长后跳过文件系统；
- VG 不足时反复执行 `lvextend`，没有先扩展容量池；
- 目录存在就判断挂载成功；
- 为了继续操作对未知签名使用强制参数；
- 用重新格式化“解决”文件系统容量问题，破坏原数据。

</section>

<section class="classic-task task-page" id="RHCSA-25-C02" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 保留 ext4 数据扩展现有报告卷

系统中 `/srv/reports` 当前已挂载 ext4，挂载源为 `/dev/datavg/reportslv`，LV 标称大小为 2 GiB。目录中存在 `/srv/reports/report.db`。`datavg` 是否有足够空间未知，`/dev/vdd1` 是经变更单提供的候选扩容设备。

完成以下目标：

1. 记录当前挂载、LV、VG、文件系统容量和 `report.db` 校验和；
2. 将 `reportslv` **增加** 512 MiB，而不是设置为总大小 512 MiB；
3. 本任务不使用 `-r`，要求分别扩展 LV 和 ext4；
4. 若 VG 空间不足，确认 `/dev/vdd1` 空闲后将其加入 `datavg`；
5. 最终挂载源不变，ext4 使用新增空间，`report.db` 校验和保持一致；
6. 不得卸载后重新格式化，不得删除并重建 LV。

> 请先独立完成。参考解答从新页开始。

</section>

<section class="classic-task solution-page" id="RHCSA-25-C02-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 分开观察 LV 与 ext4 的增长

### ① 建立基线并确认对象

```bash
findmnt /srv/reports
findmnt -no SOURCE,FSTYPE,TARGET /srv/reports
df -hT /srv/reports
lvs datavg/reportslv \
  -o lv_name,vg_name,lv_size,lv_path,segtype,devices
vgs datavg \
  -o vg_name,vg_size,vg_free,vg_extent_size,vg_free_count
sha256sum /srv/reports/report.db | tee /root/report-db.sha256
```

必须确认文件系统类型确实是 ext4，且挂载源是目标 LV。

### ② 确认 VG 是否至少有 512 MiB 可分配空间

```bash
vgs datavg -o vg_name,vg_free,vg_extent_size,vg_free_count
```

空间不足时调查候选设备：

```bash
lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt --source /dev/vdd1
blkid /dev/vdd1
pvs -o pv_name,vg_name,pv_size,pv_free
```

证明确实空闲后：

```bash
pvcreate /dev/vdd1
vgextend datavg /dev/vdd1
pvs -o pv_name,vg_name,pv_size,pv_free
vgs datavg -o vg_name,pv_count,vg_size,vg_free,vg_free_count
```

### ③ 只扩展 LV，观察中间状态

```bash
lvextend -L +512M datavg/reportslv
lvs datavg/reportslv -o lv_name,vg_name,lv_size,lv_path
```

此时 `df -hT /srv/reports` 可能仍显示原文件系统大小，这正是两层状态分离的证据。

### ④ 扩展 ext4

```bash
resize2fs /dev/datavg/reportslv
```

### ⑤ 最终验证

```bash
lvs datavg/reportslv -o lv_name,vg_name,lv_size,lv_path,devices
vgs datavg -o vg_name,vg_size,vg_free,vg_free_count
findmnt /srv/reports
df -hT /srv/reports
sha256sum -c /root/report-db.sha256
```

若 `lvs` 增长而 `df` 不变，应检查 `resize2fs` 是否针对正确设备执行；不要再次增加 512 MiB。若挂载源变化或校验失败，任务不能视为完成。

</section>

<section class="topic closing" id="RHCSA-25-CLOSING" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 容量链也是证据链

LVM 的核心不是三个缩写，而是把真实设备、容量池、逻辑块设备、文件系统和业务目录分开理解。`pvcreate` 让设备获得 LVM 身份；VG 汇聚 PV 并按 PE 管理容量；LV 从 VG 获得 LE；文件系统使用 LV 提供的块空间；挂载点把文件系统接入目录树。

面对创建题，先证明设备身份，再按 PV、VG、LV 顺序建立对象；面对扩容题，从挂载点反向找到文件系统、LV 和 VG，确认容量来源后再扩展；面对故障，比较 `pvs`、`vgs`、`lvs`、`findmnt` 和 `df` 所代表的层次，不用删除、格式化或强制参数掩盖证据。

最稳定的记忆路径是：

```text
目标目录是谁提供
→ 对应哪个文件系统和 LV
→ LV 从哪个 VG 获得容量
→ VG 是否有足够空闲 PE
→ 修改后 LV 和文件系统是否都增长
→ 挂载与原数据是否仍然正确
```

> 学完本章后，你应能从已确认空闲的设备创建指定 PE 大小的 VG 和指定 extent 数量的 LV，能在 VG 余量不足时安全扩展容量池，并在保留数据的前提下完成 XFS 或 ext4 的容量增长与分层验收。

</section>
