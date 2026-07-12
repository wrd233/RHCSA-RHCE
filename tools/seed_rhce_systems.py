from content_factory import write_chapter
def c(q,a,e="",t="ansible",p="P0"): return(q,a,e,t,p)
def b(items): return "\n\n".join(f"### {n} [{k}] {t}\n{x}" for n,k,t,x in items)
def make(slug,num,title,cid,intro,concepts,semantics,k,o,d,task,sol,close,cards):
 src=["RH294-RHEL9","RHCE9-Mock","Ansible-Documentation"]
 write_chapter(track="rhce",slug=slug,number=num,title=title,chapter_id=cid,sources=src,intro=intro,concepts=concepts,semantics=semantics,
 topics=[(cid+"-K01","知识专题",k[0][2],b(k),"；".join(x[2] for x in k)),(cid+"-O01","操作专题",o[0][2],b(o),"；".join(x[2] for x in o)),(cid+"-D01","诊断专题",d[0][2],b(d),"；".join(x[2] for x in d))],task=task,solution=sol,closing=close,cards=cards)

make("roles-collections","第七章","Include、Import、Role 与 Collection","RHCE-ROLES",
 "内容拆分必须保留执行边界。import 在解析期静态展开，include 在运行期动态选择；Role 用固定目录把 tasks、handlers、templates、files 和变量组织为可复用接口；Collection 提供 FQCN、Role 和插件版本。",
 ["include_tasks 动态执行并可按 loop/when 选择；import_tasks 静态展开，适合固定结构和 list-tasks。import_playbook 只能在 playbook 顶层。", "Role defaults 是低优先级可覆盖接口，vars 更强不适合作为用户配置入口。Collection requirements 锁定依赖来源/版本，FQCN 避免模块名冲突。"],
 ["`ansible-galaxy role init` 创建 Role 骨架，`ansible-galaxy collection install -r requirements.yml` 安装依赖；`ansible-doc -t role`/模块文档查接口。"],
 [("①","知识点","动态与静态复用","import 在解析时展开，标签/list-tasks 可见；include 在运行时根据变量与循环决定。不要只背先后，按是否需要运行时选择。"),("②","知识点","Role 目录和变量接口","tasks/main.yml 是入口，handlers/templates/files 自动按 Role 路径解析；defaults 提供可覆盖默认值，meta 声明依赖。"),("③","验证点","依赖与路径可复现","requirements 文件进入项目；离线/考试材料按给定 tar/路径安装，`ansible-galaxy collection list` 核对实际版本。")],
 [("①","操作点","把单文件重构为 Role","移动任务、Handler、模板和文件，不改变 notify 名称与变量语义；把环境差异转为 defaults 或调用时 vars。"),("②","操作点","安装并使用 Collection/System Role","requirements 指定 name/source/version；Playbook 用 FQCN 和 `roles:` 调用，阅读 Role README/defaults 获取变量 schema。"),("③","验证点","语法、任务图与远端终态","syntax-check、list-tasks/tags、limit 执行；Role 重构前后远端终态与第二次执行一致。")],
 [("①","诊断点","找不到 Role/Collection","检查 roles_path/collections_paths、项目目录、requirements 安装位置和名称空间，不复制内容到随机路径。"),("②","诊断点","变量无法覆盖","检查是否错误放在 role vars 而非 defaults，以及调用层变量名/schema。"),("③","诊断点","include 标签行为意外","动态 include 的标签不会自动以相同方式传播到内部 task；按文档使用 apply 或给内部任务标签。")],
 ("把 Web Playbook 重构为可复用 Role","创建 web_role，包含包、模板、Handler 和服务；默认端口可由组变量覆盖。通过 requirements 安装题目 Collection，并用新 Playbook 调用。验收依赖、任务图、两组差异、Handler 和幂等性。"),
 ("保留行为地移动内容","### ① [操作点] role init，移动 tasks/handlers/templates/files，接口值放 defaults。\n### ② [操作点] requirements 安装 Collection，以 FQCN 调用。\n### ③ [验证点] syntax/list-tasks、limit、全量、远端终态、第二次执行。","依赖安装 → Role 接口 → 静态边界 → 远端等价 → 幂等。"),
 ("复用的价值是稳定接口而非更多目录","选择 include/import 的时点语义，Role 用 defaults 暴露最小接口，Collection 用 requirements 固定依赖。重构完成必须证明远端行为未改变。"),
 [c("include_tasks 与 import_tasks 核心区别？","运行时动态包含；解析期静态导入。","","comparison"),c("import_playbook 可放在 tasks 内吗？","不能，位于 playbook 顶层。","","diagnosis"),c("Role tasks 默认入口？","`roles/<role>/tasks/main.yml`"),c("Role 可覆盖默认变量放哪里？","`defaults/main.yml`"),c("为什么不把接口变量放 vars/main.yml？","优先级较高，调用者难覆盖。","","diagnosis"),c("创建 Role 骨架命令？","`ansible-galaxy role init <ROLE>`"),c("按 requirements 安装 Collection？","`ansible-galaxy collection install -r requirements.yml`"),c("FQCN 的价值？","明确 collection 与模块，避免名称冲突。"),c("找不到 Role 首查什么？","roles_path、项目目录和实际安装位置。","","diagnosis"),c("Role 重构验收链？","syntax/list → limit → 远端等价 → 全量 → 第二次执行。","","process"),c("System Role 变量从哪里确认？","Role README、defaults 和官方文档。"),c("requirements 的价值？","让依赖来源和版本可复现。"
 )])

