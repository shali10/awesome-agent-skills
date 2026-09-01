---
name: telegram-pipe-table-rendering
description: "Telegram 通过 Hermes 投递时 GFM pipe table 渲染的真伪判定。覆盖 gateway live adapter（支持原生表格）vs standalone cron 投递路径（100% 退化为 bullet）的差异，含 no_agent cron 表格修复 4 方案（A 改 bullet / B 切 LLM 模式 / C 打 sendRichMessage 补丁 / D 直连 Bot API），以及 QQ Bot API msg_type:2 实现、标题后多余空行、表格内反引号三个附加格式陷阱。新增 D 方案实现参考见 references/send-rich-message-cron-implementation-2026-07-27.md，QQ 实现见 references/qq-markdown-msg-type-2-2026-07-27.md。"
version: 1.0.0
author: hermes-agent
license: MIT
platforms: [linux, macos, windows]
tags: [telegram, markdown, pipe-table, cron, no_agent, formatting, rich_message]
triggers: [telegram 表格, pipe table 不渲染, pipe table 退化, cron 表格, no_agent 表格, 管道表格, markdown table telegram, sendRichMessage]
updated: 2026-07-27
---

# Telegram Pipe Table 渲染真相（2026-07-27 实测）

## 核心结论

**no_agent cron 走 `_send_telegram()` 路径时，GFM pipe table 100% 退化为 bullet 列表，无一例外。**

旧主机 时代也不存在"表格正常渲染"——查 cron output 原始 `.md` 文件，pipe table 格式正确，但投递后同样退化为 bullet。两台服务器走同一段代码，没有区别。

## 根因链路

```
cron job (no_agent=True)
  → _send_to_platform()              [tools/send_message_tool.py]
  → _send_telegram()                 [tools/send_message_tool.py]
  → TelegramAdapter.format_message() [plugins/platforms/telegram/adapter.py]
  → _wrap_markdown_tables()          [同上]
  → convert_table_to_bullets()       [gateway/platforms/helpers.py]
  → |表格| → **粗体** + • bullet 组
```

### 关键机制

1. `_send_telegram()` 是独立发送路径，**不支持 rich_message**（Bot API 10.1 原生表格）
2. `format_message()` 把 Markdown 转成 Telegram MarkdownV2
3. MarkdownV2 **没有表格语法**——`|` 只是普通字符
4. `_wrap_markdown_tables()` 检测到 pipe table → 调 `convert_table_to_bullets()` 重写

### 对比：Gateway 完整路径（支持表格）

```
用户消息 → gateway live adapter → _should_attempt_rich() → sendRichMessage
→ Bot API 10.1 原生渲染 → 表格正常显示
```

⚠️ **v0.19.1+ 例外：含中文的内容会被 CJK guard 拦截降级成 bullet（2026-08-02 实测）**，即使 config 有 `rich_messages: true` + `allow_cjk_rich: true` 也没用（新版代码不读该配置）。旧版（v0.19.0 及之前）无此拦截，所以「迁移前表格正常、迁移后突然退化」。详见下方「v0.19.1+ CJK rich guard」一节。

## 4 种修复方案（实测对比）

| 方案 | 操作 | 代价 | 效果 |
|---|---|---|---|
| A | 脚本改 bullet 输出 | 零成本 | 没表格，信息清晰 |
| B | cron 切 LLM 模式（`no_agent=False` + prompt 让 LLM 跑脚本并原样输出） | 每天 ~50 token | **实测不保表格（2026-08-02 证伪）**——LLM 输出标准 pipe table，投递仍转 bullet |
| C | 改 `_send_to_platform`/`_send_telegram` 加 `sendRichMessage` 分支 | 改库代码，pip 升级会丢 | 根治（代码见 `references/cron-standalone-telegram-pipe-table-fix.md`） |
| **D（唯一保表格·生产稳定）** | no_agent 脚本直连 TG sendRichMessage + QQ msg_type:2 | 零 token，不改代码 | **双平台原生表格** |

