# sendRichMessage Cron 实现参考（2026-07-27）

## 背景

Hermes cron 投递路径（no_agent 和 LLM 模式均）走 `format_message()` → pipe table 转为 bullet 列表。gateway 实时对话路径走 `sendRichMessage` → raw markdown 中 pipe table 原生渲染。

**根本矛盾**：cron 自动投递无法用 `sendRichMessage`，因为 `_send_telegram()` 硬编码使用 `sendMessage` + MarkdownV2，且 `format_message()` 调用 `convert_table_to_bullets()` 转换表格。

## 方案

no_agent 脚本直连 Telegram Bot API 的 `sendRichMessage` 端点，绕过 Hermes 投递链路。

## 实战代码：每日早报 v2

位置：`~/.hermes/scripts/daily_briefing_v2.sh`

```bash
#!/usr/bin/env bash
# 每日早报 v2：通过 Telegram Bot API sendRichMessage 直发（表格原生渲染）
set -euo pipefail

HERMES_HOME="${HOME}/.hermes"
PY_SCRIPT="${HERMES_HOME}/scripts/daily_briefing_pipe.py"
TMPFILE="$(mktemp)"
trap 'rm -f "${TMPFILE}"' EXIT

# 1. 生成简报内容
python3 "${PY_SCRIPT}" >"${TMPFILE}"

# 2. 验证表格完整性（4 张表必须存在且格式正确）
python3 - "${TMPFILE}" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read().strip()
required = [
    ("今日要闻", 3), ("成都天气", 2),
    ("GitHub 日榜 Top 10", 4), ("GitHub 周榜 Top 10", 4),
]
for heading, columns in required:
    m = re.search(rf"## .*?{re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    if not m:
        raise SystemExit(f"missing table section: {heading}")
    rows = [x for x in m.group(1).splitlines() if x.strip().startswith("|")]
    if len(rows) < 3:
        raise SystemExit(f"incomplete table: {heading}")
    for row in rows:
        if row.count("|") != columns + 1:
            raise SystemExit(f"column mismatch in {heading}: {row[:100]}")
assert text.count("|---") >= 4, "missing pipe-table separator rows"
PY

# 3. 发送到 Telegram（sendRichMessage 支持原生表格渲染）
python3 -c "
import json, os, urllib.request

# 从 .env 读取凭据
env_path = os.path.expanduser('~/.hermes/.env')
token = None
chat_id = '1658239957'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            token = line.split('=', 1)[1].strip().strip(\"'\\\"\")
        elif line.startswith('TELEGRAM_HOME_CHANNEL='):
            chat_id = line.split('=', 1)[1].strip().strip(\"'\\\"\")

with open('${TMPFILE}', encoding='utf-8') as f:
    content = f.read()

# sendRichMessage API
payload = json.dumps({
    'chat_id': chat_id,
    'rich_message': {'markdown': content}
}).encode()
req = urllib.request.Request(
    f'https://api.telegram.org/bot{token}/sendRichMessage',
    data=payload,
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=30)
result = json.loads(resp.read())
assert result.get('ok'), f'Telegram API error: {result}'
print('✅ Telegram: sent via sendRichMessage')
"

# 4. 输出到 stdout（供 cron delivery → QQ bot）
cat "${TMPFILE}"
```

## Cron Job 配置

```json
{
  "name": "每日早报",
  "no_agent": true,
  "script": "daily_briefing_v2.sh",
  "deliver": "qqbot",          // 只送 QQ，TG 由脚本直发
  "schedule": "0 8 * * *",
  "enabled_toolsets": ["terminal"]
}
```

## 关键细节

| 要素 | 说明 |
|------|------|
| API 端点 | `POST https://api.telegram.org/bot<TOKEN>/sendRichMessage` |
| 请求体 | `{'chat_id': str, 'rich_message': {'markdown': str}}` |
| Token 来源 | `~/.hermes/.env` → `TELEGRAM_BOT_TOKEN=` |
| Chat ID | `~/.hermes/.env` → `TELEGRAM_HOME_CHANNEL=` |
| 输入内容 | 纯 Markdown（需含 pipe table 分隔行 `|---|---|`） |
| 输出 | raw markdown 在 Telegram 中渲染为原生表格 |
| QQ 投递 | 脚本末尾 `cat` stdout → cron no_agent 送到 QQ |
| 生产适用 | ✅ 不改 Hermes 代码，token 从 .env 读取，脚本无硬编码凭据 |

## 验证方法

```bash
# 1. 手动跑
bash ~/.hermes/scripts/daily_briefing_v2.sh
# 输出：✅ Telegram: sent via sendRichMessage + 内容

# 2. 检查 cron 执行
cronjob(action='run', job_id='xxx')

# 3. 看 Telegram 是否出现表格（不是 bullet 列表 + 不是源码）
```

## 适用场景

- 必须表格渲染的 cron 投递（日报/周报/报告类）
- 用户明确要求「不要纯文本，要 markdown 表格」
- 不需要 LLM 推理的自动化报告
- 需要 TG+QQ 双推（脚本负责 TG，cron 负责 QQ）

## 注意事项

- `sendRichMessage` 是 Telegram Bot API 10.1+ 方法，旧版 Bot API 可能不支持（返回 404 → `_is_rich_capability_error` 触发回退）
- 中文内容在 `sendRichMessage` 中正常渲染，不需要特殊配置
- 链接预览：如需禁用，给 `/sendRichMessage` 加 `link_preview_options: {"is_disabled": true}` 参数
- 回复锚点：如需回复某条消息，加 `reply_parameters: {"message_id": id}`
