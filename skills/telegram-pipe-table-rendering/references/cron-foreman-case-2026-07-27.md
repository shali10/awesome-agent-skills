# 实测验证记录（2026-07-27 工头日报 cron）

## 问题现象

1. 工头日报 cron（27d0a6e112bb）脚本输出正确的 pipe table 格式
2. 本地 `cat /root/.hermes/cron/output/27d0a6e112bb/2026-07-26_20-00-48.md` 验证：`## 标题` + `|---|---|` 齐全
3. Telegram 端收到的是 `**粗体** + • 数值: xxx` 的 bullet 列表

## 排查路径

1. **查本地输出**：格式正确 → 排除脚本问题
2. **查投递链路**：`_send_to_platform()` → `_send_telegram()` → `format_message()` → `_wrap_markdown_tables()` → `convert_table_to_bullets()`
3. **查历史**：旧主机 7/24 的 cron output `.md` 文件也是 pipe table，投递后同样是 bullet
4. **结论**：路径本身不支持，与服务器无关

## 修复验证

### 脚本格式修正（阻断因素）

去掉 `## 标题` 后多余空行 + 去掉表格内反引号，避免次要问题叠加。

### 切 LLM 模式（方案 B）

```python
cronjob(action='update', job_id='27d0a6e112bb',
    no_agent=False,
    prompt='运行 `python3 /root/.hermes/scripts/foreman_report.py`，将脚本 stdout 作为你的完整回复直接输出...',
    script='',
)
```

触发后 Telegram 表格渲染正常。

## 关键代码位置

| 文件 | 行号 | 作用 |
|---|---|---|
| `tools/send_message_tool.py` | ~1110 | `_send_telegram()` 入口 |
| `plugins/platforms/telegram/adapter.py` | ~7097 | `format_message()` 转 MarkdownV2 |
| `plugins/platforms/telegram/adapter.py` | ~7123 | `_wrap_markdown_tables()` 调 convert |
| `gateway/platforms/helpers.py` | ~376 | `convert_table_to_bullets()` 重写为 bullet |

## 反直觉事实

- Telegram MarkdownV2 **不支持表格语法**，`|` 只是普通字符
- Gateway live adapter 有 `sendRichMessage` 走 Bot API 10.1 原生渲染，支持表格
- 但 standalone `_send_telegram()` 没有 rich 入口，永远走 MarkdownV2 → 永远不支持