### ⚠️ B 方案（LLM 模式）实测证伪：投递路径仍转 bullet（2026-08-02）

**B 方案不保表格。** 实测 weekly-self-audit cron（bf109a24df98）切 LLM 模式后：
1. cron output 文件（`cron/output/<job>/<ts>.md`）里 LLM 的 Response 是**标准 pipe table**（`| 项目 | 当前值 | 备注 |`，表头/分隔/数据齐全）
2. 但投递到 Telegram 后**仍是 bullet 组**（`• 当前值: ...`）

**根因**：cron 投递（无论 no_agent 还是 LLM 模式）最终都走 `_send_telegram()` → `format_message()` → `convert_table_to_bullets()`。LLM 输出内容再标准，投递层照样转换。**唯一绕过点 = 脚本直连 Bot API（D 方案）**，让表格在 Telegram 端原生渲染，完全不经过 Hermes 的 cron 投递路径。

**判定标准（修正）**：cron output 文件含 pipe table ≠ 用户收到表格。**以 Telegram 端实际显示为准**——手动 `cronjob action='run'` 后让用户看真实消息，不要只看 output 文件。

### D 方案详解：直连 Bot API（TG sendRichMessage + QQ msg_type:2，2026-07-27 首次实用化）

**原理**：Telegram Bot API 10.1+ 提供 `sendRichMessage` 端点，接受原始 Markdown 并原生渲染 pipe table。Hermes 的 `_send_telegram`/`format_message` 路径使用 `sendMessage` + MarkdownV2，表格被 `convert_table_to_bullets()` 转为 bullet。直接调用 `sendRichMessage` 完全绕过此转换。

```python
payload = {
    'chat_id': chat_id,
    'rich_message': {'markdown': content}  # RAW markdown, not MarkdownV2
}
# POST https://api.telegram.org/bot<TOKEN>/sendRichMessage
```

**与其他方案的对比**：

| 维度 | B (LLM 模式) | D (直连 API) |
|------|-------------|-------------|
| 投递路径 | Hermes cron → `format_message()` → Telegram | 脚本 → Telegram Bot API → Telegram |
| LLM token 消耗 | ~50/次 | 0 |
| 代码侵入 | 无 | 无 |
| 稳定性 | LLM 可能包裹代码块 | 脚本完全可控 |
| QQ 投递 | cron delivery 自动 | 脚本 stdout → cron no_agent 送 QQ |

**生产化部署步骤**：
1. 新建 wrapper 脚本（no_agent）：生成内容 → 表格验证 → sendRichMessage → stdout 输出给 QQ
2. cron job：no_agent=true，deliver 只留 qqbot，Telegram 由脚本直发
3. Token 从 ~/.hermes/.env 读取，不硬编码
4. 验证即 bash wrapper.sh 看 exit code + Telegram 端是否出现表格

**⚠️ D 方案双重投递坑（2026-08-02 实测，weekly_self_audit_v2.sh 首跑翻车）**：

wrapper 脚本 sendRichMessage 直发 TG 后，**末尾 `cat` 又把内容吐到 stdout**；如果 cron `deliver` 仍保留 origin/telegram，cron 会把 stdout **再往 TG 投递一遍** → 用户收到两条：一条原生表格（直发）+ 一条 bullet 版（cron 重复投递，且带 `✅ Telegram: sent via sendRichMessage` 前缀噪音）。

**修法（两处一起改）**：
1. **cron deliver 只留 `qqbot`**（或 `local`）——TG 只收脚本直发那条，cron 不再重复投 TG
2. **发送确认行走 stderr**：`print('✅ Telegram: sent via sendRichMessage', file=sys.stderr)` —— 不能进 stdout，否则混入 QQ 投递内容/污染输出

