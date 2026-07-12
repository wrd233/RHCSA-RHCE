from content_factory import write_chapter
def c(q,a,e="",t="ansible",p="P0"): return(q,a,e,t,p)
def body(items):
 return "\n\n".join(f"### {n} [{kind}] {title}\n{txt}" for n,kind,title,txt in items)
def make(slug,num,title,cid,sources,intro,concepts,semantics,kitems,oitems,ditems,task,solution,closing,cards):
 write_chapter(track="rhce",slug=slug,number=num,title=title,chapter_id=cid,sources=sources,intro=intro,concepts=concepts,semantics=semantics,
 topics=[(cid+"-K01","知识专题",kitems[0][2],body(kitems),"；".join(x[2] for x in kitems)),(cid+"-O01","操作专题",oitems[0][2],body(oitems),"；".join(x[2] for x in oitems)),(cid+"-D01","诊断专题",ditems[0][2],body(ditems),"；".join(x[2] for x in ditems))],
 task=task,solution=solution,closing=closing,cards=cards)

make("variables-facts","第三章","变量、Facts、注册结果与优先级","RHCE-VARIABLES",["RH294-RHEL9","RHCE-Course-06-07","RHCE9-Mock"],
 "变量把同一自动化逻辑映射到不同主机；Facts 描述受管节点，register 保存某个任务的运行结果。正确性取决于变量来源、数据类型、主机作用域和实际返回结构。",
 ["变量可来自 Inventory、group_vars、host_vars、play vars、vars_files、Facts、register、set_fact 和 extra vars；高优先级覆盖低优先级，但考试重点是减少冲突而非背完整表。","Facts 是每台主机的数据；magic variables 如 inventory_hostname、groups、hostvars 描述 Inventory 上下文。register 结果是字典，字段随模块与循环改变。"],
 ["`ansible-inventory --host` 观察 Inventory 变量；`ansible -m setup -a filter=...` 查询 Facts；`debug: var=` 显示对象结构而不套 Jinja 双括号。"],
 [("①","知识点","变量来源与作用域","group_vars/all 作用全体，组文件作用组，host_vars 作用单主机。文件名必须与 Inventory 名称对应；把同一变量在多层重复定义会让覆盖难以审计。"),("②","知识点","Facts 与 magic variables","`ansible_facts['distribution']` 等来自远端采集；`inventory_hostname` 不要求 DNS 可解析，`ansible_host` 是连接地址。`groups['web']` 是主机名列表，`hostvars[h]` 访问另一主机变量。"),("③","验证点","先看类型和最终值","使用 `debug: var=myvar`、type_debug 过滤器和 inventory --host。字符串 `false` 与布尔 false 不同，when 中尤其危险。")],
 [("①","操作点","组织 group_vars 与 host_vars","将共同值放 `group_vars/all.yml`，组差异放 `group_vars/web.yml`，主机例外放 `host_vars/servera.yml`；复杂数据使用 YAML 列表/字典。"),("②","操作点","注册并读取结果","`command` 任务 `register: check` 后读取 `check.rc/stdout/stderr/changed`；循环 register 的单项结果位于 `results`。不要假设所有模块都有 stdout。"),("③","验证点","按主机显示并应用差异","先 debug 代表主机的变量/Facts，再 limit 执行；最终在每组受管节点检查差异化文件和服务。")],
 [("①","诊断点","变量未定义","用 -vvv、debug 和 inventory --host 查拼写、文件名、作用域和条件分支，不用 default 隐藏必需变量缺失。"),("②","诊断点","字典字段不存在","先 debug 完整 register/Facts 结构，循环结果尤其查看 results；不要从示例版本推定字段。"),("③","诊断点","值正确但类型错误","用 type_debug 检查引号导致的字符串/布尔/整数差异，修正数据源而非在每个 task 强制转换。")],
 ("用组变量和 Facts 部署差异配置","web 与 db 组使用不同包、端口和模板值；RHEL 9 才执行目标任务。不得复制两份 Playbook。验收最终变量、Facts 条件、每组文件和服务。"),
 ("把差异放入数据并验证返回结构","### ① [操作点] 在 group_vars 定义 `service_package/service_port`，用 Facts 条件限制 RHEL 9。\n### ② [操作点] 注册验证命令并根据 rc 显示明确结果。\n### ③ [验证点] inventory --host、debug type、limit 与远端文件/监听交叉检查。","数据源 → 类型 → host 最终值 → limit 执行 → 每组终态。"),
 ("变量只有在主机上下文中才有确定值","把共享值、组差异和主机例外放在最小层次；Facts 与 register 先观察结构再引用。这样优先级不再是猜测，而是可查询的数据合并结果。"),
 [c("查看单主机最终 Inventory 变量用什么？","`ansible-inventory --host <HOST>`"),c("debug 一个变量对象的推荐语法是什么？","`ansible.builtin.debug: var=myvar`","var 参数不写 `{{ }}`。"),c("inventory_hostname 与 ansible_host 区别？","逻辑主机名；连接地址。","comparison"),c("循环任务的 register 单项结果通常在哪里？","`result.results`","先 debug 完整结构。"),c("command register 高频字段有哪些？","rc、stdout、stderr、changed。"),c("所有模块都有 stdout 吗？","没有；返回字段取决于模块。","","diagnosis"),c("检查变量类型用哪个过滤器？","`type_debug`"),c("字符串 'false' 能否等同布尔 false？","不能。","when 中尤其危险。","diagnosis"),c("groups['web'] 保存什么？","web 组 inventory 主机名列表。"),c("hostvars 的作用是什么？","按主机名访问该主机变量字典。"),c("必需变量缺失时能否无条件 default 隐藏？","不应；应修正数据源或显式 assert。","","diagnosis"),c("变量任务验收链？","数据源/类型 → host 最终值 → limit → 远端差异终态。","","process")])

