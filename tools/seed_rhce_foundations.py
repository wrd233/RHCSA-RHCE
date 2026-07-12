from content_factory import write_chapter
def c(q,a,e="",t="ansible",p="P0"): return(q,a,e,t,p)

write_chapter(
 track="rhce",slug="architecture-inventory",number="第一章",title="Ansible 架构、配置与 Inventory",chapter_id="RHCE-INVENTORY",
 sources=["RH294-RHEL9","RHCE-Course-00-03","RHCE9-Mock"],
 intro="RHCE 的第一道证据链发生在控制节点：当前项目读取哪个 ansible.cfg、Inventory 匹配哪些主机、SSH 与提权使用什么身份。业务任务之前先证明执行边界，才能避免把 unreachable 误诊为模块错误。",
 concepts=["控制节点保存项目、Inventory、变量和内容；受管节点通常通过 SSH 接收临时模块执行，需要可用 Python 与适当提权。Ansible agentless 不等于没有远端前提。", "Inventory 同时定义主机集合、组关系和少量连接变量；业务变量更适合 group_vars/host_vars。pattern 决定本次执行集合，错误匹配可能安静地遗漏主机。"],
 semantics=["`ansible-config dump --only-changed` 观察有效配置，`ansible-inventory --graph/--host` 展开 Inventory，`ansible <PATTERN> -m ping` 验证连接与 Python。", "`ansible-doc` 查询模块和参数；ad hoc 适合一次性调查，Playbook 承担可重复目标状态。"],
 topics=[
 ("RHCE-INVENTORY-K01","知识专题","配置发现、项目边界与连接前提","""### ① [知识点] 配置来源有优先顺序
`ANSIBLE_CONFIG` 可显式指定；当前目录、家目录和系统配置按规则搜索。项目中一个拼错或不可读的 ansible.cfg 可能导致使用另一份配置。`ansible --version` 会显示 config file。

### ② [知识点] inventory、remote_user 与 become 是独立参数
SSH 登录用户先连接，become 再在远端切换权限。能 ping 不证明 become 成功；需要 `-b` 的受控命令单独验证。

### ③ [验证点] 输出有效配置与版本
```bash
ansible --version
ansible-config dump --only-changed
ansible-inventory --graph
```""","先证配置文件与 inventory；再证主机图、SSH、Python 和 become；连接成功不替代业务终态。"),
 ("RHCE-INVENTORY-O01","操作专题","编写静态 Inventory 并验证 pattern","""### ① [操作点] 定义主机、组与嵌套组
```ini
[web]
servera ansible_host=192.0.2.11
serverb ansible_host=192.0.2.12

[production:children]
web
```
Inventory 名称是 `inventory_hostname`，连接地址可以不同。

### ② [操作点] 建立最小项目配置
```ini
[defaults]
inventory=./inventory
remote_user=devops
host_key_checking=True

[privilege_escalation]
become=True
```
不要把口令明文写进配置；使用题目提供的安全入口。

### ③ [验证点] 展开、匹配和连接
```bash
ansible-inventory --graph
ansible-inventory --host servera
ansible web --list-hosts
ansible web -m ansible.builtin.ping
ansible web -b -m ansible.builtin.command -a 'id -u'
```""","Inventory graph/host → pattern list-hosts → ping → become 身份；每步回答一个边界。"),
 ("RHCE-INVENTORY-D01","诊断专题","区分 unmatched、unreachable 与 privilege failure","""### ① [诊断点] pattern 匹配 0 主机
先 `--list-hosts` 和 inventory graph，检查组名、inventory 路径和 children，不改 SSH。

### ② [诊断点] UNREACHABLE
使用 `-vvv` 读取目标地址、用户、密钥和主机密钥错误；从控制节点手工 SSH 验证同一身份。

### ③ [诊断点] ping 成功但任务权限失败
检查 become、sudo 授权和 `ansible_become_user`，用 `id -u` 最小验证，不先给全局 NOPASSWD。""","0 hosts 查 Inventory/pattern；unreachable 查 SSH；permission 查 become/sudo；不要在错误层修改业务任务。"),
 ],
 task=("建立可执行的多组主机项目", "在指定目录创建 ansible.cfg 与静态 Inventory：web、db 两组归入 production，使用 devops 连接并按题意提权。不得关闭主机密钥检查或写明文口令。验收配置来源、组图、每台 hostvars、pattern、SSH/Python 和 root 提权。"),
 solution=("从配置发现到提权逐层验收","""### ① [操作点] 在题目目录写相对 inventory 路径和 remote_user/become 配置。
### ② [操作点] 定义 web/db 与 production:children，连接地址放 host vars。
### ③ [验证点] 运行 `ansible --version`、config dump、inventory graph/host、`--list-hosts`、ping 和 `command id -u -b`。若失败按 unmatched/unreachable/become 分层处理。""","config file → inventory graph/host → list-hosts → ping → become id；不把一层成功扩大。"),
 closing=("先固定执行边界，再编写业务状态","Inventory 与配置是所有 Playbook 的作用域。只有明确控制节点读取的文件、目标主机集合、连接身份和提权能力，后续模块失败才有可解释的上下文。"),
 cards=[
c("查看 Ansible 当前使用的配置文件，最直接看什么？","`ansible --version` 输出中的 config file。","再用 config dump 看有效差异。"),
c("显示非默认有效配置的命令是什么？","`ansible-config dump --only-changed`","用于发现配置漂移。"),
c("以树形展示 Inventory 组关系用什么？","`ansible-inventory --graph`","不能证明连接。"),
c("展开某主机最终 Inventory 变量用什么？","`ansible-inventory --host <HOST>`","观察 hostvars 合并。"),
c("Inventory 名称与 ansible_host 的区别是什么？","前者是逻辑 inventory_hostname，后者是连接地址。","模板中常需区分。","comparison"),
c("children 组的 ini 标题骨架是什么？","`[parent:children]`","下面列子组名。","syntax"),
c("验证 pattern 实际匹配主机用什么？","`ansible <PATTERN> --list-hosts`","在执行前使用。","verification"),
c("ansible.builtin.ping 证明什么？","控制端能通过连接执行 Python 模块并返回 pong。","不证明 ICMP 或 become。","verification"),
c("验证 become 到 root 的最小 ad hoc 命令骨架是什么？","`ansible <PATTERN> -b -m ansible.builtin.command -a 'id -u'`","预期输出 0。"),
c("pattern 匹配 0 主机首先查什么？","Inventory 路径、graph、组名和 --list-hosts。","不先查 SSH。","diagnosis"),
c("UNREACHABLE 首先查哪一层？","SSH 地址、用户、密钥、主机密钥和网络。","用 -vvv 与同身份 ssh。","diagnosis"),
c("ping 成功但权限失败下一步是什么？","检查 become 配置和远端 sudo 授权。","连接层已成立。","diagnosis"),
c("为什么不把口令放入 ansible.cfg/Inventory？","会明文泄露且扩大项目暴露面。","使用 Vault 或题目安全入口。","diagnosis"),
c("RHCE 项目执行前的证据链是什么？","配置来源 → Inventory 图/变量 → pattern → SSH/Python → become。","再进入业务模块。","process"),
 ]
)