**验收**：`bash wrapper.sh` 后 stdout 应只有报告正文（无 ✅ 行）、stderr 有确认行；`cronjob action='run'` 后用户 TG 只收到一条表格。

**参考实现**：`references/send-rich-message-cron-implementation-2026-07-27.md`

### D 方案变体：内容需 LLM 推理/web 搜索时（wrapper 内嵌 hermes chat，2026-08-03 实战）

**场景**：报告内容不是纯脚本能生成的——需要 LLM 搜索网络/推理（如 VPS 优惠监控、行业周报）。不能直接套"脚本生成内容"的 D 方案，也不能退回 LLM 模式 cron。

**正确做法**：no_agent wrapper 脚本**内部调用 `hermes chat` CLI 生成内容**，再 sendRichMessage 直发：

```bash
# ~/.hermes/scripts/xxx.sh（节选）
# 1. hermes CLI 生成正文（-Q 模式 stdout 干净只有正文；stderr 是 session 信息，丢弃）
cd /usr/local/lib/hermes-agent-next
timeout 420 ./venv/bin/hermes chat \
  -q '<完整任务 prompt，含显式 pipe table 模板>' \
  --reasoning medium -t web -Q --max-turns 10 --ignore-rules > "${TMPFILE}" 2>/dev/null \
  || { echo "❌ LLM 生成失败"; exit 1; }

# 2. 校验表格（见下）→ 3. sendRichMessage 直发 TG（同每日早报脚本）→ 4. cat 输出给 QQ
```

cron 配置：`no_agent=True` + `script=xxx.sh` + **`deliver=local`**（脚本已直发 TG，deliver 留 origin 会双重投递——TG 收到表格 + bullet 两条）。

**🚨 决策纪律（本次翻车复盘）**：**LLM 模式 cron 用户反馈"格式不对"时，不要先改 prompt 试错**——投递层 `convert_table_to_bullets()` 强制转换，prompt 再硬也没用（本次 VPS优惠监控改了两轮 prompt 均失败）。直接判断：内容是 LLM 生成的报告且要表格 → 一步到位改 D 变体（wrapper 内嵌 hermes chat）。改完 `cronjob action='run'` 后看**用户端真实消息**（表格 or bullet），不要只看 output 文件。

**校验脚本陷阱**：分隔行 `|---|------|` 也以 `|` 开头、也含 `|---`，若把"含 --- 的行"当压缩行会误杀合法表格。正确逻辑：先按 `startswith("|---")` 识别分隔行，数据行 = 以 `|` 开头且非分隔行；只在**数据行**里检查 "|---"（表头+分隔+数据揉一行的压缩行特征）。

**参考实现**：`~/.hermes/scripts/vps_discount_monitor.sh`（VPS优惠监控，2026-08-03 实现并验证表格成功；⚠️ 该 cron 与脚本已于 2026-08-03 当天按用户要求「删除干净」——文件已不存在。可复用的不是这个脚本，而是上面的 wrapper 模式：no_agent + hermes chat 生成 + 校验 + sendRichMessage + deliver=local）。

**⚠️ 该 cron 曾因清理数据源被连带误删**（8/1 删 czl 时删掉，8/3 用户发现周一没推送）：误删后恢复完整定义（prompt/schedule）的唯一来源是 curator 备份 `~/.hermes/skills/.curator_backups/*/cron-jobs.json`，executions.db 只有 job_id 级记录没有 prompt。排查「cron 怎么没了」与预防纪律见 `references/cron-recovery-curator-backup-2026-08-03.md`。

### QQ `msg_type:2` 实现（2026-07-27 新增）

**QQ Bot API 支持 Markdown pipe table 原生渲染（`msg_type: 2`），但 Hermes 的 `send_message_tool` 使用 `msg_type: 0`（纯文本），导致 cron 投递到 QQ 时显示原始 Markdown 源码。**

**修复**：no_agent 脚本直连 QQ Bot API 的 `msg_type: 2` 端点，绕过 Hermes 的 `_send_qqbot` 路径。