make("automate-system-services","第八章","自动化用户、软件包、仓库、服务与计划任务","RHCE-SYSTEM",
 "本章把 RHCSA 手工状态映射为专用模块参数。自动化重点是声明最终用户、仓库、包、服务和 cron，而不是远程执行对应命令；变量数据驱动多对象，Handler 只响应配置变化。",
 ["user/group/authorized_key 管身份，dnf/package/yum_repository 管软件，service/systemd_service 管当前与启动状态，cron 管周期声明。每个模块的 state 对应目标终态。", "模块幂等依赖稳定输入：随机密码盐、动态时间戳、无 regexp 的追加文本都会制造持续 changed。"],
 ["使用 FQCN；`password` 传哈希，`groups` 配合 append；`enabled` 与 `state` 分别表达启动和当前服务。"],
 [("①","知识点","身份模块参数边界","user.groups 默认可替换附加组，`append: true` 才追加；remove 要明确是否删除家目录。authorized_key 的 exclusive 对循环逐项使用可能互相删除。"),("②","知识点","仓库与包分层","yum_repository 创建 repo 配置，rpm_key 管 key，dnf 安装包。仓库文件存在后仍要 makecache/包事务证据。"),("③","验证点","服务双态与 cron 身份","service 的 started/enabled 分别验证；cron 的 user、时间字段和 job 必须与题意一致，远端检查 crontab/产物。")],
 [("①","操作点","用外部列表创建用户","loop 字典调用 group/user/authorized_key；密码哈希从 Vault，no_log 限制敏感 task。"),("②","操作点","配置仓库、包和服务","先 key/repo，再 dnf；模板 notify Handler，service 保证 started+enabled。"),("③","验证点","模块结果与远端对象","第二次执行无 changed；getent/id、dnf repolist/rpm、systemctl、crontab 和实际服务功能。")],
 [("①","诊断点","用户附加组丢失","检查 groups 是否在未 append 情况下替换全部列表；修正数据为完整目标或 append。"),("②","诊断点","服务每次重启","检查 Handler 是否被动态模板/无条件 changed task 每次通知。"),("③","诊断点","cron 存在但不执行","远端查 user、绝对路径、环境、crond 日志和产物；模块 changed=0 只证明条目稳定。")],
 ("用变量为多组主机配置基础服务","从外部用户数据创建组/用户/公钥，配置指定仓库和包，部署服务并只在配置变化时重启，创建周期任务。验收每组数据差异、秘密安全、服务双态、cron 产物和第二次执行。"),
 ("把手工命令映射为专用模块","### ① [操作点] group/user/authorized_key loop；Vault 哈希。\n### ② [操作点] rpm_key/yum_repository/dnf/template/Handler/service。\n### ③ [操作点] cron 声明；远端 getent/rpm/systemctl/crontab/功能，第二次执行。","数据 → 身份 → 仓库/包 → 配置/Handler/服务 → cron → 远端/幂等。"),
 ("自动化对象要以 state 而非命令表达","专用模块让 Ansible 比较当前和目标；变量提供差异，Handler 绑定真实变化。recap 之外仍需在受管节点证明身份、包、服务和调度功能。"),
 [c("user.groups 如何追加而非替换？","设置 `append: true`。"),c("user.password 需要什么形式？","目标系统支持的密码哈希。"),c("管理 SSH 公钥模块？","`ansible.posix.authorized_key`"),c("authorized_key exclusive 在 loop 中的风险？","每项可能删除上一项未包含的 key。","","diagnosis"),c("创建 yum repo 模块？","`ansible.builtin.yum_repository`"),c("导入 RPM key 模块？","`ansible.builtin.rpm_key`"),c("服务当前与持久参数？","`state: started` 与 `enabled: true`。"),c("配置变化才重启如何表达？","template/copy notify Handler。"),c("cron 模块关键字段？","name、user、minute/hour/day/month/weekday、job。"),c("cron changed=0 能否证明执行成功？","不能；还要 crond 日志与产物。","","verification"),c("用户附加组丢失首查？","groups 与 append 语义。","","diagnosis"),c("系统自动化验收链？","变量/秘密 → 模块 state → 远端对象/功能 → 第二次执行。","","process")])

