# PDF 大字号阅读版排版规范

正式讲义使用 `reading` profile：A4 纵向、20 mm 左右页边距、10.2 pt 正文、1.64 行高、8.5 pt 代码和表格。可见页面不出现页眉、页脚、页码、构建时间、commit、状态、Chapter ID、slug、Source 或稳定 ID；维护信息只进入源 frontmatter、PDF metadata、manifest 和报告。

概念以 `.concept-block` 全宽单列显示，`.concept-term` 加粗并使用深蓝强调色。作者已有的第一句为“定义”，后续句为“理解”；构建器只做确定性重排，绝不补写技术内容。缺少后续解释的概念由 QA 报告列出。

专题和原子节点保留 Markdown 的语义标签，输出时转为 `.semantic-badge`。操作摘要使用 `.operation-block`；重要参数应在源中逐项书写，HTML 使用定义列表 `.option-list`，不得复制完整 man page。经典任务 `.task-page` 与参考解答 `.solution-page` 必须另起页。

代码和内联标识符禁用 hyphenation；短内联代码不换行，长命令进入代码块。表格不得低于 8.1 pt，长表重复表头，过宽内容改为纵向结构。目录只列章并可点击；PDF 书签保留章和专题层级。

正式构建产物位于 `dist/rhcsa/reading/`，二进制不提交 Git。紧凑样式保留为兼容 profile，但不是正式默认。