```python
# QQ Bot API 获取 Token
token_resp = requests.post(
    'https://bots.qq.com/app/getAppAccessToken',
    json={'appId': appid, 'clientSecret': secret}
)
access_token = token_resp.json()['access_token']

# 发送 Markdown 消息（msg_type: 2）
payload = {
    'msg_type': 2,
    'markdown': {'content': raw_markdown_content}  # RAW markdown
}
headers = {
    'Authorization': f'QQBot {access_token}',
    'Content-Type': 'application/json'
}
# 尝试 group → C2C 端点
for endpoint in ['v2/groups/{id}/messages', 'v2/users/{id}/messages']:
    resp = requests.post(f'https://api.sgroup.qq.com/{endpoint}', ...)
```

**凭据来源**：`~/.hermes/.env` → `QQ_APP_ID=` 和 `QQ_CLIENT_SECRET=`；`QQBOT_HOME_CHANNEL=` 为 Chat/Group ID。

**组合方案（推荐）**：同一 no_agent 脚本同时处理 TG（sendRichMessage）和 QQ（msg_type:2），cron deliver 设为 `local`（双平台均由脚本直发）。此时脚本须读取 TG token（TELEGRAM_BOT_TOKEN）和 QQ 凭据（QQ_APP_ID + QQ_CLIENT_SECRET），分别调用对应 API。

| 平台 | API 端点 | 请求体 |
|------|---------|--------|
| TG | `POST /bot<TOKEN>/sendRichMessage` | `{'chat_id': ..., 'rich_message': {'markdown': content}}` |
| QQ | `POST /v2/groups/{id}/messages` | `{'msg_type': 2, 'markdown': {'content': content}}` |
| QQ 认证 | `POST /app/getAppAccessToken` | `{'appId': ..., 'clientSecret': ...}` → `Authorization: QQBot <token>` |

**🚨 用户说「TG 正常，QQ 是乱的」→ 先查 cron 是否刚从 agent 模式切到 no_agent（2026-08-03 工头日报实测）**

**症状**：同一份工头日报，TG 端表格正常、QQ 端打散成乱格式；用户反馈「现在的 tg 正常，QQ 是乱的，之前的 QQ 正常」。

**根因**：投递模式变了，不是 QQ 平台坏了。之前 cron 是 **agent 模式**（LLM 输出走 Hermes markdown 投递路径，QQ 端 msg_type 正常渲染）；升级成 **no_agent 后**，stdout 投递走纯文本路径，QQ 端 pipe table 不渲染。TG 正常是因为脚本已改 D 方案直发 sendRichMessage，而 QQ 还挂在 cron stdout 投递上。

**修复（对齐 daily_briefing_v2.sh 成熟方案）**：
1. 投递脚本里 QQ 也直发：Bot API `msg_type:2` markdown（group 端点失败回退 C2C `v2/users/{id}/messages`）
2. cron `deliver` 改 `local`——脚本自己双平台直发，**不让 cron stdout 再投递 QQ**（否则 QQ 收两份：乱格式 stdout + 正常直发）
3. 验证：`bash script.sh` 后 stderr 出现 `✅ QQ group/C2C: sent` + `✅ Telegram: sent` = 修对；让用户看真实 QQ 端消息确认

**排查优先级（用户说 QQ 乱时）**：
| 步骤 | 检查项 |
|---|---|
| ① | cron 当前是 no_agent 还是 agent 模式？（jobs.json `no_agent` 字段；output 文件有 `## Prompt` + `## Script Output` 结构 = agent 模式，只有脚本正文 = no_agent） |
| ② | QQ 走 cron stdout 投递还是脚本直发？（投递脚本里有没有 QQ Bot API 调用段） |
| ③ | 命中 → 脚本补 QQ 直发段 + deliver 改 local |

### B 方案 LLM 代码块陷阱

