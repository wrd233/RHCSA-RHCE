# PDF 大字号阅读版排版规范

## 唯一视觉参考

正式参考为根目录输入包 `RHCSA-01-shell-parsing-expansion-v5.1-final.zip` 内的 `RHCSA-01-shell-parsing-expansion/lecture-review.pdf`，SHA-256 为 `610162e211a9a9e61fcfb404b8ed80f0511117362fed04be6f1107fe7fd1fc29`。该摘要同时写入输入清单和自动测试；不得引用个人目录或其他样章。

## 内容与组件合同

渲染器只读取源 Markdown 已明确表达的语义，不通过自然语言模式猜概念、拆句或创造参数。历史冻结稿 class 只能通过有限 alias map 迁移到 canonical 组件：`chapter-cover`、`reading-navigation`、`concept-block`、`concept-term`、`concept-explanation`、`operation-quickref`、`quickref-command`、`quickref-synopsis`、`option-list`、`knowledge-topic`、`operation-topic`、`diagnosis-topic`、`atomic-point`、`classic-task`、`reference-solution`、`chapter-closing`、`decision-table`、`page-break`。

概念必须全宽单列，名称蓝色加粗，作者解释保持为自然完整段落；页面不显示机械式的两段标签。操作速查使用独立浅绿色区域，每个关键命令具有独立 SYNOPSIS 代码框，重要参数或形式使用纵向 `dl/dt/dd`；只渲染作者显式写出的命令、形式和解释。

正文保留知识、操作、查询、验证、边界和诊断的自然教学叙事。经典任务与参考答案分别从新页开始。A4 正文为 9.8--10.5 pt、行高 1.58--1.68，代码 8.3--8.8 pt，表格不低于 8.2 pt。命令、选项、路径、unit、FQCN、SELinux 类型、变量名和配置键不得内部断词。页面不显示运行页眉、页脚、页码、commit、Source、status 或 Chapter ID。

## 构建与视觉回归

正式流程先分别生成并验收 33 个单章 PDF，再生成封面/目录前置 PDF，最后按 `config/chapters.yml` 顺序原样合并单章。禁止把 33 章重新拼成巨大 HTML 二次排版。整书页数必须等于单章页数之和加前置页数。

视觉回归逐章比较单章与整书对应页的 media box 和解码后 PDF content stream，并抽取封面、导航、概念、速查、高密度代码/表格、任务、答案和末页制作 contact sheet。二进制 PDF、PNG 和 contact sheet 只保留在忽略目录；结构化 QA 与结论进入 `reports/`。