make("loops-conditionals-handlers","第四章","循环、条件、Handler、Block 与错误控制","RHCE-CONTROL",["RH294-RHEL9","RHCE-Course-05-09","RHCE9-Mock"],
 "控制结构用于对数据集合和主机差异重复表达目标，同时让变更、失败和恢复保持可解释。循环不是复制 task，Handler 不是无条件重启，错误控制也不能把必须失败的状态吞掉。",
 ["loop 为每项设置 item，可用 loop_control 改名；when 对每台主机和每个 item 求值。Handler 只在通知 task 返回 changed 时排队，默认在 play 后部运行。","block 组织任务并可配 rescue/always；failed_when 和 changed_when 改写结果语义，必须基于可靠返回字段。"],
 ["`notify` 触发命名 Handler，`meta: flush_handlers` 提前运行；`assert` 把前置条件写成明确失败。"],
 [("①","知识点","循环数据应保持结构","字典列表让 item.name/item.state 明确。避免平行列表和基于索引拼接。loop_control.label 只改善输出，不改变数据。"),("②","知识点","when 不使用 Jinja 定界符","`when: ansible_facts['os_family'] == 'RedHat'` 是表达式；字符串布尔需要显式类型。多个条件列表通常 AND。"),("③","知识点","Handler 合并通知","同一 Handler 被多次通知通常只运行一次；通知 task 未 changed 则不运行。配置变化才重启是幂等关键。")],
 [("①","操作点","循环创建对象","使用 user/package 等专用模块遍历字典；给 loop_var 命名避免 include 嵌套 item 冲突。"),("②","操作点","根据 register 定义结果","command 探测可用 `changed_when: false`，按 rc 定义 failed_when；但专用查询模块优先。"),("③","验证点","检查 changed 与 Handler 时点","第一轮配置变化应通知，第二轮无变化不应重启；必要时 flush 后再做依赖 Handler 的功能验证。")],
 [("①","诊断点","ignore_errors 掩盖失败","它继续执行但主机仍有失败语义，可能让后续使用无效状态。合法替代是明确 failed_when 或 block/rescue。"),("②","诊断点","Handler 未运行","查通知 task 是否 changed、notify 名称、play 是否在失败前到达 Handler，必要时 flush。"),("③","诊断点","每轮都 changed","查 command/shell、时间戳内容、changed_when 和模块目标值；第二次执行定位具体 task。")],
 ("批量创建服务并只在变化时重启","从字典列表安装多个包并部署配置；仅配置改变时重启对应服务。对不满足内存条件主机明确跳过，并在失败时输出可诊断信息。"),
 ("让数据、条件和 Handler 对齐","### ① [操作点] loop 字典调用 package，模板 task notify Handler。\n### ② [操作点] when 使用 Facts；block/rescue 处理受控异常。\n### ③ [验证点] 第一轮观察 changed/handler，第二轮确认无重启，远端查服务。","结构数据 → when → 变更通知 → Handler → 第二次执行。"),
 ("控制结构应提高可解释性","循环减少重复，条件限定适用主机，Handler 绑定真实变更，block 保留失败边界。任何结构都应让 recap 和远端终态更清楚，而不是隐藏错误。"),
 [c("when 表达式是否写 `{{ }}`？","不写。","when 本身解析表达式。"),c("多个 when 列表项通常是什么关系？","AND。"),c("Handler 何时被通知？","notify 所在 task 返回 changed 时。"),c("同一 Handler 多次通知通常运行几次？","一次。"),c("提前执行已通知 Handler 用什么？","`ansible.builtin.meta: flush_handlers`"),c("探测 command 怎样避免虚假 changed？","`changed_when: false`"),c("ignore_errors 的主要风险？","掩盖必须失败的状态并让后续基于坏数据继续。","","diagnosis"),c("block/rescue/always 分别作用？","主任务、失败恢复、无论结果都执行的清理。","","comparison"),c("循环 register 的结果在哪里？","`registered.results`"),c("嵌套 include 避免 item 冲突用什么？","`loop_control.loop_var`"),c("每轮都 changed 首先查什么？","具体 task 的命令、动态内容和 changed_when。","","diagnosis"),c("Handler 未运行查什么？","通知 task changed、notify 名称和失败时点。","","diagnosis"),c("控制结构幂等验收？","第一轮合理 changed/handler；第二轮无无解释 changed；远端服务正确。","","process")])