B 方案（LLM 模式）中，LLM 常把脚本输出包裹在三反引号中，导致 Telegram 显示源码而非渲染结果。**根因：** prompt 仅写「请把它原样输出，不要修改任何格式」——LLM 理解「原样」= 放在代码块里保护格式。

**修法**：prompt 必须**显式禁止代码块**：
```python
prompt='...保留完整的 Markdown 结构... **非常重要：不要用 ``` 代码块包裹输出内容！直接输出纯 Markdown 文本。**'
```

**验证**：查看 cron output 文件中 agent 的 Response 部分 — 被 ``` 包围 = 命中此坑。

### A/B/C 方案实测历史

工头日报 cron（27d0a6e112bb）在 2026-07-26 到 2026-07-27 期间经历了 no_agent → LLM → no_agent 的三轮切换，最终确认：
- 用户要求「不要纯文本，要 markdown 表格」→ A 方案被用户否决
- B 方案（LLM 模式）出代码块陷阱 → prompt 加禁止代码块后修复
- 最终采用 D 方案（直连 sendRichMessage）：每日早报用此方案，工头日报维持 no_agent bullet（用户接受）

```python
# prompt 示例（B 方案 + 防代码块）
cronjob(action='update', job_id='xxx',
    no_agent=False,
    prompt='运行 `python3 /root/.hermes/scripts/foreman_report.py`，将脚本 stdout 作为你的完整回复直接输出，不做任何修改、摘要或额外说明。保留所有 ## 标题和 | 管道表格 | 的原始格式。**非常重要：不要用代码块包裹输出内容。**',
    script='',  # 清掉旧 script
)
```

## 额外格式陷阱

### ① `## 标题` 后多余空行导致表格脱离上下文

```
## 📊 今日 token 诊断
                  ← 这个多余空行让 Telegram 把后面表格当新段落
| 指标 | 数值 |
```

**修法**：`"\n## 标题\n"` 改 `"\n## 标题"`（依赖 join 自然补一个换行）

### ② 表格内反引号导致整表崩溃

```python
# ❌ 反引号在表格单元格内 → 整表渲染失败
out.append(f"| 输入 / 输出 / 缓存读 | `{fmt_n(x)}` / `{fmt_n(y)}` |")

# ✅ 纯文本或粗体替代
out.append(f"| 输入 / 输出 / 缓存读 | {fmt_n(x)} / {fmt_n(y)} |")
out.append(f"| 总 token | **{fmt_n(total)}** |")
```

## 🚨 v0.19.1+ CJK rich guard：gateway live 中文表格也退化成 bullet（2026-08-02 实测）

**症状**：gateway live 会话（非 cron）里发 pipe table，只要含中文，Telegram 端显示成 bullet 组（`• 状态: ✅ ...`），用户质问「你这是什么格式」。config 已有 `platforms.telegram.extra.rich_messages: true` + `allow_cjk_rich: true`，表格仍退化。

**根因**：v0.19.1 的 `plugins/platforms/telegram/adapter.py` 新增 `_has_telegram_desktop_cjk_rich_garble_shape()`（TDesktop #47653 CJK 乱码防护），**无条件拦截所有含 CJK 字符的内容**跳过 rich 渲染，且该 guard **不读取 `allow_cjk_rich` 配置**——配置是旧版语义，新版代码硬编码忽略。旧版（v0.19.0 及之前）无此拦截，所以迁移前表格正常、迁移后突然退化。

**修复**（改 Hermes 源码，需外部重启 Gateway）：
1. `__init__` 加一行读取配置：`self._cjk_rich_allowed: bool = self._coerce_bool_extra("allow_cjk_rich", False)`
2. `_has_telegram_desktop_cjk_rich_garble_shape()` 开头加：`if getattr(self, "_cjk_rich_allowed", False): return False`
3. `python3 -m py_compile` 验证语法 + `cp adapter.py adapter.py.bak-cjkrich-$(date +%s)` 备份
4. 外部 detached 重启 Gateway（见 `hermes-gateway-restart-from-inside` skill）；`systemctl restart` 卡 deactivating = drain 等当前 agent 回合结束，属预期行为

