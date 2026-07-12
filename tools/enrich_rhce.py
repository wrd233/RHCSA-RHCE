from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
extras={
"loops-conditionals-handlers": ("RHCE-CONTROL-X01", "控制结构的输出与边界检查", """### ① [参数点] loop_control 不改变业务数据
`label` 只缩短终端输出，`loop_var` 改变循环变量名，`index_var` 保存索引。调试时仍应检查原始 item 结构，不能因为 label 美观就认为数据完整。

### ② [验证点] failed_when 与 changed_when 必须可复核
条件应引用稳定的 `rc`、模块字段或明确输出，不匹配本地化人类文本。执行后用 `debug: var=result` 抽查被改写的任务结果，确保真实失败没有被标成成功。

### ③ [边界] rescue 不是事务回滚
block 中前一任务已经改变的远端状态不会自动撤销。rescue 必须显式恢复需要恢复的对象，always 只适合清理、记录和无条件收束。""", "loop_control 管输出/变量名；结果改写必须基于稳定字段；rescue 需显式恢复，不是自动回滚。"),
"files-templates-jinja": ("RHCE-TEMPLATES-X01", "模板渲染、校验与换行细节", """### ① [参数点] validate 命令使用占位符
`validate: '/usr/sbin/sshd -t -f %s'` 让模块把临时文件路径代入 `%s`。命令不经 Shell，因此管道与重定向不能直接使用；校验工具必须能读取临时路径。

### ② [知识点] Jinja 空白会改变真实配置
`trim_blocks`、`lstrip_blocks` 和 `-{%` 等控制空白。多一空行通常无害，但 YAML、sudoers、hosts 或严格配置中的缩进与末尾换行可能改变语义，必须查看 `--diff` 和远端文件。

### ③ [验证点] 模板依赖清单
模板引用的每个变量都应能从 defaults、group_vars、host_vars 或 Facts 追溯；修改模板后回归所有消费主机组，而不只测试当前 limit 主机。""", "validate 用 `%s` 临时路径；空白控制可能改语义；diff 后回归所有模板消费者。"),
"external-data-vault": ("RHCE-VAULT-X01", "Vault ID、文件权限与日志泄露面", """### ① [参数点] 多 Vault 使用 label
`--vault-id dev@prompt --vault-id prod@/path/key` 将密文 label 与密码来源绑定。运行错误时先确认密文头中的 vault ID 和命令提供的 label，不按文件名猜密码。

### ② [边界] 密码文件不是 Vault
密码文件通常是解密钥匙本身，必须 `0600`、排除版本控制并按题目路径管理；把它再放进同一 Vault 会形成无法启动的循环依赖。

### ③ [验证点] 失败输出也可能泄密
模块失败的 invocation、register、debug 和 callback 均可能包含参数。对传递秘密的最小 task 使用 `no_log`，同时避免随后 debug 整个注册对象。""", "多 Vault 核对 label；密码文件 0600 且不入库；敏感 task 与后续 register 输出一起审计。"),
"roles-collections": ("RHCE-ROLES-X01", "Role 接口、依赖与标签传播", """### ① [知识点] defaults 是公开接口，不是所有变量仓库
调用者需要覆盖的值进入 defaults；Role 内部常量可放 vars，但过强优先级会阻止环境差异。变量名加 Role 前缀可减少多 Role 冲突。

### ② [参数点] requirements 可同时描述 Role 与 Collection
实际项目可分 `roles/requirements.yml` 与 `collections/requirements.yml`，也可按工具支持格式组织。离线 tarball 的 source 与版本要保持题目给定 lineage，不擅自换最新版。

### ③ [验证点] 重构前后比较任务与 Handler
`--list-tasks`、tags、远端 diff 和第二次执行共同证明移动内容没有丢失 Handler、模板路径或变量覆盖。""", "defaults 暴露接口；requirements 固定真实依赖；重构用任务图、远端 diff 与幂等证明等价。"),
"automate-system-services": ("RHCE-SYSTEM-X01", "模块参数的替换、追加与删除语义", """### ① [参数点] user 模块表达最终账号而非 useradd 命令
`state`、`uid`、`group`、`groups`、`append`、`shell`、`password_expire_max` 等共同描述目标。删除账号时 `remove: true` 会删除家目录，必须由题意明确。

### ② [参数点] dnf state 的范围
`present` 保证安装，`latest` 会随仓库元数据升级并可能持续改变发布结果，`absent` 删除。只有题目要求最新时使用 latest，并阅读依赖事务。

### ③ [验证点] authorized_key 与 sudoers 仍需功能测试
公钥文件存在后从控制节点实际 SSH；sudoers 由 template/copy 部署时用 `visudo -cf %s` validate，再以目标用户执行允许与拒绝命令。""", "user 删除/组语义要显式；dnf latest 只按题意；公钥与 sudoers 最终做真实认证/授权测试。"),
"automate-network-selinux": ("RHCE-NETWORK-X01", "网络批量变更的串行与恢复策略", """### ① [边界] serial 降低影响但不修复错误
play 设置 `serial: 1` 可逐台应用网络，配合 `max_fail_percentage` 控制停止条件。第一台失败时立即停止并调查，不能依赖 serial 自动回滚连接。

### ② [验证点] 等待重连要验证新地址
网络 Role 完成后可用 `wait_for_connection`，但成功只证明 Ansible 重新连接；继续运行 `ip route get`、`getent` 和目标协议测试，确认连接不是经错误备用路径恢复。

### ③ [边界] SELinux module 与 restorecon 分工
规则模块只保证 policy mapping，当前对象仍需恢复标签。restorecon command 可先用 `-n` 预览差异，再在规则确定后应用并用 `matchpathcon`/`ls -Z` 对比。""", "网络用 serial/停止条件降低批量风险；重连后验地址/路由；fcontext 规则与 restorecon 当前标签分开。"),
"automate-storage": ("RHCE-STORAGE-X01", "设备事实、容量单位与失败保护", """### ① [知识点] ansible_devices 不是安全空闲证明
Facts 可给设备大小、分区和型号，但未必包含所有签名/LVM/挂载关系。真正初始化前仍需受控 `lsblk/blkid/pvs` 证据或题目明确保证。

### ② [参数点] 容量字符串保持题意单位
`size: 2g`、百分比和 resizefs 行为由当前 collection 模块定义。extent 题若模块不能精确表达，应计算并 assert 结果，不用近似容量悄悄改变目标。

### ③ [失败边界] 先 fail 再做破坏性任务
用 assert 检查设备变量存在、VG 条件和目标大小；block/rescue 可输出明确错误，但不能在 rescue 中格式化另一块猜测设备。""", "Facts 只做初筛；容量保持题意单位并 assert；破坏性 task 前显式 fail，rescue 不猜替代设备。"),
"troubleshooting-idempotency": ("RHCE-TROUBLESHOOTING-X01", "check mode、diff 与可观测性边界", """### ① [知识点] check mode 支持度取决于模块
支持 check_mode 的模块预测 changed，不支持的任务可能跳过或仍需特殊处理。不能把一次 `--check` 全绿当作真实执行成功。

### ② [验证点] diff 只显示可公开差异
`--diff` 有助于模板/文件审查，但可能暴露敏感内容；秘密任务应 no_log，并用非敏感结构证据验收。二进制或某些模块没有可读 diff。

### ③ [诊断点] start-at-task 会跳过前置状态
从中间开始可能缺少 Facts、变量设置、文件下载或 Handler 通知，只适合前置状态已明确成立的复现。最终仍从完整 Playbook 回归。""", "check 支持度要核对；diff 注意秘密；start-at-task 不替代完整回归。"),
"comprehensive": ("RHCE-COMPREHENSIVE-X01", "交付目录、命名与可重复执行入口", """### ① [验证点] 题目要求的路径本身可能评分
Inventory、ansible.cfg、playbook、Vault、templates 和 roles 必须位于指定绝对路径并具备正确权限。内容等价但文件名或入口错误仍可能无法被评分命令发现。

### ② [知识点] 控制节点产物与受管节点产物分开
template 源、requirements 和 Vault 留在控制端；目标配置、用户和挂载在远端。验证脚本要明确在哪一端执行，不能看到控制端文件就判定远端完成。

### ③ [验证点] 最终执行记录可重现
从项目目录运行固定命令，记录 inventory graph、syntax、首次/第二次 recap 和远端矩阵。清理临时明文与 debug 任务，但不删除题目要求的内容源。""", "路径/命名是接口；控制端与远端对象分开；固定入口重现首次、二次与远端矩阵。"),
}

