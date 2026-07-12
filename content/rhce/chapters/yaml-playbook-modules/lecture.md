---
title: "第二章 YAML、Playbook、Task 与模块"
chapter_id: RHCE-PLAYBOOK
exam: RHCE
validation: static-verified
sources: [RH294-RHEL9, RHCE-Course-03-05, RHCE9-Mock]
---

# 第二章　YAML、Playbook、Task 与模块

Playbook 把目标主机、提权和一组任务写成可重复执行的 YAML。结构能通过解析只是第一道门，模块参数、目标主机、远端终态和第二次执行仍需独立验证。

**[概念]** YAML mapping 表达键值，sequence 表达列表；缩进属于结构，Tab 不用于缩进。一个 play 选择 hosts 并包含 tasks，每个 task 调用一个模块。

**[概念]** 专用模块表达目标状态并返回 changed；command 不经 Shell，shell 才解释管道/重定向。能用专用模块时不用无条件命令。

**[操作语义]** `ansible-playbook --syntax-check/--list-hosts/--list-tasks` 分别检查解析、主机和任务边界；`--check --diff` 在模块支持范围内预览。

**[操作语义]** 模块返回 ok/changed/failed/skipped；recap 总结执行，不证明远端业务功能。

<section class="topic knowledge" id="RHCE-PLAYBOOK-K01" data-kind="knowledge-topic">

## <span class="topic-label">[知识专题]</span> YAML 结构、标量和模块参数

### ① [知识点] playbook 顶层是 play 列表
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
`ansible-doc ansible.builtin.dnf` 查询字段，不从其他模块类推参数名。

**[Cheatsheet]** 顶层 play 列表；play 含 hosts/tasks；task 只调用一个模块；布尔 true/false、mode 引用；字段查 ansible-doc。

</section>

<section class="topic operation" id="RHCE-PLAYBOOK-O01" data-kind="operation-topic">

## <span class="topic-label">[操作专题]</span> 安装、配置并启动服务的最小 Playbook

### ① [操作点] 用目标状态模块
```yaml
- name: Deploy web
  hosts: web
  become: true
  tasks:
    - ansible.builtin.dnf:
        name: httpd
        state: present
    - ansible.builtin.copy:
        content: "exam\\n"
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
第二次无 changed 是幂等证据；仍有 changed 时逐 task 查无条件 command、动态内容或错误 changed_when。

**[Cheatsheet]** syntax/list → limit 执行 → recap → 远端文件/服务/HTTP → 全量 → 第二次执行；recap 不替代终态。

</section>

<section class="topic diagnosis" id="RHCE-PLAYBOOK-D01" data-kind="diagnosis-topic">

## <span class="topic-label">[诊断专题]</span> 区分 YAML、模块、连接和远端失败

### ① [诊断点] syntax error
根据行列号检查上一层缩进、冒号和列表标记，不只盯报错行。

### ② [诊断点] unsupported parameters
用 `ansible-doc` 核对 FQCN 与当前 collection 版本字段，不把其他模块参数复制过来。

### ③ [诊断点] command 与 shell 选错
command 中 `|`、`>` 不会由 Shell 解释；若确需 Shell 使用 shell 并确保幂等/引用，优先寻找专用模块。

**[Cheatsheet]** 解析错查 YAML；参数错查 ansible-doc；unreachable 回连接层；远端 failed 读 module msg；命令行为先选专用模块。

</section>

<section class="classic-task task-page" id="RHCE-PLAYBOOK-C01" data-kind="classic-task">

## <span class="topic-label">[经典任务]</span> 用 Playbook 部署可重复 Web 终态

在 web 组安装 httpd、部署指定首页并启用服务。第一次先限制到一台，随后扩展全组，第二次执行应无无法解释的 changed。不得用 shell 模拟包、文件和服务模块。验收语法、主机范围、recap、远端文件、active/enabled 与 HTTP。

> 请先独立完成。参考解答从下一页开始。

</section>

<section class="classic-task solution-page" id="RHCE-PLAYBOOK-C01-SOLUTION" data-kind="classic-task-solution">

## <span class="topic-label">[参考解答]</span> 用三个专用模块表达终态

### ① [操作点] 使用 `ansible.builtin.dnf`、`copy`、`service` 分别表达包、文件和服务。
### ② [验证点] syntax-check、list-hosts 后 limit 执行；远端检查 rpm、stat、systemctl 与 curl。
### ③ [验证点] 全组执行后第二次运行，逐项解释 changed；最终再次 HTTP 验收。

**[Cheatsheet]** 专用模块 → 静态边界 → 小范围 → 远端终态 → 全量 → 第二次执行。

</section>

<section class="topic closing" id="RHCE-PLAYBOOK-CLOSE" data-kind="chapter-closing">

## <span class="topic-label">[本章收束]</span> 执行成功必须落到远端目标状态

YAML 和模块把意图结构化，但只有目标主机范围正确、模块字段有效、远端对象符合要求且重复执行稳定，Playbook 才真正完成。

</section>