**排查优先级**（用户问「这是什么格式」时先查这个，再查反引号/压缩行/emoji）：
| 步骤 | 检查项 |
|---|---|
| ① | 内容是否含中文 + Gateway ≥ v0.19.1？→ 命中 CJK guard |
| ② | config 是否已有 `allow_cjk_rich: true`？→ 有则按上述 patch 修代码 |
| ③ | 表格行是否独立成行（老规矩） |

详细 patch 与验证见 `references/cjk-rich-guard-patch-2026-08-02.md`。

**发测试表格前先确认 patch 是否已生效（2026-08-03 实测流程）**：
```bash
# ① 代码是否含 patch（期望 2 处 _cjk_rich_allowed）
grep -n "_cjk_rich_allowed" /usr/local/lib/hermes-agent-next/plugins/platforms/telegram/adapter.py
# ② config 是否开启
grep -n "allow_cjk_rich\|rich_messages" ~/.hermes/config.yaml
# ③ Gateway 是否已用新代码重启（启动时间必须晚于 adapter.py 修改时间）
systemctl show hermes-gateway -p ActiveEnterTimestamp
stat -c '%y' /usr/local/lib/hermes-agent-next/plugins/platforms/telegram/adapter.py
```
三项全绿才发测试表格；③ 不满足说明 patch 打了但 gateway 还在跑旧代码，需按 `hermes-gateway-restart-from-inside` 重启。

**✅ 2026-08-03 实测确认**：三项全绿（patch 生效 + config 开启 + gateway 启动晚于 adapter.py 修改时间）后发中文 pipe table，用户实测「表格是正常的，测试通过」。此后 gateway live 中文表格链路视为已验证正常，无需重复怀疑 CJK guard；若用户再说格式不对，优先查表格行压缩/反引号等老规矩，而不是再怀疑 CJK guard。

## 判定标准

- 本地 `cat cron/output/<job_id>/latest.md` 含 pipe table，但 Telegram 显示 bullet → 命中本坑
- 切换到 LLM 模式后表格正常渲染 → 修对本坑

## 🔍 用户反馈表格"乱码"时的排查流程

当用户说「这是什么格式」「乱了」「格式不对」时，**不要切换格式**（pipe table → bullet），而是按顺序排查：

| 步骤 | 检查项 | 修复 |
|------|--------|------|
| ⓪ | 内容含中文 + Gateway ≥ v0.19.1？ | 命中 CJK rich guard，改 adapter 源码（见上节） |
| ① | 表格中是否有反引号 `code`？ | 改用 **粗体** 或去掉反引号 |
| ② | 表头/分隔/数据行是否在同一行？ | 每行独立，不要压缩 |
| ③ | 表格前后是否有空行隔离？ | 前后各加一个空行 |
| ④ | emoji 是否导致列宽度错位？ | 移除或缩短 emoji 内容 |

**关键原则**：用户说格式有问题，是让你**修内容**，不是让你换格式。

**🚨 交互纪律（2026-07-31 实测）：用户问「你这是什么格式」时必须先答格式，不要答非所问**

用户问「你这是什么合适/你这是什么格式」时，指的是**上一条的排版格式**（比如表格渲染挤成一行），不是让你回答业务结论。本会话实例：用户问「你这是什么合适」→ 我理解成"哪个 VPS 合适"回答了一堆选型 → 用户纠正「我说的格式」。正确做法：

1. 先承认问的是格式，直接说明用的什么格式（如"GFM pipe table，每行独立"）
2. 立即自查 + 重新发送一遍确保格式正确
3. 不要展开业务分析，先解决格式问题

## 🚨 代理端格式纪律 —— 不要压缩表格行