make("automate-network-selinux","第九章","自动化网络、防火墙与 SELinux","RHCE-NETWORK",
 "网络、安全与 SELinux 自动化要求同时表达当前和持久状态，并避免批量断连。模块或 RHEL System Role 描述目标连接；firewalld immediate/permanent、SELinux fcontext/port/boolean 分别对应不同策略对象。",
 ["网络变更可能切断 Ansible 控制通道，应先 limit、保留旧连接和控制台恢复路径。RHEL network System Role 以结构化变量表达连接集合。", "firewalld 的 permanent 与 immediate 分别写持久和 runtime；SELinux fcontext 建规则后仍要 restorecon，端口和 Boolean 是独立入口。"],
 ["`ansible.posix.firewalld`、`community.general.sefcontext/seport` 与 `ansible.posix.seboolean`（以安装 collection 文档为准）表达状态；command 只补没有模块的恢复动作。"],
 [("①","知识点","网络 role 输入必须按节点变量化","每台主机地址/网关/DNS 放 host/group vars，不在 task 中按主机名堆 when。应用连接前验证设备名与现有连接。"),("②","知识点","firewalld 双态","`permanent: true` 写持久；`immediate: true` 同时应用 runtime，前提 firewalld 运行。zone/service/port 必须匹配。"),("③","知识点","SELinux 三类状态","sefcontext 管路径规则，restorecon 应用当前标签；seport 管协议/端口类型；seboolean 的 persistent 管持久值。")],
 [("①","操作点","小范围应用网络","syntax/check（role 支持范围）、limit 单主机，等待连接恢复并重新 gather facts；再扩全组。"),("②","操作点","部署非标准 Web 安全状态","template 配置端口，firewalld service/port 双态，sefcontext+restorecon，seport，服务 Handler。"),("③","验证点","远端终态和外部访问","nmcli/ip、firewall-cmd 双查询、semanage/ls -Z/getsebool、ss 与外部 curl；第二次执行。")],
 [("①","诊断点","网络 task 后 unreachable","从控制台/旧地址确认 profile 与 route，检查 Ansible 是否等待重连；不要在全组重复错误连接。"),("②","诊断点","firewalld 每次 changed","检查 immediate/permanent、zone 和 module 版本字段，避免 reload command 每次执行。"),("③","诊断点","标签规则存在但访问仍拒绝","确认 restorecon 已应用、目标类型/端口/Boolean 与 AVC；规则存在不等于当前标签。")],
 ("自动部署自定义目录与端口 Web 服务","按主机变量配置网络；部署 httpd 自定义目录和 8080，配置 firewalld 当前/持久、SELinux 文件规则和端口类型。不得 Permissive。先一台再全组，验收连接恢复、安全三层、监听、外部 HTTP 和幂等性。"),
 ("按风险顺序应用网络与安全","### ① [操作点] network role limit，一台恢复连接并验证路由/DNS。\n### ② [操作点] 模板/Handler、firewalld 双态、sefcontext+restorecon、seport。\n### ③ [验证点] 远端命令与外部 curl，全组后第二次执行。","网络小范围/重连 → 服务 → 防火墙双态 → SELinux 规则/当前标签/端口 → 外部功能/幂等。"),
 ("自动化仍要尊重系统状态分层","模块把目标状态写成参数，但连接风险、runtime/permanent 和规则/当前标签的区别没有消失。先小范围、再远端证据、最后全量和幂等。"),
 [c("firewalld permanent 与 immediate 分别表达什么？","持久配置；立即应用 runtime。","","comparison"),c("管理 SELinux 文件规则的模块？","`community.general.sefcontext`（按安装版本文档）。"),c("规则建立后当前标签如何应用？","运行 restorecon，可用 command 补充。"),c("管理 SELinux 端口类型模块？","`community.general.seport`"),c("管理 Boolean 模块？","`ansible.posix.seboolean`"),c("网络自动化为什么先 limit？","错误地址/路由会切断控制连接。","","diagnosis"),c("firewall rule 正确能否证明服务监听？","不能。","还要 ss/协议访问。","verification"),c("sefcontext changed=0 能否证明当前标签正确？","不能；还要 ls -Z/matchpathcon。","","verification"),c("网络 task 后 unreachable 首要动作？","停止全量，使用恢复入口检查活动 profile/route。","","diagnosis"),c("自定义 Web 自动化验收层？","网络 → 服务 → firewall 双态 → SELinux 规则/标签/端口 → 外部 HTTP。","","process"),c("为什么不自动 setenforce 0？","改变安全目标并掩盖具体策略偏差。","","diagnosis"),c("第二次执行仍 reload firewall 查什么？","无条件 command 与模块双态参数。","","diagnosis")])