cloze={
"architecture-inventory":[("配置来源先看 `ansible --version` 的 {{c1::config file}}；主机范围先看 `{{c2::--list-hosts}}`。","执行边界。"),("Inventory 的逻辑名是 {{c1::inventory_hostname}}，连接地址可由 {{c2::ansible_host}} 指定。","名称与地址分开。")],
"yaml-playbook-modules":[("Playbook 静态门：`{{c1::--syntax-check}}`、`{{c2::--list-hosts}}`、`--list-tasks`。","再 limit 执行。"),("服务当前状态用 `state: {{c1::started}}`，启动持久状态用 `enabled: {{c2::true}}`。","两维度。")],
"variables-facts":[("循环 register 的逐项结果通常位于 `{{c1::results}}`；命令返回码通常位于 `{{c2::rc}}`。","先 debug 结构。"),("逻辑主机名是 `{{c1::inventory_hostname}}`；连接地址常是 `{{c2::ansible_host}}`。","不要混用。")],
"loops-conditionals-handlers":[("Handler 只有在通知 task 返回 {{c1::changed}} 时被 `{{c2::notify}}` 排队。","默认 play 后部执行。"),("提前运行已通知 Handler：`ansible.builtin.meta: {{c1::flush_handlers}}`。","之后再验证依赖功能。")],
"files-templates-jinja":[("Jinja 输出表达式使用{{c1::双花括号定界符}}；控制结构使用{{c2::花括号加百分号定界符}}。","保持目标缩进。"),("模板替换前校验使用 `validate`，临时文件占位符是 `{{c1::%s}}`。","命令不经 Shell。")],
"external-data-vault":[("轮换 Vault 密码并保持密文使用 `ansible-vault {{c1::rekey}}`。","不要 decrypt 编辑。"),("Vault 保护{{c1::静态文件}}，敏感 task 输出用 `{{c2::no_log: true}}`。","两层不同。")],
"roles-collections":[("Role 可覆盖默认值位于 `{{c1::defaults/main.yml}}`；任务入口是 `{{c2::tasks/main.yml}}`。","接口与实现。"),("动态包含用 `{{c1::include_tasks}}`；静态导入用 `{{c2::import_tasks}}`。","时点语义。")],
"automate-system-services":[("user 附加组追加需要 `append: {{c1::true}}`；否则 groups 常表达{{c2::完整目标列表}}。","避免丢组。"),("服务当前启动 `state: {{c1::started}}`；开机启动 `enabled: {{c2::true}}`。","双态。")],
"automate-network-selinux":[("firewalld 持久配置 `permanent: {{c1::true}}`；立即应用 runtime `immediate: {{c2::true}}`。","分别验收。"),("fcontext 建立{{c1::持久规则}}，`restorecon` 应用{{c2::当前标签}}。","不能互替。")],
"automate-storage":[("存储依赖顺序：`{{c1::lvg → lvol → filesystem}}` → mountpoint → `{{c2::mount}}`。","先设备证据。"),("`lvs` 增长而 `df` 不变，缺少{{c1::文件系统扩展}}。","不要继续增加 LV。")],
"troubleshooting-idempotency":[("{{c1::UNREACHABLE}} 表示连接层未建立；{{c2::FAILED}} 表示可达主机上的任务失败。","先分层。"),("第二次无 changed 证明{{c1::幂等稳定}}，不能单独证明{{c2::目标正确}}。","还要远端验收。")],
"comprehensive":[("RHCE 主线：静态边界 → {{c1::limit 代表主机}} → 远端终态 → 全量 → {{c2::第二次执行}}。","每阶段取证。"),("最终判据包含主机覆盖、远端正确、秘密安全、依赖可复现与{{c1::幂等稳定}}。","不是 recap 单项。")],
}