**硬规则：每个 `|...|` 行必须独立成行。绝不留空、不压缩、不合并多行为一行。**

### 🚨 嵌套 bullet 渲染错乱（2026-08-02 实测补充）

**症状**：消息里用子项缩进（`- 主项` 下面再缩进 `  - 子项`），Telegram 渲染层级错乱——子项缩进丢失或错位，用户看到"格式错误"。实测：向用户列举"已落盘证据"时用了 3 层嵌套 bullet（`- 今天新坑 1/2/3` 挂在 `- 今天的新坑全记进去了` 下面），用户直接指「刚说完你又出现格式错误」。

**规则**：**Telegram 上禁止嵌套 bullet（多级缩进列表）。** 信息要么全平铺成顶层 bullet（每项 `- ` 开头、不缩进），要么多行多列用 pipe table。

| ❌ 错误做法 | ✅ 正确做法 |
|---|---|
| `- 主项` + 缩进子项 `  - 子项A` / `  - 子项B` | 全部平铺：`- 主项A` / `- 主项B` / `- 主项C`，或用 pipe table |
| 3 层嵌套：`- 主` → `  - 次` → `    - 三` | 拆成独立顶层 bullet，或转表格 |

**发前自检**：消息里有没有缩进超过 0 格的 `- ` 子项？有就平铺或转表格。

| ❌ 错误做法（反复被用户纠正 5+ 次） | ✅ 正确做法 |
|---|---|
| 表头+分隔+数据全在一行 | 表头一行 → 换行 → 分隔一行 → 换行 → 每行数据各一行 |
| 表头行末尾 `|` 后直接跟分隔行 `|---|---|`，未换行 | 表头写完换行，分隔行单独占一行 |
| 用 inline 文本冒充表格（逗号/箭头/冒号分隔） | 保持 pipe table 结构 |

**具体错误示例（2026-07-29 实测）：**
```
| 位置 | 内容 | |:---|---| | 🗑 xxx | 已删 |
```
这是表头 `| 位置 | 内容 |` + 分隔 `|:---|---|` + 首行数据 `| 🗑 xxx | 已删 |` 全部在同一行。必须拆成三行：
```
| 位置 | 内容 |
|:---|---:|
| 🗑 xxx | 已删 |
```

**根因：** 觉得内容少可以「压缩到一行省空间」→ Telegram 渲染失败乱码。**内容多少不是压缩的理由。**

**发前自检清单（加载此 skill 后必须执行）：**
1. 所有 pipe table 的每行是否都独立成行？
2. 分隔行 `|---|---|` 是否在独立行上？
3. 有没有用 inline 文本冒充表格？
4. 简单 key-value（2-4 条）是否用 bullet 列表比表格更清晰？

**🚨 禁止主动降级成 bullet（2026-07-31 用户第三次纠正）**

用户原话：「改用表格就表格，格式一定要对，发给我之前先检查一下」「你又偷懒干什么，不要节约格式呀」。多行多列的结构化对比**必须用 pipe table**，即使只有 3 行 3 列也不能压成 bullet。当天连续 3 次翻车路径：pipe table 揉成一行 → 改用 bullet（被批「格式不对」）→ 再发 pipe table 又揉成一行（被批「不要节约格式」）。正确做法：**一律写独立行的 pipe table，发前逐行检查表头/分隔/数据各自成行**。用户要的是「内容少也用标准表格」，不是「内容少就换 bullet 省事」。

**🚨 2026-08-01 第 4-5 次翻车：压缩表格行是生成时问题，不是发送时问题**

用户连续问「什么格式呀」「你是不是有什么问题，为什么格式一会对一会错」。复盘发现：**时对时错的根因是生成消息时偶尔把表头+分隔+首行数据写在同一行**（压缩省空间），Telegram 端必然揉成一团；写对时（每行独立）就正常渲染。这不是平台不稳定，是生成内容本身违规——**发前自查不能靠感觉，必须逐字检查输出文本**。