make("automate-storage","第十章","自动化存储、文件系统与挂载","RHCE-STORAGE",
 "存储自动化必须面对每台主机设备条件不同和写操作不可逆。模块能保证对象 state，却不能判断题目中的设备是否安全；设备证据、容量来源、文件系统和 mount 双态仍需逐层验证。",
 ["community.general.lvg/lvol 管 VG/LV，community.general.filesystem 管签名，ansible.posix.mount 管 fstab 与当前挂载；实际 FQCN/字段以已安装 Collection 为准。", "容量可表达绝对值、增量或百分比。自动化应描述目标总量，避免每次运行都增加；扩容文件系统需要 resizefs 或专用步骤，XFS 不缩小。"],
 ["先 gather facts/lsblk 调查，但不从设备名模式推定空闲。模块 state present 只推进对应层；远端 `pvs/vgs/lvs/blkid/findmnt/df` 形成验收。"],
 [("①","知识点","设备安全不是模块自动判断","lvg 的 pvs 参数会初始化/加入设备；题目设备不确定时先 assert 事实和人工证据门。不要自动 wipefs/force。"),("②","知识点","目标大小避免增量漂移","lvol size 写目标容量或百分比；使用扩容参数时确认模块幂等语义。每次 `+1G` 的命令式 shell 会持续增长。"),("③","验证点","LVM、文件系统和挂载三层","lvs 变大不代表 df 变大；mount state mounted/ephemeral/present 的当前与 fstab 语义不同，按模块文档选择。")],
 [("①","操作点","用变量描述每主机布局","host_vars 定义 devices、vg、lv、size、fstype、mount；assert 设备键存在和尺寸条件。"),("②","操作点","按依赖创建","lvg → lvol → filesystem → file mountpoint → mount。已有 filesystem 不重建；扩容使用 resizefs 并保留数据。"),("③","验证点","执行前后与幂等","limit 单主机，远端查对象/UUID/fstab/findmnt/df/数据；第二次无 changed，再扩全组。")],
 [("①","诊断点","VG 不存在或设备不存在","用 hostvars/Facts 与远端 lsblk 证明条件，fail/assert 给明确消息，不用 ignore_errors。"),("②","诊断点","LV 变大 df 不变","文件系统 resize 未完成；按类型执行模块 resize 或 xfs_growfs，不继续增加 LV。"),("③","诊断点","mount 每次 changed","检查 src 是否稳定（UUID/设备路径）、opts 顺序、state 与 fstab 现状；不要用 shell mount。")],
 ("按主机变量创建并挂载逻辑卷","在指定主机使用给定空闲设备创建 VG/LV/ext4 或 XFS 并持久挂载；空间不足时输出明确失败，不得格式化未知设备。随后扩容并保留标记数据。验收模块结果、三层容量、fstab、挂载和幂等。"),
 ("把设备差异放入变量并设置证据门","### ① [操作点] host_vars 描述布局，assert 设备/容量前提。\n### ② [操作点] lvg/lvol/filesystem/mount 按依赖；扩容 resizefs。\n### ③ [验证点] pvs/vgs/lvs、blkid、findmnt/df、标记校验，第二次执行。","变量/设备证据 → LVM → filesystem → mount → 数据 → 扩容 → 幂等。"),
 ("幂等模块不能替代设备风险判断","模块擅长比较已知对象状态，但初始化哪个设备仍由数据和证据决定。按依赖创建并分层验收，才能避免自动化放大破坏性错误。"),
 [c("创建 VG 常用模块？","`community.general.lvg`"),c("创建/扩展 LV 常用模块？","`community.general.lvol`"),c("创建文件系统模块？","`community.general.filesystem`"),c("持久并当前挂载模块？","`ansible.posix.mount`"),c("为什么不自动 wipefs？","可能破坏未知签名和数据。","","diagnosis"),c("为什么避免 shell `lvextend +1G`？","每次执行可能持续增长，非目标状态。","","diagnosis"),c("lvs 增长 df 不变说明？","文件系统未扩展。","","diagnosis"),c("存储模块顺序？","lvg → lvol → filesystem → mountpoint → mount。","","process"),c("设备差异放哪里？","host_vars/group_vars 的结构化布局。"),c("mount current 与 fstab 都需验证什么？","findmnt 与 fstab/模块 state。","","verification"),c("扩容保留数据怎样证明？","前后 checksum、lvs、df、findmnt。","","verification"),c("存储自动化发布前为何 limit？","错误设备变量会批量破坏。","","diagnosis")])