for slug,(sid,title,body,cheat) in extras.items():
 p=ROOT/"content/rhce/chapters"/slug/"lecture.md"
 text=p.read_text(encoding="utf-8")
 marker=f'id="{sid}"'
 if marker not in text:
  section=f'''<section class="topic knowledge" id="{sid}" data-kind="knowledge-topic">\n\n## <span class="topic-label">[知识专题]</span> {title}\n\n{body}\n\n**[Cheatsheet]** {cheat}\n\n</section>\n\n'''
  text=text.replace('<section class="classic-task task-page"',section+'<section class="classic-task task-page"',1)
  p.write_text(text,encoding="utf-8")

for slug,items in cloze.items():
 p=ROOT/"content/rhce/chapters"/slug/"anki.yml"; data=yaml.safe_load(p.read_text(encoding="utf-8"))
 existing={n["id"] for n in data["notes"]}; cid=data["chapter_id"]
 for i,(text,extra) in enumerate(items,1):
  nid=f"{cid}-CLOZE-X{i:02d}"
  if nid not in existing:
   data["notes"].append({"id":nid,"type":"cloze","text":text,"extra":extra,"source":["RH294-RHEL9","Ansible-Documentation"],"tags":["exam::rhce",f"chapter::{slug}","card::cloze","coverage::extra"]})
 p.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False,width=1000),encoding="utf-8")