**发前必做逐行检查（消息含 pipe table 时强制执行）：**
1. 数一遍表格：表头行、分隔行、每行数据是否**各自独立成行**（每行以 `|` 开头、以 `|` 结尾、行间只有单个换行）
2. 扫描输出里有没有 `| A | B | |---|---|` 这种**表头后紧跟分隔行无换行**的压缩 pattern——出现即违规，必须拆行
3. 分隔行 `|---|---|` 必须独占一行，禁止与表头或数据行同行
4. 简单 key-value（2-4 条）用 bullet，但**多行多列结构化对比必须 pipe table**（即使用户说"格式不对"，也是让你修表格行，不是让你换格式）

## 关联

- `hermes-cron-lessons` 坑 ⑰（**描述有误，声称"支持"——实际不支持**，2026-08-02 weekly_self_audit 周报实测退化 bullet；该 skill 为 user-owned，curator 无法直接修正）
- `hermes-self-audit-v2` Step 5 + 坑位表（**同样声称 "no_agent cron 投递 Telegram 支持管道表格"——2026-08-02 实测证伪，必转 bullet**；该 skill 为 user-owned，curator 无法直接修正。正确做法见本 skill「D 方案」节：wrapper 直连 sendRichMessage + cron deliver=qqbot。若用户触发自审相关流程，先看本 skill 再照做）
- `hermes-cron-setup` 坑 19（建议用代码块包裹——非最佳方案）
- `references/cron-standalone-telegram-pipe-table-fix.md`（方案 C 的代码级修复）
- `references/cjk-rich-guard-patch-2026-08-02.md`（v0.19.1+ CJK guard 源码级修复，gateway live 中文表格退化）
- `references/weekly-self-audit-cron-fix-2026-08-02.md`（B 方案在 weekly-self-audit cron 上的完整闭环：Py3.11 f-string 双坑 + no_agent 退化 + 手动 run 验证）

## 🚨 用户偏好：表格优先，token 不是问题（2026-08-02 实测）

**用户原话**：「B，token 不是问题，别抠抠搜搜」。

weekly-self-audit cron（bf109a24df98）2026-08-02 修复流程验证：no_agent 模式投递周报必然退化为 bullet → 用户要求表格 → 推荐 B 方案（LLM 模式 + 防代码块 prompt）→ 用户**明确否决因 token 成本而选 A/维持 no_agent**。

**但 B 方案实测不保表格**（见上方「B 方案实测证伪」节）：LLM 输出 pipe table 正确，投递仍转 bullet。最终按 D 方案落地：`weekly_self_audit_v2.sh` 直连 sendRichMessage（模式同 `daily_briefing_v2.sh`），cron 切回 `no_agent=True + script=wrapper`，Telegram 由脚本直发、cron 只负责 QQ 投递。

**决策规则（cron 表格修复时）**：
| 用户语境 | 选择 |
|---|---|
| 用户提到表格/格式 | 保表格，不要因 ~50 token/次成本降级到 A |
| 用户说"token 不是问题/别抠搜" | 优先 D（直连 sendRichMessage）——一次到位，别再走 B 试错 |
| 用户明确要 B | 可以试，但必须 run 后看真实 Telegram 端；若仍 bullet 立即转 D |

**为什么推荐直接 D 而非 B**：B 方案多一轮试错（改模式 → run → 用户发现还是 bullet → 再改 D），而 D 方案是已知唯一保表格路径，成本为零 token。用户偏好是"别抠搜"，不是"必须用 LLM 模式"——D 同样满足。

**切换 cron 模式后必须真验证**：`cronjob action='run'` 手动触发一次，确认 last_status=ok **且用户端收到的是表格而非 bullet**。不要只看配置落盘、不要只看 cron output 文件（output 文件是脚本/LLM 原始输出，不代表投递结果）。
