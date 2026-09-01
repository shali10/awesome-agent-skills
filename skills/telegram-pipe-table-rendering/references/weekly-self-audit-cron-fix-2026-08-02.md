# weekly-self-audit cron 修复实录（2026-08-02，最终版）

## 背景

`weekly_self_audit.py` cron（job bf109a24df98，每周日 20:00）连续失败，用户收到投递错误通知；修复后又发现投递表格退化为 bullet + 版本显示 v8 而非 v10。三个独立问题叠加。

## 问题 1：Python 3.11 f-string 语法错误（SyntaxError）

**报错**：`SyntaxError: f-string expression part cannot include a backslash / cannot include a double quote`

**根因**：Python 3.11 的 f-string 表达式内**不允许反斜杠和同类型引号**（3.12 的 PEP 701 才放开）。脚本第 169/171 行：

```python
# ❌ 错（Py3.11 报 SyntaxError）
print(f"""...{'  \n'.join(actions) if actions else '无'}...""")
print(f"""...{run_cmd("date '+%Y%m%d-%H%M'")}.md""")
```

**修法**：提前取值，f-string 里只放变量名：

```python
report_ts = run_cmd("date '+%Y%m%d-%H%M'")
action_line = '  \n'.join(actions) if actions else '无'
print(f"""...{action_line}...""")
print(f"""...{report_ts}.md""")
```

**验证**：`python3 -m py_compile weekly_self_audit.py` 通过 + 实弹运行 RC=0。

⚠️ 注意脚本本身跑得慢（串行跑 zeroops_v8_snapshot.py + foreman_8d_score.py + 查 state.db），直接前台跑会超时，用 `timeout 300 python3 ... > /tmp/out 2>&1` 后台跑。

## 问题 2：cron 投递表格退化 —— B 方案证伪，D 方案落地

修复语法后手动 run 成功，但用户收到的周报是 **bullet 组**（`Gateway • 当前值: RSS 313MB`），不是表格。这是 cron 投递路径（`_send_telegram()` → MarkdownV2 无表格 → convert_table_to_bullets）的**必然行为**，与脚本内容无关。

**B 方案（LLM 模式）实测证伪**：切 no_agent=False + 防代码块 prompt 后，`cron/output/bf109a24df98/<ts>.md` 里 LLM 的 Response 是**标准 pipe table**，但用户端**仍是 bullet**。投递层无论 LLM 还是 no_agent 都走同一 `_send_telegram()` → 照样转 bullet。**cron output 文件有表格 ≠ 用户收到表格，必须以 Telegram 端实际显示为准。**

**最终采用 D 方案**：no_agent 脚本直连 TG sendRichMessage（模式同 `daily_briefing_v2.sh`），cron 恢复 no_agent=True + script=wrapper：

```bash
# weekly_self_audit_v2.sh（新增，chmod +x）
#!/usr/bin/env bash
set -euo pipefail
HERMES_HOME="${HOME}/.hermes"
PY_SCRIPT="${HERMES_HOME}/scripts/weekly_self_audit.py"
TMPFILE="$(mktemp)"
trap 'rm -f "${TMPFILE}"' EXIT
python3 "${PY_SCRIPT}" >"${TMPFILE}"
# 2. 表格完整性验证（≥2 张表、pipe 行数）
# 3. python3 - <<'PY'：POST https://api.telegram.org/bot<TOKEN>/sendRichMessage
#    payload={'chat_id': chat_id, 'rich_message': {'markdown': content}}
#    token/chat_id 从 ~/.hermes/.env 读（TELEGRAM_BOT_TOKEN / TELEGRAM_HOME_CHANNEL）
cat "${TMPFILE}"   # stdout 供 cron 投递 → QQ
```

```python
cronjob(action='update', job_id='bf109a24df98',
    no_agent=True,
    script='weekly_self_audit_v2.sh',   # wrapper 纯文件名
    prompt='',                           # 清空，避免残留 prompt 走 LLM
    enabled_toolsets=['terminal'],
)
```

**验证**：`cronjob action='run'` → cron output 出现 `✅ Telegram: sent via sendRichMessage` + last_status=ok → 用户端确认表格。

## 问题 3：v8 → v10 版本残留

`weekly_self_audit.py` 原写死 v8，系统已升 v10：
- `A = B / 'audits/zeroops-v8'` → `'audits/zeroops-v10'`
- `prev_reports = A.glob('self-audit-v8-*.md')` → `'self-audit-v10-*.md'`
- 标题 `**Hermes 健康周报** · v8 Zero-Ops` → `· v10 Zero-Ops`
- 报告路径 `self-audit-v8-{ts}.md` → `self-audit-v10-{ts}.md`

**教训**：大版本升级后，cron 脚本里硬编码的版本字符串/归档目录不会自动跟随，必须主动 grep 检查（`grep -n 'v8\|zeroops-v8' scripts/*.py`）。

## 时间线（供复现）

1. 20:00 cron 报 SyntaxError（f-string）→ 修两个表达式 → 实跑 OK（核心 98.58 S）
2. 手动 run → 用户收到 bullet 版 → 推荐 B 方案 → 用户「B，token 不是问题」
3. 切 B → run → cron output 有 pipe table 但用户仍收到 bullet → **B 证伪**
4. 改 D（v2 wrapper 直连 sendRichMessage）+ v8→v10 升级 → run → `✅ Telegram: sent via sendRichMessage`
5. 用户确认表格正常

## 经验

1. **Py3.11 f-string 双坑**：表达式内不能有 `\n` 这类反斜杠、不能嵌套同引号函数调用。写多行 f-string 报告时提前把所有表达式算成变量。
2. **cron 表格必然退化（无论 no_agent 还是 LLM 模式）**：修好脚本 ≠ 用户看到表格，投递路径决定渲染。cron output 文件有 pipe table ≠ 用户收到表格，**以 Telegram 端实际显示为准**。
3. **保表格只有 D 方案**（脚本直连 sendRichMessage）；B 方案（LLM 模式）是无效试错，用户说"token 不是问题"时直接上 D，别再走 B。
4. **手动 run 是 cron 修复的标准验证手段**：`cronjob action='run'` 返回 executed=true + last_status=ok 才算闭环，且必须让用户确认实际收到的格式。
5. **版本残留**：升级后 grep cron 脚本里的旧版本字符串/归档路径。

## 关联

- `telegram-pipe-table-rendering` 主 SKILL.md —— 4 方案对比 + B 证伪 + 用户偏好（表格优先、token 不是问题）
- `hermes-cron-lessons` 坑 ⑰ —— no_agent 表格支持描述有误（声称支持，实测不支持）
- `daily_briefing_v2.sh` —— D 方案最早落地模板（2026-07-27）
