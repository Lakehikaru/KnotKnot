# file-to-markdown

将文件（PDF、XLSX、DOCX、图片等）通过 markdown.new API 转换为 Markdown 格式。自动处理超过 10MB 的大文件拆分。

## When to Use
- 用户要求将 PDF、Word、Excel 或图片文件转换为 Markdown
- 用户提到 markdown.new 或文件转 md
- 需要从非文本文件中提取内容为 Markdown 格式

## 使用流程

1. 确认输入文件路径存在
2. 调用转换脚本：
   ```bash
   python .claude/scripts/file2md.py "<input_file>" --output "<output.md>"
   ```
3. 检查输出文件内容是否完整

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `input_file` | 是 | 输入文件路径（支持多个），PDF/XLSX/DOCX/图片等 |
| `--output` | 否 | 输出 md 文件路径，默认与输入同名 .md（仅单文件时有效） |
| `--api-key` | 否 | markdown.new API key，也可通过环境变量 `MARKDOWN_NEW_API_KEY` 设置 |

## 支持的大文件拆分

- PDF（> 10MB）：自动按页拆分为多个子 PDF，逐片转换后合并
- XLSX（> 10MB）：按 sheet 拆分为多个子文件，逐片转换后合并
- DOCX（> 10MB）：按段落拆分为多个子文件，逐片转换后合并
- 其他格式超 10MB：提示用户手动拆分

## 注意事项

- API 单次上传限制 10MB
- 无需 API key，每天每 IP 500 次免费调用
- 需要网络连接访问 markdown.new API