make("troubleshooting-idempotency","第十一章","Ansible 故障排除、验证与幂等性","RHCE-TROUBLESHOOTING",
 "Ansible 故障首先归类为控制端解析、Inventory 匹配、SSH/提权、模块执行或远端终态。verbosity 和 register 提供证据；ignore_errors、无条件 changed_when 或 recap 绿色不能替代根因修复。",
 ["FAILED 表示主机可达但任务失败，UNREACHABLE 表示连接层未建立，SKIPPED 是条件未满足，CHANGED 是模块认为状态改变。它们是执行分类，不是业务结论。", "幂等性要求相同目标状态重复执行不再改变；正确性要求目标本身符合题意。错误配置也可能稳定幂等，因此两者必须组合。"],
 ["从 `--syntax-check/--list-hosts` 开始，使用 `-v/-vvv` 增加证据，debug 注册对象，`--step/--start-at-task` 谨慎缩小；远端协议与系统查询最终验收。"],
 [("①","知识点","按失败层分类","YAML/模块字段在控制端；0 hosts 在 Inventory；unreachable 在 SSH；become 在 sudo；failed msg 在模块/远端；绿色 recap 后仍查终态。"),("②","知识点","changed 语义可被模块与规则改写","changed_when 应基于可靠输出，不为追求全绿无条件 false；failed_when 不能吞掉真实失败。"),("③","验证点","第二次执行与远端状态并行","比较两次 recap/任务 diff，同时从受管节点查文件、服务、端口、挂载和数据。")],
 [("①","操作点","最小化复现","syntax/list/limit 单主机，使用 tags/start-at-task 前确认依赖；verbosity 只提升到能回答问题的层。"),("②","操作点","读取 register 结构","debug var 完整结果，区分 rc/stdout/msg/results；用 assert 明确前置和验收条件。"),("③","验证点","修复后做全链回归","从失败层向下到远端功能，再全组执行和第二次执行；检查 Handler 是否按变化运行。")],
 [("①","诊断点","变量未定义/模板错误","查最终 hostvars、数据类型、模板路径和 scope；不要用 default 空值掩盖。"),("②","诊断点","unreachable 被当作 task 失败","业务模块尚未执行，先修 SSH/host key/remote_user/Python。"),("③","诊断点","每次 changed 但终态相同","查 command/shell、mtime、随机值、模板动态内容与 module 参数；不要全局 changed_when false。")],
 ("修复一个多层故障项目","项目同时存在错误 Inventory 组、变量类型、模板字段、Handler 名称和无条件 changed。要求逐层修复，不能 ignore_errors；最终全组终态正确且第二次无无法解释 changed。"),
 ("按层收缩并回归","### ① [诊断点] syntax/list-hosts/inventory 先修控制与范围；ping/become 修连接。\n### ② [诊断点] limit 运行，debug register/变量，修模板与 Handler。\n### ③ [验证点] 远端文件/服务/端口，全组与第二次执行。","控制端 → Inventory → 连接/become → task/Handler → 远端终态 → 全量/幂等。"),
 ("绿色执行不是最终判据","可靠排错让每个错误回到所属层，可靠验收同时看执行语义和远端事实。幂等性是正确终态的附加条件，不是替代条件。"),
 [c("FAILED 与 UNREACHABLE 区别？","任务执行失败；连接层未建立。","","comparison"),c("SKIPPED 表示什么？","条件不满足而未执行。"),c("changed 是否证明功能改变正确？","不证明。","","verification"),c("错误配置能否幂等？","能；稳定错误也可能无 changed。","","diagnosis"),c("0 hosts 首查什么？","Inventory/pattern/--list-hosts。","","diagnosis"),c("UNREACHABLE 首查什么？","SSH 地址、用户、密钥、host key、网络/Python。","","diagnosis"),c("become 失败首查什么？","远端 sudo 与 become 配置。","","diagnosis"),c("register 结构怎样检查？","`debug: var=result`"),c("为什么不全局 changed_when false？","会伪造幂等并隐藏真实变化。","","diagnosis"),c("verbosity 何时提高？","需要连接、变量或模块细节证据时。"),c("故障修复后的回归链？","失败层 → 远端功能 → 全组 → 第二次执行。","","process"),c("最终幂等判据？","第二次无无法解释 changed 且远端正确终态保持。","","verification")])