make("files-templates-jinja","第五章","文件、模板与 Jinja2","RHCE-TEMPLATES",["RH294-RHEL9","RHCE-Course-10-11","RHCE9-Mock"],
 "文件自动化首先选择所有权边界：完整内容由 copy/template 管，单行由 lineinfile 管，受标记区块由 blockinfile 管。模板把变量渲染成每台主机的完整文件，错误内容也可能幂等。",
 ["file 管路径状态/身份/模式，copy 分发静态内容，template 渲染 Jinja2，lineinfile 维护一行，blockinfile 维护带 marker 的区块。选择过细工具修改完整受管文件会留下未知旧内容。","Jinja2 `{{ }}` 输出表达式，`{% %}` 控制结构，`{# #}` 注释。模板在控制节点渲染，Facts/变量来自目标主机上下文。"],
 ["`template` 的 validate 在替换前用临时文件运行校验命令；成功后原子替换并 notify Handler。diff 与远端语法/功能共同验收。"],
 [("①","知识点","按所有权选择文件模块","完整文件归项目所有用 template/copy；只拥有一行用 lineinfile；只拥有区块用 blockinfile。`file state=touch` 每次改变时间，不适合只保证存在。"),("②","知识点","模板变量必须处理缺失与类型","用 mandatory/assert 处理必需数据；default 只用于合法默认。过滤器如 join、sort、to_nice_yaml 改变输出，要检查目标格式。"),("③","验证点","内容、元数据和消费者分层","`stat`/slurp/checksum 查文件，应用 `-t` 或 validate 查语法，服务 active/HTTP 查功能。")],
 [("①","操作点","渲染差异配置","模板使用 inventory_hostname、组变量和 Facts；for 循环生成重复行，if 只表达真正主机差异。保持缩进与换行符合目标格式。"),("②","操作点","安全替换并通知","template 设置 owner/group/mode、backup（按需）、validate，并 notify restart Handler；只有内容/元数据变化才 changed。"),("③","验证点","check/diff 与远端语法","先 `--check --diff` 预览支持的变化，再 limit 执行；远端运行应用校验并查看渲染内容。")],
 [("①","诊断点","模板变量未定义","定位变量作用域和拼写，debug 数据结构；不在模板各处 default 空字符串。"),("②","诊断点","渲染成功但服务失败","控制端 Jinja 合法不等于目标配置语法合法；使用 validate 和远端日志。"),("③","诊断点","lineinfile 每次 changed","检查 regexp 是否能匹配写入后的 line，避免插入重复行；必要时选择 template。")],
 ("为不同主机生成服务配置并安全重载","使用一个模板按 web 组变量生成监听端口和后端列表，所有者/模式固定；配置校验成功且内容变化时才重载服务。验收 diff、远端内容、语法、Handler、监听和第二次执行。"),
 ("让模板成为完整文件真相","### ① [操作点] 在 j2 中使用明确变量、循环与最小条件。\n### ② [操作点] template 设元数据和 validate，notify reload Handler。\n### ③ [验证点] check/diff、limit、远端语法/监听，第二次无 changed。","数据 → 模板 → validate → 原子替换 → Handler → 远端功能/幂等。"),
 ("文件模块的选择决定维护边界","完整文件、单行和区块应由不同模块承担。Jinja 只负责渲染，validate 与远端功能证明内容可用；第二次执行证明表达稳定。"),
 [c("完整差异配置文件首选什么模块？","`ansible.builtin.template`"),c("静态文件分发首选什么？","`ansible.builtin.copy`"),c("只维护一行首选什么？","`ansible.builtin.lineinfile`"),c("维护带 marker 区块首选什么？","`ansible.builtin.blockinfile`"),c("为什么 file state=touch 常非幂等？","会更新 mtime。","","diagnosis"),c("Jinja 输出与控制标记是什么？","`{{ }}` 与 `{% %}`。","","syntax"),c("template validate 的价值？","替换目标前对临时渲染文件运行语法检查。","","verification"),c("模板渲染成功能否证明服务配置有效？","不能；还要应用语法和功能验证。","","verification"),c("lineinfile 每次 changed 查什么？","regexp 是否匹配写入后的最终行。","","diagnosis"),c("模板内容变化如何只触发一次重载？","notify Handler。"),c("文件验收三层？","内容/校验值、owner/group/mode、消费者语法/功能。","","process"),c("模板章幂等验收？","第二次无模板 changed、无 Handler，远端功能仍正确。","","process")])

