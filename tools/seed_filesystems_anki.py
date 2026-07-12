from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[1]
def c(q,a,e,t="command",p="P0"): return (q,a,e,t,p)
cards=[
c("写操作前查看块设备拓扑、类型、UUID 与挂载点的命令是什么？","`lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,UUID,MOUNTPOINTS`","设备名相似时必须重查。"),
c("`wipefs /dev/vdb` 与 `wipefs -a /dev/vdb` 的区别是什么？","前者列签名；后者擦除签名。","调查时不得加 -a。","comparison"),
c("为什么 FSTYPE 为空不能充分证明设备安全空闲？","设备仍可能有未识别数据、分区表或上层归属。","继续查挂载、LVM/RAID 和题意。","diagnosis"),
c("在新磁盘建立 GPT 的 parted 命令骨架是什么？","`parted -s <DISK> mklabel gpt`","会重写分区布局。"),
c("创建约 2 GiB 分区并预留对齐空间的骨架是什么？","`parted -s <DISK> mkpart data xfs 1MiB 2049MiB`","mkpart 不创建 XFS。"),
c("请求内核重读分区表并等待设备事件，使用什么？","`partprobe <DISK>`；`udevadm settle`。","再用 lsblk 验证。"),
c("`mkfs.xfs` 的作用与风险是什么？","在块设备上新建 XFS，会覆盖原文件系统结构。","只对确认无需保留数据的新对象使用。","diagnosis"),
c("XFS 与 ext4 的缩小边界是什么？","XFS 不支持原地缩小；ext4 可在满足条件时缩小。","创建题按指定类型。","comparison"),
c("读取文件系统或 Swap UUID 的命令是什么？","`blkid <DEVICE>`","UUID 必须来自当前签名。"),
c("fstab 六字段顺序是什么？","设备、挂载点、类型、选项、dump、fsck pass。","各字段共同描述持久策略。","syntax"),
c("为什么不应默认给 fstab 添加 `nofail`？","它改变启动失败处理，可能掩盖本应修复的错误。","仅按题意使用。","diagnosis"),
c("修改 fstab 后的重启前验证链是什么？","`daemon-reload` → `findmnt --verify` → `mount -a` → `findmnt`。","静态检查不替代实际挂载。","process"),
c("`findmnt /srv/data` 与 `df -hT /srv/data` 分别证明什么？","挂载源/类型/选项；文件系统容量与使用率。","两个层次。","verification"),
c("Swap 的三层状态是什么？","mkswap 签名、swapon 当前启用、fstab 持久条目。","任一层不能替代其余。","process"),
c("创建 Swap 签名并当前启用的命令是什么？","`mkswap <DEV>`；`swapon <DEV>`。","先确认设备空闲。"),
c("Swap fstab 条目骨架是什么？","`UUID=<UUID> none swap defaults 0 0`","使用真实 UUID。","syntax"),
c("查看具体 Swap 设备、大小和优先级，使用什么？","`swapon --show`","free -h 不直接列设备。","verification"),
c("Swap USED=0 是否表示没有启用？","不是；可能已启用但当前无需换出页面。","看 swapon --show。","output"),
c("umount 报 target is busy 的下一步是什么？","查嵌套挂载和 `fuser -vm <MOUNT>`/lsof。","不先 force/lazy。","diagnosis"),
c("挂载到非空目录后原内容怎样？","被新挂载暂时遮蔽，卸载后重新出现。","不是自动删除。","concept"),
c("fstab 报 UUID 不存在时怎样处理？","用 blkid/lsblk -f 核对当前 UUID，修正条目后重新 verify/mount。","不要重新格式化。","diagnosis"),
c("目录存在但 findmnt 无结果，数据可能写到哪里？","根文件系统中的普通目录。","停止写入并恢复挂载。","diagnosis"),
c("分区、文件系统与 Swap 综合任务的验收骨架是什么？","布局 → 签名/UUID → 当前 mount/swapon → fstab → 容量/写入。","逐层验证。","process"),
]
notes=[]
for i,(q,a,e,t,p) in enumerate(cards,1):
 notes.append({"id":f"RHCSA-FILESYSTEMS-QA-{i:03d}","type":"qa","question":q,"answer":a,"extra":e,"source":["RH134-RHEL9","RHCSA-Course-21","RHCSA9-Mock"],"tags":["exam::rhcsa","chapter::partitions-filesystems",f"card::{t}",f"priority::{p}"]})
payload={"chapter_id":"RHCSA-FILESYSTEMS","deck":"RedHat::RHCSA-RHEL9","note_types":["RedHat-QA","RedHat-Cloze"],"notes":notes}
path=root/"content/rhcsa/chapters/partitions-filesystems/anki.yml"
path.write_text(yaml.safe_dump(payload,allow_unicode=True,sort_keys=False,width=1000),encoding="utf-8")