write_chapter(
 track="rhce",slug="yaml-playbook-modules",number="第二章",title="YAML、Playbook、Task 与模块",chapter_id="RHCE-PLAYBOOK",
 sources=["RH294-RHEL9","RHCE-Course-03-05","RHCE9-Mock"],
 intro="Playbook 把目标主机、提权和一组任务写成可重复执行的 YAML。结构能通过解析只是第一道门，模块参数、目标主机、远端终态和第二次执行仍需独立验证。",
 concepts=["YAML mapping 表达键值，sequence 表达列表；缩进属于结构，Tab 不用于缩进。一个 play 选择 hosts 并包含 tasks，每个 task 调用一个模块。", "专用模块表达目标状态并返回 changed；command 不经 Shell，shell 才解释管道/重定向。能用专用模块时不用无条件命令。"],
 semantics=["`ansible-playbook --syntax-check/--list-hosts/--list-tasks` 分别检查解析、主机和任务边界；`--check --diff` 在模块支持范围内预览。", "模块返回 ok/changed/failed/skipped；recap 总结执行，不证明远端业务功能。"],
 topics=[
 ("RHCE-PLAYBOOK-K01","知识专题","YAML 结构、标量和模块参数","""### ① [知识点] playbook 顶层是 play 列表
```yaml
---
- name: Configure web
  hosts: web
  become: true
  tasks:
    - name: Install httpd
      ansible.builtin.dnf:
        name: httpd
        state: present
```

### ② [知识点] 布尔与权限模式要避免类型歧义
布尔用 `true/false`；文件 mode 常引用为 `'0644'`，避免 YAML 数值解释。含冒号、`#` 或 Jinja 表达式开头的字符串按需引用。

### ③ [验证点] 先让解析器和 ansible-doc 证明字段
`ansible-doc ansible.builtin.dnf` 查询字段，不从其他模块类推参数名。""","顶层 play 列表；play 含 hosts/tasks；task 只调用一个模块；布尔 true/false、mode 引用；字段查 ansible-doc。"),
 ("RHCE-PLAYBOOK-O01","操作专题","安装、配置并启动服务的最小 Playbook","""### ① [操作点] 用目标状态模块
```yaml
- name: Deploy web
  hosts: web
  become: true
  tasks:
    - ansible.builtin.dnf:
        name: httpd
        state: present
    - ansible.builtin.copy:
        content: "exam\n"
        dest: /var/www/html/index.html
        mode: '0644'
    - ansible.builtin.service:
        name: httpd
        state: started
        enabled: true
```

### ② [验证点] 静态、限制执行与远端终态
```bash
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml --list-hosts
ansible-playbook site.yml --limit servera
ansible web -b -m command -a 'systemctl is-enabled httpd'
```
再从受管节点或客户端检查文件与 HTTP。

### ③ [验证点] 第二次执行解释 changed
第二次无 changed 是幂等证据；仍有 changed 时逐 task 查无条件 command、动态内容或错误 changed_when。""","syntax/list → limit 执行 → recap → 远端文件/服务/HTTP → 全量 → 第二次执行；recap 不替代终态。"),
 ("RHCE-PLAYBOOK-D01","诊断专题","区分 YAML、模块、连接和远端失败","""### ① [诊断点] syntax error
根据行列号检查上一层缩进、冒号和列表标记，不只盯报错行。

### ② [诊断点] unsupported parameters
用 `ansible-doc` 核对 FQCN 与当前 collection 版本字段，不把其他模块参数复制过来。

### ③ [诊断点] command 与 shell 选错
command 中 `|`、`>` 不会由 Shell 解释；若确需 Shell 使用 shell 并确保幂等/引用，优先寻找专用模块。""","解析错查 YAML；参数错查 ansible-doc；unreachable 回连接层；远端 failed 读 module msg；命令行为先选专用模块。"),
 ],
 task=("用 Playbook 部署可重复 Web 终态", "在 web 组安装 httpd、部署指定首页并启用服务。第一次先限制到一台，随后扩展全组，第二次执行应无无法解释的 changed。不得用 shell 模拟包、文件和服务模块。验收语法、主机范围、recap、远端文件、active/enabled 与 HTTP。"),
 solution=("用三个专用模块表达终态","""### ① [操作点] 使用 `ansible.builtin.dnf`、`copy`、`service` 分别表达包、文件和服务。
### ② [验证点] syntax-check、list-hosts 后 limit 执行；远端检查 rpm、stat、systemctl 与 curl。
### ③ [验证点] 全组执行后第二次运行，逐项解释 changed；最终再次 HTTP 验收。""","专用模块 → 静态边界 → 小范围 → 远端终态 → 全量 → 第二次执行。"),
 closing=("执行成功必须落到远端目标状态","YAML 和模块把意图结构化，但只有目标主机范围正确、模块字段有效、远端对象符合要求且重复执行稳定，Playbook 才真正完成。"),
 cards=[
c("Playbook 顶层 YAML 类型是什么？","play 的列表（sequence）。","每个 play 是 mapping。","concept"),
c("一个 task 通常应调用几个模块？","一个。","name/when/register 等是 task 关键字。","concept"),
c("为什么 mode 常写 `'0644'`？","避免 YAML 数值类型歧义并保留权限表达。","模块接收明确模式。","parameter"),
c("查询模块字段和示例用什么？","`ansible-doc <FQCN>`","以当前安装版本为准。"),
c("syntax-check 证明什么？","控制端能解析 Playbook 和静态结构。","不证明连接或远端成功。","verification"),
c("执行前查看目标主机用什么？","`ansible-playbook play.yml --list-hosts`","避免错误范围。","verification"),
c("限制第一轮到 servera 用什么？","`--limit servera`","成功后再扩展。","parameter"),
c("command 与 shell 的关键区别是什么？","command 不经 Shell；shell 解释管道、重定向等。","优先专用模块。","comparison"),
c("为什么包安装优先 dnf 模块而不是 command？","模块表达 state 并能幂等判断。","command 通常每次执行。","diagnosis"),
c("recap 无 failed 能否证明 HTTP 正确？","不能；还要远端服务/监听和协议验证。","执行结果不等于功能。","verification"),
c("第二次仍 changed 的调查方向是什么？","定位具体 task 的动态输入、无条件命令或 changed_when。","先解释再接受。","diagnosis"),
c("unsupported parameters 下一步是什么？","核对 FQCN 和 ansible-doc 当前字段。","不猜参数。","diagnosis"),
c("YAML 报错行一定是根因行吗？","不一定；上一层缩进或未闭合结构可导致后续报错。","向上检查。","diagnosis"),
c("Playbook 完整验收链是什么？","syntax/list → limit → 远端终态 → 全量 → 第二次执行 → 再验收。","幂等与正确性都要。","process"),
 ]
)

if __name__=="__main__": print("seeded RHCE foundations")