make("comprehensive","第十二章","RHCE 综合任务","RHCE-COMPREHENSIVE",
 "RHCE 综合任务把项目配置、变量、Vault、Role 和系统状态组合为一套多节点声明。完成标准不是 Playbook 数量，而是所有目标主机被正确覆盖、秘密安全、远端终态正确且第二次执行稳定。",
 ["控制面包含 ansible.cfg、Inventory、requirements、group_vars/host_vars、Vault、templates 和 roles；数据面是受管节点上的用户、包、服务、网络、安全和存储。", "执行应从静态边界到单主机，再到主机组和全量；每个阶段保留 recap 与远端证据。"],
 ["发布入口是可重复的构建/执行命令；`--syntax-check`、inventory graph、requirements install、vault access、limit/full/idempotence 和远端验收构成主链。"],
 [("①","知识点","先审计项目完整性","确认题目要求的文件路径、名称、权限、Vault 密文、Role/Collection 依赖和 Inventory 组均存在；不从任意工作目录执行。"),("②","知识点","桥接 RHCSA 目标为模块 state","用户/包/服务/防火墙/SELinux/存储使用专用模块或 System Roles；shell 仅补明确缺口并定义 changed/failed。"),("③","验证点","每组主机有独立终态矩阵","web、db、balancer 等分别核对变量差异、文件、服务、端口和安全；inventory 漏主机不会在 recap 中自动报错。")],
 [("①","操作点","执行前门","安装 requirements，vault view，syntax/list-hosts/list-tasks；ping/become；check/diff（支持范围）。"),("②","操作点","从一台到全量","limit 代表主机，修复控制/连接/task 问题并验远端；扩组、全量，观察 Handler 与失败分类。"),("③","验证点","第二次执行和外部功能","再次全量，解释 changed；从客户端验证 HTTP/网络，从节点验证身份、包、服务、SELinux、mount 和数据。")],
 [("①","诊断点","全绿但漏主机","对照题目与 `--list-hosts`/Inventory graph，不能只看 recap 中出现的主机。"),("②","诊断点","秘密或生成物泄露","检查 debug/no_log、明文密码文件权限、构建输出和版本控制；保持 Vault 加密。"),("③","诊断点","修一组破坏另一组","把差异移到变量/模板条件，回归所有共享 Role 消费者；不要复制分叉 Role。")],
 ("完成一个多组主机自动化项目","建立指定 Inventory/配置、Vault 与 Role，配置用户、仓库、包、模板/Handler、网络、防火墙/SELinux、LVM/mount，并使用 requirements。不得泄露秘密或掩盖错误。验收文件路径、主机覆盖、各组终态、外部功能与第二次执行。"),
 ("按发布门连续推进","### ① [操作点] 审计项目/依赖/Vault/Inventory，syntax/list/ping/become。\n### ② [操作点] limit 代表主机，远端验收；扩组与全量。\n### ③ [验证点] 全量第二次执行；按主机组矩阵查身份/服务/网络/安全/存储与外部功能。","项目完整性 → 静态/连接 → 单机 → 分组/全量 → 远端矩阵 → 幂等/安全审计。"),
 ("自动化交付是可复现的正确终态","项目源、依赖、秘密和执行边界必须可重建；受管节点的目标状态必须由专用模块表达并由外部证据验证；第二次执行则证明这种正确状态可以稳定维持。"),
 [c("RHCE 综合项目执行前四类门是什么？","项目/依赖、Vault、Inventory/配置、连接/become。","","process"),c("为什么 recap 不能发现 Inventory 漏主机？","未匹配主机根本不会进入执行。","","diagnosis"),c("如何证明主机覆盖？","inventory graph 与 playbook --list-hosts 对照题目。","","verification"),c("为什么先 limit 代表主机？","降低批量错误并暴露运行时问题。","","diagnosis"),c("何时扩展全组？","代表主机远端终态正确后。"),c("全量第一次后做什么？","远端矩阵验收并再次全量检查幂等。","","process"),c("秘密安全验收包含什么？","Vault 保持密文、密码入口权限、no_log、输出无明文。","","verification"),c("Role 共享变化后怎么验收？","回归所有消费组，不复制分叉。","","process"),c("系统状态映射原则？","优先专用模块/System Role，shell 只补明确缺口。"),c("第二次 0 changed 能否证明正确？","不能，仍需主机覆盖和远端功能。","","verification"),c("综合终态矩阵维度？","每组主机的身份、软件、文件、服务、网络、安全、存储、功能。","","process"),c("RHCE 完成判据？","全目标覆盖、远端正确、秘密安全、依赖可复现、第二次稳定。","","verification")])

if __name__=="__main__": print("seeded all RHCE systems")
