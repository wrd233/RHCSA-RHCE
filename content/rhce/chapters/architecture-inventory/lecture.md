---
title: "第一章 Ansible 架构、配置与 Inventory"
chapter_id: RHCE-INVENTORY
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE-Course-00-03, RHCE9-Mock]
---

# 第一章　Ansible 架构、配置与 Inventory

RHCE 的第一道证据链发生在控制节点：当前项目读取哪个 ansible.cfg、Inventory 匹配哪些主机、SSH 与提权使用什么身份。业务任务之前先证明执行边界，才能避免把 unreachable 误诊为模块错误。

**[概念]** 控制节点保存项目、Inventory、变量和内容；受管节点通常通过 SSH 接收临时模块执行，需要可用 Python 与适当提权。Ansible agentless 不等于没有远端前提。

**[概念]** Inventory 同时定义主机集合、组关系和少量连接变量；业务变量更适合 group_vars/host_vars。pattern 决定本次执行集合，错误匹配可能安静地遗漏主机。

**[操作语义]** `ansible-config dump --only-changed` 观察有效配置，`ansible-inventory --graph/--host` 展开 Inventory，`ansible <PATTERN> -m ping` 验证连接与 Python。

**[操作语义]** `ansible-doc` 查询模块和参数；ad hoc 适合一次性调查，Playbook 承担可重复目标状态。

<section class="topic knowledge" id="RHCE-INVENTORY-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> 配置发现、项目边界与连接前提

### ① [知识点] 配置来源有优先顺序
`ANSIBLE_CONFIG` 可显式指定；当前目录、家目录和系统配置按规则搜索。项目中一个拼错或不可读的 ansible.cfg 可能导致使用另一份配置。`ansible --version` 会显示 config file。

### ② [知识点] inventory、remote_user 与 become 是独立参数
SSH 登录用户先连接，become 再在远端切换权限。能 ping 不证明 become 成功；需要 `-b` 的受控命令单独验证。

### ③ [验证点] 输出有效配置与版本
```bash
ansible --version
ansible-config dump --only-changed
ansible-inventory --graph
```

**[Cheatsheet]** 先证配置文件与 inventory；再证主机图、SSH、Python 和 become；连接成功不替代业务终态。

</section>

<section class="topic operation" id="RHCE-INVENTORY-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 编写静态 Inventory 并验证 pattern

### ① [操作点] 定义主机、组与嵌套组
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
```

**[Cheatsheet]** Inventory graph/host → pattern list-hosts → ping → become 身份；每步回答一个边界。

</section>

<section class="topic diagnosis" id="RHCE-INVENTORY-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 区分 unmatched、unreachable 与 privilege failure

### ① [诊断点] pattern 匹配 0 主机
先 `--list-hosts` 和 inventory graph，检查组名、inventory 路径和 children，不改 SSH。

### ② [诊断点] UNREACHABLE
使用 `-vvv` 读取目标地址、用户、密钥和主机密钥错误；从控制节点手工 SSH 验证同一身份。

### ③ [诊断点] ping 成功但任务权限失败
检查 become、sudo 授权和 `ansible_become_user`，用 `id -u` 最小验证，不先给全局 NOPASSWD。

**[Cheatsheet]** 0 hosts 查 Inventory/pattern；unreachable 查 SSH；permission 查 become/sudo；不要在错误层修改业务任务。

</section>

<section class="classic-task task-page" id="RHCE-INVENTORY-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 建立可执行的多组主机项目

在指定目录创建 ansible.cfg 与静态 Inventory：web、db 两组归入 production，使用 devops 连接并按题意提权。不得关闭主机密钥检查或写明文口令。验收配置来源、组图、每台 hostvars、pattern、SSH/Python 和 root 提权。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-INVENTORY-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 从配置发现到提权逐层验收

### ① [操作点] 在题目目录写相对 inventory 路径和 remote_user/become 配置。
### ② [操作点] 定义 web/db 与 production:children，连接地址放 host vars。
### ③ [验证点] 运行 `ansible --version`、config dump、inventory graph/host、`--list-hosts`、ping 和 `command id -u -b`。若失败按 unmatched/unreachable/become 分层处理。

**[Cheatsheet]** config file → inventory graph/host → list-hosts → ping → become id；不把一层成功扩大。

</section>

<section class="topic closing" id="RHCE-INVENTORY-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 先固定执行边界，再编写业务状态

Inventory 与配置是所有 Playbook 的作用域。只有明确控制节点读取的文件、目标主机集合、连接身份和提权能力，后续模块失败才有可解释的上下文。

</section>