make("external-data-vault","第六章","外部数据、敏感变量与 Vault","RHCE-VAULT",["RH294-RHEL9","RHCE-Course-06-12","RHCE9-Mock"],
 "外部变量把用户、服务和环境数据从任务逻辑中分离；Vault 只加密静态内容，不自动隐藏运行时输出。正确流程同时保证数据结构可解析、秘密在磁盘中加密、运行时可解密且日志不泄露。",
 ["vars_files 显式加载数据文件，group_vars/host_vars 按 Inventory 自动加载。YAML 列表适合对象集合，字典适合按名称索引；稳定 schema 比在 task 中兼容多种形状更可靠。","Vault 可加密整个文件或单个字符串。vault ID 允许多个密码来源；密码文件本身必须受保护且不进入发布内容。"],
 ["`ansible-vault create/edit/view/encrypt/decrypt/rekey/encrypt_string` 管密文；`--vault-password-file` 或 `--vault-id` 提供运行时秘密。`no_log: true` 只在必要 task 抑制输出。"],
 [("①","知识点","外部数据要有明确 schema","批量用户可定义 name/groups/password_hash 等键；Playbook 用 assert 验证必需键，避免部分对象执行到中途才失败。"),("②","知识点","Vault 密文仍是内容源","编辑用 ansible-vault edit，不先 decrypt 留明文临时文件。`rekey` 更换密码保持数据加密；decrypt 是明确导出明文的高风险操作。"),("③","验证点","检查文件头和安全输出","Vault 文件以 `$ANSIBLE_VAULT;` 开头；view 能按授权读取。运行后检查目标终态，不打印秘密值。")],
 [("①","操作点","加载外部用户列表","`vars_files` 加载 YAML，loop 遍历用户字典；密码字段应是目标模块所需哈希，不把明文直接传给 user.password。"),("②","操作点","创建和改密 Vault","使用 create/edit；密码轮换用 rekey old/new vault-id。密码文件权限收紧并排除版本控制。"),("③","验证点","语法、解密与远端对象","先 vault view 和 playbook syntax-check，再 limit；远端用 getent/id 验证用户，不回显哈希。")],
 [("①","诊断点","no vault secrets found","检查当前项目是否收到正确 vault-id/password file，文件是否被错误 decrypt 或 vault ID 不匹配。"),("②","诊断点","秘密出现在日志","给最小敏感 task 设置 no_log，并审查 debug、失败消息与注册变量；不能靠删终端历史作为修复。"),("③","诊断点","数据结构与 loop 不匹配","debug 仅显示非敏感键/类型，使用 assert；修正 schema，不在任务中叠加复杂兼容。")],
 ("使用加密变量批量创建账号","下载/提供的用户列表保存在外部 YAML，密码哈希放 Vault；按组变量选择附加组。密码文件路径由题目指定且不得泄露。验收 Vault 保持加密、Playbook 可运行、用户/组正确且输出无秘密。"),
 ("以 schema 和 Vault 边界驱动用户任务","### ① [操作点] 验证用户列表必需键，Vault 保存哈希与敏感值。\n### ② [操作点] vars_files 加载，user 模块 loop 创建；敏感 task no_log。\n### ③ [验证点] vault view/syntax/limit，远端 getent/id，最终确认源文件仍加密。","schema/assert → Vault → 安全加载 → user loop → 远端身份 → 密文与日志审计。"),
 ("加密不等于不会泄露","Vault 保护静态文件，no_log 控制任务输出，文件权限和版本控制保护密码入口。三层同时成立，外部数据才既可维护又安全。"),
 [c("创建/编辑/查看 Vault 文件分别用什么？","`ansible-vault create/edit/view`"),c("轮换 Vault 密码且保持加密用什么？","`ansible-vault rekey`"),c("加密单个值用什么？","`ansible-vault encrypt_string`"),c("Vault 文件头典型是什么？","`$ANSIBLE_VAULT;...`","","output"),c("Vault 是否自动隐藏运行时输出？","不会。","敏感 task 需 no_log。","diagnosis"),c("no_log 应放在哪里？","最小的敏感 task/block。","过宽会阻碍诊断。"),c("user.password 应传明文吗？","不应；通常传目标系统支持的密码哈希。","","diagnosis"),c("vars_files 与 group_vars 区别？","前者 play 显式加载；后者按 Inventory 自动加载。","","comparison"),c("批量数据执行前如何验证 schema？","用 assert 检查必需键和类型。"),c("为什么不先 decrypt 再编辑？","会在磁盘留下明文并扩大泄露窗口。","使用 vault edit。","diagnosis"),c("Vault 验收层？","文件仍加密、授权可 view、Playbook 解密运行、日志无秘密、远端终态正确。","","process"),c("no vault secrets found 查什么？","vault-id/password file、文件头与 ID 匹配。","","diagnosis")])

if __name__=="__main__": print("seeded RHCE bulk complete foundations")
